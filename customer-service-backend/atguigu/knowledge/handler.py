from typing import Dict, Any

from atguigu.domain.messages import BotMessage


class KnowLedgeHandler:

    def __init__(self,konwledge_intents:Dict[str,Any]):
        self.knowledge_intents = konwledge_intents



    def handle(self) -> list[BotMessage]:
        return [BotMessage(text="我暂不知道任何信息")]
