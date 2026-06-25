from typing import List

from atguigu.domain.state import Turn, Session

from atguigu.domain.messages import *


class HistoryBuilder:
    """
    历史记录构建器
    把用户消息的usermessage对象给序列化为字符串
    把历史对话的QA 这两个类型的对象给序列化为字符串
    """

    @staticmethod
    def build(turns: List[Turn]) -> str:
        """
        构建历史记录
        :param turns:
        :return:
        """
        msg:list[str]=[]
        for turn in turns:
            # 1 用户消息

            user_message = turn.user_message

            user_message_str = HistoryBuilder._render_user_message(user_message)

            msg.append(f"USER:{user_message_str}")

            for bot_msg in turn.bot_messages:
                bot_msg_str = HistoryBuilder._render_bot_message(bot_msg)
                msg.append(f"BOT:{bot_msg_str}")

        return "\n".join(msg)


            # 2 机器人回复消息

    @staticmethod
    def _render_user_message(user_message: UserMessage):
        """
        渲染用户消息
        :param user_message:
        :return:
        """

        if user_message.type == MessageType.TEXT:
            return HistoryBuilder._render_text_msg(user_message.text)

        else:
            return HistoryBuilder._render_obj_msg(user_message.object)

    @staticmethod
    def _render_text_msg(text: str) -> str:
        return text.strip()

    @classmethod
    def _render_obj_msg(cls, object_msg: FocusedObject) -> str:

        label = "订单对象" if object_msg.type == "order" else "商品对象"
        id = object_msg.id
        title = object_msg.title
        attributes:Dict[str,Any] = object_msg.attributes

        attributes_str=" ".join([f"{k}={v}" for k,v in attributes.items()])

        return f"[lable= {label}, id= {id}. title= {title}, attributes= {attributes_str}]"

    @classmethod
    def _render_bot_message(cls, bot_msg:BotMessage)->str:

        if bot_msg.text:
            return HistoryBuilder._render_text_msg(bot_msg.text)
        else:
            return HistoryBuilder._render_obj_msg(bot_msg.object)

    @staticmethod
    def render_chat_history_user_message(user_message: UserMessage, session: Session):

        return ChatHistoryMessage(
            session_id=session.session_id,
            role="user",
            text=user_message.text,
            object=user_message.object
        )

    @staticmethod
    def render_chat_history_bot_message(bot_message: BotMessage, session: Session):

        return ChatHistoryMessage(
            session_id=session.session_id,
            role="bot",
            text=bot_message.text,
            object=bot_message.object
        )
