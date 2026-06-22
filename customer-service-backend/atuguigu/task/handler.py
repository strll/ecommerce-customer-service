from atuguigu.domain.messages import BotMessage
from atuguigu.task.flow.flow import FlowsList


class TaskHandler:

    def __init__(self,flows:FlowsList):
        self.flows=flows

    def handle(self) -> list[BotMessage]:
        return [BotMessage(text="任务已经处理")]

