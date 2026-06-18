from domain.messages import UserMessage, ProcessResult, BotMessage
from domain.state import DialogueState


class DialogueEngine:
    """占位实现：暂不做任何对话逻辑，仅回固定话术，用于打通 web 层链路。
    下一节将替换为真正的引擎。"""

    async def process_message(self, state: DialogueState, user_message: UserMessage) -> ProcessResult:
        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages=[BotMessage(text="（占位回复）我已经收到你的消息了。")],
        )