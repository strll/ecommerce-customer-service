"""
领域上下文模块

定义流程引擎的上下文数据结构:
- TaskContext: 业务流程上下文（当前流程、步骤、已收集的槽位数据）
- SystemContext: 系统流程上下文（启动/中断/恢复/取消/收集信息的系统事件）
- SystemTaskContext: 聚合上下文（TaskContext + SystemContext）
- FLOW_ID_TO_CONTEXT_CLASS: 系统流程ID到子类的注册表，用于多态反序列化
"""

from dataclasses import field, asdict
from typing import Dict, Any

from dataclasses import dataclass


@dataclass(slots=True)
class TaskContext:
    """业务流程上下文: 记录当前在哪个流程、哪一步、已收集到的槽位数据"""

    flow_id: str                        # 业务流程ID, 对应 user_flows.yml 中的定义, 如 "order_status_query"
    step_id: str | None = None          # 当前步骤ID, None 表示尚未进入具体步骤
    slots: Dict[str, Any] = field(default_factory=dict)  # 槽位数据, 如 {"order_number": "20240101001"}

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskContext":
        """从字典反序列化, flow_id 为必填"""
        return cls(
            flow_id=data["flow_id"],
            step_id=data.get("step_id"),
            slots=data.get("slots", {})
        )


# 前向声明: 供 SystemTaskContext 类型注解使用, 实际定义见下方同名类
@dataclass(slots=True)
class SystemContext:  # 系统上下文：模版【各个子类系统上下文的通用属性】
    """
    系统流程上下文
    """
    flow_id: str  # 系统流程的流程ID(system_task_started)
    step_id: str | None = None  # 系统流程的步骤ID(start)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemContext":
        clz = FLOW_ID_TO_CONTEXT_CLASS[data['flow_id']]
        return clz(**data)



@dataclass(slots=True)
class SystemTaskContext:
    """聚合上下文: 同时维护业务侧(TaskContext)和系统侧(SystemContext)的状态"""

    task_context: TaskContext        # 业务维度: 哪个流程、哪一步、收集了哪些数据
    system_context: "SystemContext"  # 系统维度: 启动/中断/恢复/取消/收集信息

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_context": self.task_context.to_dict(),
            "system_context": self.system_context.to_dict()
        }


@dataclass(slots=True)
class SystemContext:
    """系统流程上下文基类: 描述系统内部的状态流转事件"""

    flow_id: str                 # 系统流程ID: system_task_started / interrupted / resumed / canceled / collect_information
    step_id: str | None = None   # 系统流程步骤ID, 如 "start"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemContext":
        """工厂方法: 根据 flow_id 在注册表中查找对应子类并实例化"""
        clz = FLOW_ID_TO_CONTEXT_CLASS[data['flow_id']]
        return clz(**data)


@dataclass(slots=True)
class StartedSystemContext(SystemContext):
    """系统启动上下文: 系统启动了一个新的业务流程"""

    started_flow_id: str = ""    # 被启动的业务流程ID, 如 "order_status_query"
    started_flow_name: str = ""  # 被启动的业务流程名称, 如 "订单状态查询"


@dataclass(slots=True)
class InterruptedSystemContext(SystemContext):
    """系统中断上下文: 用户切换意图, 中断当前流程并启动新流程"""

    interrupted_flow_id: str = ""    # 被中断的旧业务流程ID
    interrupted_flow_name: str = ""  # 被中断的旧业务流程名称
    started_flow_id: str = ""        # 新启动的业务流程ID
    started_flow_name: str = ""      # 新启动的业务流程名称


@dataclass(slots=True)
class ResumedSystemContext(SystemContext):
    """系统恢复上下文: 恢复之前被中断的业务流程"""

    resumed_flow_id: str = ""    # 被恢复的业务流程ID
    resumed_flow_name: str = ""  # 被恢复的业务流程名称


@dataclass(slots=True)
class CanceledSystemContext(SystemContext):
    """系统取消上下文: 用户放弃或系统超时/异常导致取消当前流程"""

    canceled_flow_id: str = ""    # 被取消的业务流程ID
    canceled_flow_name: str = ""  # 被取消的业务流程名称


@dataclass(slots=True)
class CollectedSystemContext(SystemContext):
    """系统信息收集上下文: 系统正在向用户收集某个槽位信息(槽位填充)"""

    slot_name: str = ""                                     # 收集的槽位名, 如 "order_number", 可用于前端渲染和路由
    response: Dict[str, Any] = field(default_factory=dict)  # 系统提示内容, 如 {"text": "请告诉我您的订单号"}


# 系统流程ID -> 子类的注册表, 用于 SystemContext.from_dict() 多态反序列化
FLOW_ID_TO_CONTEXT_CLASS: Dict[str, Any] = {
    "system_task_started": StartedSystemContext,
    "system_task_resumed": ResumedSystemContext,
    "system_collect_information": CollectedSystemContext,
    "system_task_interrupted": InterruptedSystemContext,
    "system_task_canceled": CanceledSystemContext
}


# 快速自测: python contexts.py
if __name__ == '__main__':
    task_context = TaskContext(flow_id="1", step_id="1", slots={"name": "张三"})
    print(task_context.to_dict())
    # 预期: {'flow_id': '1', 'step_id': '1', 'slots': {'name': '张三'}}