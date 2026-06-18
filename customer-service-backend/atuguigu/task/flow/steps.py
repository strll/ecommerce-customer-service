from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

from atuguigu.task.flow.links import FlowSteplink, FlowStepStaticLink, FlowStepConditionalLink, FlowStepFallbackLink

class FlowStepType(str, Enum):
    START = "start"
    ACTION = "action"
    END = "end"
    COLLECT = "collect"


def build_links(link_data: str | list[Dict[str, Any]]) -> List[FlowSteplink]:
    if isinstance(link_data, str):
        return [FlowStepStaticLink(target=link_data)]
    else:
        links = []
        for link_dict in link_data:
            if "if" in link_dict:
                links.append(FlowStepConditionalLink(condition=link_dict['if'], target=link_dict['then']))
            else:
                links.append(FlowStepFallbackLink(target=link_dict['else']))
        return links

@dataclass
class FlowStep:
    id: str
    type: FlowStepType
    next: list[FlowSteplink] = field(default_factory=list)
    description: str = ""

    @staticmethod
    def base_load_fields(base_data: Dict[str, Any]) -> Dict[str, Any]:
        # 【关键修改】：这里必须用大括号 {} 返回字典，不能用 FlowStep()！
        return {
            "id": base_data["id"],
            "type": FlowStepType(base_data["type"]),
            "description": base_data.get("description", ""),
            "next": build_links(base_data.get("next", []))
        }

    @classmethod
    def from_dict(cls, step_data: Dict[str, Any]) -> "FlowStep":
        # 多态转发
        step_type = step_data['type']
        clz = TYPE_TO_FLOW_STEP[step_type]
        return clz.from_dict(step_data)




@dataclass(slots=True)
class ResponseDefinition:
    text: str  # 必填

    model: str = "static"

    prompt: str | None = None


@dataclass(slots=True)
class StartedFlowState(FlowStep):
    pass


@dataclass()
class ActionFlowStep(FlowStep):
    action: str = ""

    args: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, step_data: Dict[str, Any]) -> "ActionFlowStep":
        return cls(
            **FlowStep.base_load_fields(step_data),
            action=step_data['action'],
            args=step_data.get('args', {})
        )

@dataclass(slots=True)
class EndFlowStep(FlowStep):
    @classmethod
    def from_dict(cls, step_data: Dict[str, Any]) -> "EndFlowStep":
        return cls(**FlowStep.base_load_fields(step_data))



@dataclass(slots=True)
class SlotValidation:
    condition: str  # 条件(必填)
    failure_response: ResponseDefinition | None = None


@dataclass(slots=True)
class CollectedFlowStep(FlowStep):
    slot_name: str = ""
    response: ResponseDefinition = field(default_factory=ResponseDefinition)

    validate: SlotValidation | None = None
    @classmethod
    def from_dict(cls, step_data: Dict[str, Any]) -> "CollectedFlowStep":
        return cls(
            **FlowStep.base_load_fields(step_data),
            slot_name=step_data['slot_name'],
            response=ResponseDefinition(
                text=step_data['response']['text'],
                model=step_data['response'].get('model', 'static'),
                prompt=step_data['response'].get('prompt')
            ),
            validate=SlotValidation(
                condition=step_data['validate']['condition'],
                failure_response=ResponseDefinition(
                    text=step_data['validate']['failure_response']['text'],
                    model=step_data['validate']['failure_response'].get('model', 'static'),
                    prompt=step_data['validate']['failure_response'].get('prompt')
                ) if step_data['validate'].get('failure_response') else None
            ) if step_data.get('validate') else None
        )

@dataclass(slots=True)
class StartedFlowStep(FlowStep):

    @classmethod
    def from_dict(cls, step_data: Dict[str, Any]) -> "StartedFlowStep":
        return cls(**FlowStep.base_load_fields(step_data))

# 类的类型 实例类型
TYPE_TO_FLOW_STEP: Dict[str, type[FlowStep]] = {
    "start": StartedFlowStep,
    "action": ActionFlowStep,
    "end": EndFlowStep,
    "collect": CollectedFlowStep
}

if __name__ == '__main__':
    data = {
        "id": "111",
        "type": "start",
        "next": [],
        "description": "1111111"
    }
    print(FlowStep.from_dict(data))
