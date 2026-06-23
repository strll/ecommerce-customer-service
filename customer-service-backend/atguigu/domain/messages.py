from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict

from atguigu.infrastructure.http_client import main


class MessageType(Enum):
    TEXT = "text"
    OBJECT = "object"


@dataclass(slots=True)
class FocusedObject:
    id: str
    type: str
    title: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)  # 类型

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "attributes": dict(self.attributes)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FocusedObject":
        return cls(
            id=data["id"],
            type=data["type"],
            title=data.get("title", ""),
            attributes=data.get("attributes","")
        )


@dataclass(slots=True)
class UserMessage:
    sender_id: str  # 用户id
    message_id: str  # 消息id
    type: MessageType  # 消息类型 text或者object
    text: str  # 文本消息
    object: FocusedObject | None = None


    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "message_id": self.message_id,
            "type": self.type.value,
            "text": self.text,
            "object": self.object.to_dict() if self.object else None
        }
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserMessage":
        return cls(
            sender_id=data["sender_id"],
            message_id=data["message_id"],
            type=MessageType(data["type"]),
            text=data["text"],
            object=FocusedObject.from_dict(data["object"]) if data.get("object") else None
        )

@dataclass(slots=True)
class BotMessage:
    text:str|None=None
    object: FocusedObject | None = None
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "object": self.object.to_dict() if self.object else None
        }
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BotMessage":
        return cls(
            text=data["text"],
            object=FocusedObject.from_dict(data["object"]) if data.get("object") else None
        )

@dataclass
class ProcessResult:
    sender_id: str  #`这次回复给哪个用户
    message_id: str # 本轮消息的 id（和请求里的对应）
    messages: list[BotMessage] #机器人本轮要回复的消息列表（可能多条）



if __name__ == '__main__':
    object = FocusedObject(id="1")
