import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from openai.types.beta.realtime import session

from atuguigu.domain.contexts import TaskContext, SystemContext
from atuguigu.domain.messages import UserMessage, BotMessage


@dataclass(slots=True)
class FocusedObject:
    type: str  # 对象类型，例如 `order`、`product`
    id: str  # `对象唯一标识
    title: str | None = None  # 对象的显示标题
    attributes: dict = field(default_factory=dict)  # 对象的扩展属性，由前端决定带什么

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "id": self.id,
            "title": self.title,
            "attributes": self.attributes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FocusedObject":
        return cls(
            type=data["type"],
            id=data["id"],
            title=data["title"],
            attributes=data["attributes"],
        )


@dataclass(slots=True)
class Turn:
    turn_id: str
    user_message: UserMessage
    bot_messages: list[BotMessage]

    @classmethod
    def from_dict(cls, param):
        return Turn(
            turn_id=param["turn_id"],
            user_message=UserMessage.from_dict(param["user_message"]),
            bot_messages=[BotMessage.from_dict(message) for message in param["bot_messages"]],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "user_message": self.user_message.to_dict(),
            "bot_messages": [message.to_dict() for message in self.bot_messages],
        }


@dataclass(slots=True)
class Session:
    session_id: str  # 会话唯一标识，使用 UUID
    started_at: float  # `会话开始的时间戳
    last_activity_at: float  # `最后一次活动的时间戳，用来判断超时
    closed_at: float | None = None  # 会话关闭时间，未关闭时为 `None`
    turns: list[Turn] = field(default_factory=list)  # `这个会话里的所有轮次

    def to_dict(self) -> dict[str, Any]:
        return {
            "turns": [turn.to_dict() for turn in self.turns],
            "session_id": self.session_id,
            "started_at": self.started_at,
            "last_activity_at": self.last_activity_at,
            "closed_at": self.closed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        return cls(
            turns=[Turn.from_dict(turn) for turn in data["turns"]],
            session_id=data["session_id"],
            started_at=data["started_at"],
            last_activity_at=data["last_activity_at"],
            closed_at=data["closed_at"],
        )


@dataclass(slots=True)
class DialogueState:
    sender_id: str  # 用户唯一标识
    active_task: TaskContext | None = None  # 当前活跃的业务任务
    paused_tasks: list[TaskContext] = field(default_factory=list)  # `被挂起的任务列表
    active_system_task: SystemContext | None = None  # 当前活跃的系统任务
    focused_object: FocusedObject | None = None  # `用户当前聚焦的订单 / 商品
    sessions: list[Session] = field(default_factory=list)  # `历史会话列表
    current_session_id: str | None = None  # `当前活跃会话 ID
    pending_turn: Turn | None = None  # `正在处理中的轮次

    def to_dict(self) -> dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "active_task": self.active_task.to_dict() if self.active_task else None,
            "paused_tasks": [task.to_dict() for task in self.paused_tasks],
            "active_system_task": self.active_system_task.to_dict() if self.active_system_task else None,
            "focused_object": self.focused_object.to_dict() if self.focused_object else None,
            "sessions": [session.to_dict() for session in self.sessions],
            "current_session_id": self.current_session_id,
            "pending_turn": self.pending_turn.to_dict() if self.pending_turn else None
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DialogueState":
        return cls(
            sender_id=data["sender_id"],
            active_task=TaskContext.from_dict(data["active_task"]) if data.get("active_task") else None,
            paused_tasks=[TaskContext.from_dict(task) for task in data["paused_tasks"]],
            active_system_task=SystemContext.from_dict(data["active_system_task"]) if data.get(
                "active_system_task") else None,
            focused_object=FocusedObject.from_dict(data["focused_object"]) if data.get("focused_object") else None,
            sessions=[Session.from_dict(session) for session in data["sessions"]],
            current_session_id=data.get("current_session_id"),
            pending_turn=Turn.from_dict(data["pending_turn"]) if data.get("pending_turn") else None

        )

    def start_active_system_task(self, active_system_task: SystemContext) -> None:
        """激活一个系统任务"""
        self.active_system_task = active_system_task

    def end_active_system_task(self) -> None:
        """结束一个系统任务"""
        self.active_system_task = None

    def start_active_task(self, active_task: TaskContext) -> None:
        """开始一个业务任务"""
        self.active_task = active_task

    def end_active_task(self) -> None:
        """
        结束一个业务任务
        """
        self.active_task = None

    def interrupted_active_task(self, task: TaskContext) -> None:
        """暂停一个任务"""
        self.paused_tasks.append(task)

        self.active_task = None

    def resumed_active_task(self, flow_id: str) -> None:
        """恢复一个任务"""

        if not flow_id:
            pop = self.paused_tasks.pop()
            self.active_task = pop

        for task in self.paused_tasks:

            if task.flow_id == flow_id:
                self.active_task = task
                self.paused_tasks.remove(task)
                return

        task = self.paused_tasks.pop()
        self.active_task = task

    def cancel_active_task(self):
        """取消一个任务"""
        self.active_task = None
        self.active_system_task = None

    # 设置任务槽
    def set_slots(self, slots: dict[str, Any]):

        self.active_task.slots.update(slots)

    def rempve_slots(self, slot_name: str):
        """
        移除任务槽
        """
        self.active_task.slots.pop(slot_name)

    def current_active_task(self) -> TaskContext | None:
        """
        获取当前活跃的业务任务
        """
        return self.active_system_task or self.active_task

    def current_session(self) -> Session | None:
        """
        获取当前活跃会话
        """

        for session in self.sessions:
            if session.session_id == self.current_session_id:
                return session

        return None

    # session相关的
    def start_session(self):

        if self.current_session() is None:
            session = Session(session_id=str(uuid.uuid4()),
                              started_at=time.time(),
                              last_activity_at=time.time(),
                              )

            self.current_session_id = session.session_id
            self.sessions.append(session)

    def close_session(self):
        """
        关闭当前活跃会话
        """
        session = self.current_session()
        if session:
            session.closed_at = time.time()
            self.current_session_id = None

    def reset_running_state_for_new_session(self):
        """
        重置当前会话的运行状态
        """
        self.active_task = None
        self.active_system_task = None
        self.paused_tasks = []
        self.focused_object = None
        self.pending_turn = None
        self.current_session_id = None

    # turn
    def begin_turn(self, message: UserMessage):
        if self.current_session():
            turn = Turn(turn_id=str(uuid.uuid4()),
                        user_message=message,
                        bot_messages=[]
                        )

            self.pending_turn= turn


    def comment_turn(self):

        if self.current_session():
            self.current_session().turns.append(self.pending_turn)
            self.pending_turn = None


    def set_focused_object(self, focused_object: FocusedObject):
        self.focused_object = focused_object

