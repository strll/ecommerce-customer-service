import datetime
import time

from atuguigu.domain.messages import ProcessResult, UserMessage, BotMessage, MessageType
from atuguigu.domain.state import DialogueState
from atuguigu.plan.turn_plann import TurnPlanner


class DialogueEngine:

    def __init__(self,turn_planner: TurnPlanner):
        self.turn_planner=turn_planner


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

            self._handle_text_msg(state,self.turn_planner)

            pass
        else:

            self._handle_obj_msg()

            pass



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

    def _handle_text_msg(self, state:DialogueState, turn_planner:TurnPlanner):

        '''

        :param state:
        :param turn_planner:
        :return:
        '''

        turn_planner.predict()


        pass




    def _handle_obj_msg(self):
        pass






