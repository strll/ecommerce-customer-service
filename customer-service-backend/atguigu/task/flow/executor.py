
from typing import List
from dataclasses import asdict
from atguigu.task.action.base import ActionResult
from atguigu.task.action.buitin.registry import ActionRegistry
from atguigu.task.action.buitin.runner import ActionRunner, ActionCall
from atguigu.task.flow.flow import FlowsList

from atguigu.domain.state import DialogueState
from atguigu.domain.messages import BotMessage
from atguigu.task.flow.steps import FlowStep, StartedFlowStep, CollectedFlowStep, ActionFlowStep, EndFlowStep
from atguigu.task.flow.links import FlowStepStaticLink, FlowStepConditionalLink, FlowStepFallbackLink
from atguigu.domain.contexts import CollectedSystemContext

class FlowExecutor:
    """
    流程推进器，负责驱动对话流程的执行与推进。

    核心职责：
    - 按照流程定义（FlowsList）逐步推进当前对话任务
    - 根据不同步骤类型（开始、收集槽位、动作、结束）执行对应逻辑
    - 在步骤间通过链接（静态/条件/兜底）选择下一步
    - 最终产出动作调用（ActionCall）或机器人消息列表
    """

    async def run_task(self, state: DialogueState,
                       flows: FlowsList,
                       action_runner: ActionRunner
                       ) -> List[BotMessage]:

        """
        执行当前任务流程，持续推流动作直到遇到 action_listen（等待用户输入）为止。

        :param state: 当前对话状态，包含任务上下文和槽位信息
        :param flows: 流程定义列表，提供流程结构查询
        :param action_runner: 动作执行器，负责实际执行 ActionCall 并返回结果
        :return: 本轮流程推进过程中产生的所有机器人消息列表
        """
        messages: List[BotMessage] = []
        while True:
            # 持续推流流程步骤，直到产出一个需要执行的动作调用
            action_call: ActionCall = self._advance_util_action(state, flows)

            # action_listen 表示当前轮次需要等待用户输入，结束推流
            if action_call.action_name == "action_listen":
                break
            else:
                # 执行动作并将结果（槽位更新和消息）合并到当前状态
                action_result: ActionResult = action_runner.run(action_call, state)
                state.set_slots(action_result.slot_updates)
                messages.extend(action_result.messages)

        return messages

    def _advance_util_action(self, state: DialogueState,
                             flows: FlowsList) -> ActionCall:
        """
        持续推进流程步骤，直到产出一个有效的 ActionCall。

        内部循环依次取出当前活跃任务的步骤并执行，
        某些步骤（如开始步骤、槽位收集启动）不产生动作调用，
        会继续推进到下一步，直到遇到需要执行的动作为止。

        :param state: 当前对话状态
        :param flows: 流程定义列表
        :return: 下一个需要执行的 ActionCall
        """

        while True:
            # 获取当前活跃任务的流程ID和步骤ID
            current_active_task = state.current_active_task()
            flow_id = current_active_task.flow_id

            # 根据流程ID查找对应的流程定义
            flow = flows.get_flow_by_id(flow_id)

            # 根据步骤ID获取当前步骤对象
            step = flow.get_step_by_id(current_active_task.step_id)

            # 执行当前步骤，可能返回 ActionCall 或 None（继续推进）
            action_call: ActionCall | None = self._run_step(state, step, flows)

            if action_call is not None:
                return action_call

    def _run_step(self, state: DialogueState, step:FlowStep, flows:FlowsList)->ActionCall|None:
        """
        根据步骤类型分派到对应的处理逻辑。

        支持的步骤类型：
        - StartedFlowStep: 流程起始步骤
        - CollectedFlowStep: 槽位收集步骤
        - EndFlowStep: 流程结束步骤
        - ActionFlowStep: 动作执行步骤

        :param state: 当前对话状态
        :param step: 当前需要执行的流程步骤
        :param flows: 流程定义列表
        :return: ActionCall（需要执行动作时）或 None（仅推进流程时）
        """
        if isinstance(step, StartedFlowStep):
            return self._run_start_step(step, state)
        if isinstance(step, CollectedFlowStep):
            return self._run_collect_slots_step(step, state, flows)
        if isinstance(step, EndFlowStep):
            return self._run_end_step(state)
        if isinstance(step, ActionFlowStep):
            return self._run_action_step(step, state)



    def _run_start_step(self, step: StartedFlowStep,
                        state: DialogueState) -> None:
        """
        处理流程起始步骤：直接推进到下一步，不产生动作调用。

        :param step: 起始步骤
        :param state: 当前对话状态
        :return: 始终返回 None，表示无需执行动作
        """

        # 1. 推进下一步
        self._advance_next_step(state, step)
        # 2. 返回None
        return None

    def _advance_next_step(self, state, step):
        """
        将当前任务的步骤推进到下一个步骤。

        通过链接选择策略确定下一步的 step_id，
        并更新到当前活跃任务的上下文中。

        :param state: 当前对话状态
        :param step: 当前步骤，用于查找出边链接
        """
        # 1. 寻找下一个step边
        next_step_id = self._select_next_step(step, state)
        # 2. 更新当前任务上下文的step_id(给当前执行任务流程的上下文用)不做这个动作，出不来
        state.current_active_task().step_id = next_step_id

    def _select_next_step(self,
                          step: FlowStep,
                          state: DialogueState
                          ) -> str:
        """
        根据步骤的出边链接选择下一个步骤ID。

        链接匹配优先级：
        1. FlowStepStaticLink: 静态链接，直接跳转
        2. FlowStepConditionalLink: 条件链接，条件满足时跳转
        3. FlowStepFallbackLink: 兜底链接，作为默认跳转

        :param step: 当前步骤，包含出边链接列表
        :param state: 当前对话状态，用于条件链接的表达式求值
        :return: 下一个步骤的ID
        """

        for link in step.next:
            if isinstance(link, FlowStepStaticLink):
                return link.target  # 静态链接：直接返回目标步骤ID
            if isinstance(link, FlowStepConditionalLink):
                # 条件链接：评估条件表达式，满足则跳转
                if self._eval_condition(state, link.condition):
                    return link.target
            if isinstance(link, FlowStepFallbackLink):
                return link.target  # 兜底链接：作为默认跳转目标
        return "step not exist next"

    def _eval_condition(self,
                        state: DialogueState,
                        condition: str
                        ) -> bool:
        """
        评估条件表达式的布尔值。

        将当前任务的槽位和上下文作为变量注入，
        使用 eval 对条件字符串进行求值。

        :param state: 当前对话状态
        :param condition: 条件表达式字符串，如 "slots['order_number'] is not None"
        :return: 条件评估结果
        """
        # 构建 eval 的变量命名空间，包含槽位和任务上下文
        data = {
            "slots": state.active_task.slots,
            "context": asdict(state.current_active_task())
        }
        return bool(eval(condition, {}, data))

    def _run_end_step(self, state: DialogueState) -> None:
        """
        处理流程结束步骤：清除对话状态中的任务流程上下文。

        优先结束系统级任务（如槽位收集），
        若无系统级任务则结束业务级任务。

        :param state: 当前对话状态
        :return: 始终返回 None
        """
        if state.active_system_task:
            # 优先结束系统级任务上下文
            state.end_active_system_task()
        else:
            # 结束业务级任务上下文
            state.end_active_task()
        return None

    def _run_action_step(self,
                         step: ActionFlowStep,
                         state: DialogueState) -> ActionCall:
        """
        处理动作执行步骤：先推进到下一步，再构建并返回动作调用。

        :param step: 动作步骤，包含动作名称和参数
        :param state: 当前对话状态
        :return: 构建好的 ActionCall 对象
        """

        # 先推进流程到下一步，避免动作执行后流程停滞
        self._advance_next_step(state, step)

        return self._build_action_call(state, step)

    def _build_action_call(self, state, step) -> ActionCall:
        """
        根据步骤定义构建 ActionCall 对象。

        从步骤中提取动作名称和参数，若参数为字符串引用（如 "context.response"），
        则从系统任务上下文中解析获取实际值。

        :param state: 当前对话状态
        :param step: 动作步骤定义
        :return: 包含动作名称和参数的 ActionCall
        """
        # 1. 获取action_name (action_listen/action_response/action_xxx)
        # 2. 获取action_kwargs (构建参数)
        action_name = step.action
        action_kwargs = step.args
        # action_kwargs有可能有:结构有可能是一个str、dict{}  有可能没有:结构是个空字典{}
        if isinstance(action_kwargs, str):
            # 字符串引用形式（如 "context.response"），从系统任务上下文中提取对应字段值
            action_kwargs = asdict(state.active_system_task)[action_kwargs.split(".")[1]]
        return ActionCall(action_name=action_name, action_kwargs=action_kwargs)

    def _run_collect_slots_step(self,
                                step: CollectedFlowStep,
                                state: DialogueState,
                                flows: FlowsList):
        """
        处理槽位收集步骤：尝试填充槽位、校验槽位值、或启动收集子流程。

        处理逻辑：
        1. 先尝试通过 focused_object 自动填充槽位
        2. 若槽位已有值，进行校验：
           - 校验通过：推进到下一步
           - 校验失败：清除槽位，返回失败提示
        3. 若槽位无值：启动系统级信息收集子流程

        :param step: 槽位收集步骤，包含槽位名称、校验规则和提示信息
        :param state: 当前对话状态
        :param flows: 流程定义列表，用于获取系统收集流程
        :return: ActionCall（校验失败时返回提示）或 None（推进/启动收集时）
        """

        # 尝试通过 focused_object（如用户提及的订单/商品）自动填充槽位
        self._try_to_fill_collect_slot_focused_object(state, step)
        # 1. 判断槽位是否已经填过
        if state.active_task.slots.get(step.slot_name):
            if step.validate:
                # 有校验规则时，评估槽位值是否合法
                if self._eval_condition(state, step.validate.condition):
                    # 校验通过，推进到下一步
                    self._advance_next_step(state, step)
                    return None
                else:
                    # 校验失败，清除无效槽位值
                    state.remove_slot(step.slot_name)
                    if step.validate.failure_response:
                        # 返回自定义的校验失败提示
                        return ActionCall(action_name="action_response",
                                          action_kwargs=asdict(step.validate.failure_response))
                    else:
                        # 返回默认的校验失败提示
                        return ActionCall(action_name="action_response",
                                          action_kwargs={"text": "您填写的信息有误，请你重新在填"})
            else:
                # 无校验规则，直接推进到下一步
                self._advance_next_step(state, step)
                return None
        else:
            # 槽位未填充，启动系统级信息收集子流程
            state.start_active_system_task(CollectedSystemContext(
                flow_id="system_collect_information",
                step_id=flows.get_flow_by_id('system_collect_information').start_step().id,
                slot_name=step.slot_name,
                response=asdict(step.response)
            ))
            return None

    def _try_to_fill_collect_slot_focused_object(self, state: DialogueState,
                                                 step: CollectedFlowStep):
        """
        尝试通过对话上下文中的 focused_object 自动填充槽位。

        当用户在对话中提及了特定对象（如订单、商品）时，
        直接将该对象的 ID 填入对应槽位，减少交互轮次。

        :param state: 当前对话状态，包含 focused_object
        :param step: 槽位收集步骤，包含目标槽位名称
        :return: 始终返回 None
        """

        if state.focused_object is None:
            return None

        # 根据槽位名称和对象类型匹配，自动填充对象ID
        if step.slot_name == 'order_number' and state.focused_object.type == "order":
            state.set_slots({step.slot_name: state.focused_object.id})
        if step.slot_name == "product_id" and state.focused_object.type == "product":
            state.set_slots({step.slot_name: state.focused_object.id})


if __name__ == '__main__':
    condition = "context.get('reason') == 'clarification_rejected'"
    data = {
        "context": {"reason": "abc"}
    }

    print(bool(eval(condition, {}, data)))
