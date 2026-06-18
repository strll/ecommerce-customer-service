
from atuguigu.domain.state import DialogueState

from atuguigu.infrastructure.llm import llm

class TurnPlanner:
    """
    意图分析器
    根据任务自然语言调用LLM 分析轨道类型
    """

    def predict(self,state:DialogueState):
        """

        :param state:
        :return:
        """
        inputs_prompt=self._bulid_inputs_prompt()

        chain=inputs_prompt|llm




