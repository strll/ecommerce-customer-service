from dataclasses import dataclass


@dataclass(slots= True)
class FlowSteplink:

    target:str

@dataclass(slots= True)
class FlowStepStaticLink(FlowSteplink):
    """
    next是字符串的

    """
    pass
@dataclass(slots= True)
class FlowStepConditionalLink(FlowSteplink):
    """
    next是列表的[{if: xxx,then:xx} ]
    """
    condition:str #接受if里面的xxx

@dataclass(slots= True)
class FlowStepFallbackLink(FlowSteplink):
    """
    next是列表的[{if: xxx,then:xx} ]
    """
    pass




