import datetime
import time

from atuguigu.chitchat.handler import ChitChatHandler
from atuguigu.domain.messages import ProcessResult, UserMessage, BotMessage, MessageType
from atuguigu.domain.state import DialogueState
from atuguigu.knowledge.handler import KnowLedgeHandler
from atuguigu.plan.planner import TurnPlanner
from atuguigu.plan.turn_validator import TurnPlanValidator
from atuguigu.task.flow.flow import FlowsList
from atuguigu.task.handler import TaskHandler


class DialogueEngine:

    def __init__(self,turn_planner: TurnPlanner,
                 turn_validator: TurnPlanValidator,
                 task_handler: TaskHandler,
                 konwLedge_handler: KnowLedgeHandler,
                 chit_chat_handler:ChitChatHandler,

                 ):
        self.turn_validator=turn_validator
        self.turn_planner=turn_planner
        self.task_handler=task_handler              # 处理轨道是业务任务的
        self.konwledge_handler=konwLedge_handler    #处理轨道是信息咨询的
        self.chit_chat_handler=chit_chat_handler    # 处理轨道是闲聊的



    async def handle_dialogue(self,state: DialogueState,
                              user_message: UserMessage)->ProcessResult:

        #开启session
        self._prepare_session(state)
        #开启turn
        self._begin_turn(state,user_message)

        if user_message.type in MessageType.TEXT:
            #1 准备llm提示词
            #2 调用llm
            #3 校验
            #4 分流处理三个轨道

            msgs=self._handle_text_msg(state,self.turn_planner,self.task_handler.flows)


        else:

            self._handle_obj_msg()

        state.current_session().turns.extend()

        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages=[
                BotMessage(text="我是智能小客服"),
                BotMessage(text="欢迎你来到这里...")
            ]
        )



    async def process_message(self, state: DialogueState, user_message: UserMessage) -> ProcessResult:
        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages=[BotMessage(text="（占位回复）我已经收到你的消息了。")],
        )

    def _prepare_session(self, state:DialogueState):

        current_session=state.current_session()

        if current_session is None:
            state.start_session()
            return

        now = time.time()

        if now - current_session.started_at > self.session_timeout:
            state.close_session()
            state.reset_running_state_for_new_session()
            state.start_session()
        else:
            current_session.last_activity_at=now

        return

    def _begin_turn(self, state:DialogueState,userMessage:UserMessage):
        state.begin_turn(userMessage)

    def _handle_text_msg(self, state:DialogueState,
                         turn_planner:TurnPlanner,
                         flows:FlowsList
                         )->list[BotMessage]:

        '''

        :param state:
        :param turn_planner:
        :return:
        '''

        turn_plan=turn_planner.predict(state,flows)

        self.turn_validator.validate()

        if turn_plan.task is not None:
            self.task_handler.handle()
        elif turn_plan.knowledge is not None:
            self.konwledge_handler.handle()

        else:
            self.chit_chat_handler.handle()






    def _handle_obj_msg(self):
        pass






