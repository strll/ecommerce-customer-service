from typing import List

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.buitin.runner import ActionRunner
from atguigu.task.command.models import Command
from atguigu.task.command.processor import CommandProcessor
from atguigu.task.flow.flow import FlowsList


class TaskHandler:

    def __init__(self,flows:FlowsList,
                 processor:CommandProcessor,
                 action_runner:ActionRunner
                 ):
        self.flows=flows
        self.processor=processor
        self.action_runner=action_runner

    def handle(self,state:DialogueState,*,commands:List[Command]) -> list[BotMessage]:

        self.processor.run(state,commands,self.flows)


        return [BotMessage(text="任务已经处理")]

