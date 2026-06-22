import datetime
import time
from typing import Any

from atuguigu.chitchat.handler import ChitChatHandler
from atuguigu.clarify.responder import ClarifyResponder
from atuguigu.domain.messages import ProcessResult, UserMessage, BotMessage, MessageType
from atuguigu.domain.state import DialogueState
from atuguigu.knowledge.handler import KnowLedgeHandler
from atuguigu.knowledge.intents import KnowledgeIntent
from atuguigu.plan.planner import TurnPlanner
from atuguigu.plan.turn_plan import ClarifyReason
from atuguigu.plan.turn_validator import TurnPlanValidator
from atuguigu.task.command.models import SetSlotsCommand, Command
from atuguigu.task.flow.flow import FlowsList
from atuguigu.task.flow.steps import CollectedFlowStep
from atuguigu.task.handler import TaskHandler


class DialogueEngine:
    """
    对话引擎：整个客服对话系统的核心调度器。
    负责接收用户消息，经过 LLM 规划、校验、分流处理后，返回机器人回复。
    支持三种对话轨道：业务任务（task）、信息咨询（knowledge）、闲聊（chitchat）。
    """

    def __init__(self,
                 turn_planner: TurnPlanner,
                 turn_validator: TurnPlanValidator,
                 clarify_responder: ClarifyResponder,
                 task_handler: TaskHandler,
                 knowLedge_handler: KnowLedgeHandler,
                 chit_chat_handler: ChitChatHandler,

                 ):
        """
        初始化对话引擎，注入所有必需的协作组件。

        :param turn_planner: 轮次规划器，调用 LLM 预测用户意图并生成 TurnPlan
        :param turn_validator: 轮次规划校验器，校验 TurnPlan 是否合法
        :param clarify_responder: 澄清回复器，当规划不合法时生成引导用户澄清的回复
        :param task_handler: 业务任务处理器，处理业务轨道的流程执行
        :param knowLedge_handler: 信息咨询处理器，处理知识咨询轨道的回复
        :param chit_chat_handler: 闲聊处理器，处理闲聊轨道的回复
        """
        self.turn_validator = turn_validator
        self.turn_planner = turn_planner
        self.task_handler = task_handler  # 处理轨道是业务任务的
        self.knowLedge_handler = knowLedge_handler  # 处理轨道是信息咨询的
        self.chit_chat_handler = chit_chat_handler  # 处理轨道是闲聊的
        self.clarify_responder = clarify_responder

    async def hand_dialogue(self, state: DialogueState,
                            user_message: UserMessage) -> ProcessResult:
        """
        处理一轮完整的对话交互，是对外的主入口方法。
        流程：开启会话 -> 开启轮次 -> 根据消息类型分发处理 -> 提交轮次 -> 返回结果。

        :param state: 当前用户的对话状态，包含会话、任务、聚焦对象等上下文
        :param user_message: 用户发送的消息（文本消息或对象消息）
        :return: ProcessResult 包含回复消息列表的处理结果
        """

        # 1. 准备会话：若无活跃会话或会话已超时，则创建新会话
        self._prepare_session(state)
        # 2. 开启新的对话轮次，将用户消息记录到 pending_turn
        self._begin_turn(state, user_message)

        if user_message.type == MessageType.TEXT:
            # 文本消息处理流程：LLM 规划 -> 校验 -> 分流到三个轨道
            msgs = await self._handle_text_msg(state, self.turn_planner,
                                               self.task_handler.flows,
                                               self.knowLedge_handler.knowledge_intents

                                               )


        else:
            # 对象消息（如用户点击了订单/商品卡片）：先设置聚焦对象，再走对象处理流程
            state.set_focused_object(user_message.object)

            msgs = await self._handle_obj_msg(user_message, state, self.task_handler.flows)

        # 4. 将本轮机器人回复追加到 pending_turn 的 bot_messages 中
        state.pending_turn.bot_messages.extend(msgs)

        # 5. 提交轮次：将 pending_turn 归档到当前会话的 turns 列表
        state.commit_turn()

        # 6. 构造并返回处理结果
        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages=msgs
        )

    async def process_message(self, state: DialogueState, user_message: UserMessage) -> ProcessResult:
        """
        消息处理的占位方法，目前返回固定回复，用于开发阶段的快速验证。

        :param state: 当前对话状态
        :param user_message: 用户消息
        :return: 包含占位回复文本的 ProcessResult
        """
        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages=[BotMessage(text="（占位回复）我已经收到你的消息了。")],
        )

    def _prepare_session(self, state: DialogueState):
        """
        准备会话环境。判断是否需要创建新会话：
        - 若当前无活跃会话，直接创建新会话；
        - 若会话已超时（距开始时间超过阈值），则关闭旧会话、重置运行状态后创建新会话；
        - 否则仅更新最后活动时间。
        """

        current_session = state.current_session()

        # 无活跃会话，直接创建
        if current_session is None:
            state.start_session()
            return

        now = time.time()

        # 会话已超时，关闭旧会话并重置状态后创建新会话
        if now - current_session.started_at > self.session_timeout:
            state.close_session()
            state.reset_running_state_for_new_session()
            state.start_session()
        else:
            # 会话未超时，仅刷新最后活动时间
            current_session.last_activity_at = now

        return

    def _begin_turn(self, state: DialogueState, userMessage: UserMessage):
        """
        开启新的对话轮次，将用户消息绑定到 pending_turn。

        :param state: 当前对话状态
        :param userMessage: 本轮用户发送的消息
        """
        state.begin_turn(userMessage)

    async def _handle_text_msg(self, state: DialogueState,
                               turn_planner: TurnPlanner,
                               flows: FlowsList,
                               knowledge_intents: dict[str, KnowledgeIntent]
                               ) -> list[BotMessage]:
        """
        处理文本类型的用户消息。核心流程为：
        1. 调用 LLM 进行意图规划，生成 TurnPlan（包含 task/knowledge/chitchat 三个轨道的规划）
        2. 校验 TurnPlan 是否合法（如轨道冲突、缺少必要信息等）
        3. 校验不通过时，走澄清回复流程
        4. 校验通过时，按优先级分流到对应的轨道处理器

        :param state: 当前对话状态
        :param turn_planner: 轮次规划器，用于调用 LLM 生成规划结果
        :param flows: 可用的业务流程清单
        :param knowledge_intents: 可用的知识咨询意图映射
        :return: 机器人回复消息列表
        """

        # 1. 调用 LLM 规划器，预测用户意图，生成轮次规划（TurnPlan）
        turn_plan = await turn_planner.predict(state, flows=flows, knowledge_intents=knowledge_intents)

        # 2. 校验规划结果的合法性（轨道数量、命令类型、流程是否存在等）
        validated = self.turn_validator.validate(state, turn_plan, flow_list=flows, intents=knowledge_intents)

        # 3. 校验不通过：根据原因生成澄清回复，引导用户补充信息
        if not validated.valid:
            return self.clarify_responder.respond(state, validated.reason)

        # 4. 校验通过：按优先级分流到对应轨道的处理器（task > knowledge > chitchat）
        if turn_plan.task is not None:
            self.task_handler.handle()
        elif turn_plan.knowledge is not None:
            self.knowLedge_handler.handle()

        else:
            self.chit_chat_handler.handle()

    async def _handle_obj_msg(self, user_message: UserMessage,
                              state: DialogueState,
                              flows: FlowsList) -> list[BotMessage]:
        """
        处理对象类型的用户消息（如用户在前端点击了订单卡片、商品卡片）。
        核心流程为：
        1. 尝试将对象解析为槽位填充命令（SetSlotsCommand）
        2. 若能解析为命令且当前有活跃业务流程，直接推进业务流程
        3. 若不能解析为命令但有活跃业务流程，也尝试推进
        4. 若都没有匹配的业务流程，走澄清回复引导用户说明意图

        :param user_message: 用户发送的对象消息
        :param state: 当前对话状态
        :param flows: 可用的业务流程清单
        :return: 机器人回复消息列表
        """

        # 1. 将对象消息解析为槽位填充命令（如 order_number、product_id）
        command = self._resolve_object_command(user_message, state, flows)
        # 2. 如果解析出了命令，说明当前流程正好需要这个槽位，直接推进业务流程
        if command:
            return self.task_handler.handle()

        # 3. 没有解析出命令，但存在活跃的业务流程，也尝试推进
        if state.active_task is not None:
            return self.task_handler.handle()

        # 4. 既没有命令也没有活跃流程，走澄清回复，引导用户说明想对对象做什么
        return await self.clarify_responder.respond(state, reason=ClarifyReason.OBJECT_REQUIRES_INTENT)

    def _resolve_object_command(self, user_message: UserMessage,
                                state: DialogueState,
                                flows: FlowsList) -> list[Command]:
        """
        将前端传入的对象消息解析为槽位填充命令。
        根据对象类型（order/product）判断当前活跃流程是否正好需要该槽位，
        若需要则生成 SetSlotsCommand 用于填充槽位。

        :param user_message: 用户发送的对象消息
        :param state: 当前对话状态
        :param flows: 可用的业务流程清单
        :return: 解析出的命令列表，若无法匹配则返回空列表
        """

        # 1. 获取用户发送的对象信息
        user_obj = user_message.object
        if user_obj is None:
            return []
        # 2. 获取对象的类型（如 order、product）
        object_type = user_obj.type

        # 3. 根据对象类型判断：若当前活跃流程中存在未填充的对应槽位，则生成填充命令
        if object_type == "order":
            # 订单对象 -> 尝试填充 order_number 槽位
            if self._flow_has_unfilled_collect_slot(state, flows, "order_number"):
                return [SetSlotsCommand(command="set_slots", slots={"order_number": user_obj.id})]

            return []

        if object_type == "product":
            # 商品对象 -> 尝试填充 product_id 槽位
            if self._flow_has_unfilled_collect_slot(state, flows, "product_id"):
                return [SetSlotsCommand(command="set_slots", slots={"product_id": user_obj.id})]
            return []

        return []

    def _flow_has_unfilled_collect_slot(self, state: DialogueState,
                                        flows: FlowsList, slot_name: str) -> bool:
        """
        判断当前活跃业务流程中是否存在指定名称的未填充采集槽位。
        用于决定前端传入的对象消息能否直接作为槽位值使用。

        :param state: 当前对话状态
        :param flows: 可用的业务流程清单
        :param slot_name: 需要检查的槽位名称（如 "order_number"、"product_id"）
        :return: True 表示存在未填充的采集槽位，可以填充；False 表示不存在
        """

        # 1. 获取当前活跃的业务任务
        active_task = state.active_task

        # 2. 若不存在活跃任务，则无槽位可填
        if active_task is None:
            return False

        # 3. 从活跃任务中获取关联的业务流程定义
        flow_id = active_task.flow_id
        flow = flows.get_flow_by_id(flow_id)
        if flow is None:
            return False

        # 4. 若槽位已经在任务上下文中被填充过，则不再需要
        if active_task.slots.get(slot_name):
            return False

        # 5. 遍历流程步骤，检查是否存在匹配名称的采集步骤（CollectedFlowStep）
        for step in flow.steps:
            if isinstance(step, CollectedFlowStep) and step.slot_name == slot_name:
                return True

        return False
