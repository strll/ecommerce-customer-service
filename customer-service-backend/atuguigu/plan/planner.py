import json
from dataclasses import asdict
from typing import Any, Dict

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from atuguigu.domain.state import DialogueState
from atuguigu.infrastructure.llm import llm
from atuguigu.knowledge.intents import KnowledgeIntent
from atuguigu.plan.turn_plan import TurnPlan
from atuguigu.prompts.history_builder import HistoryBuilder
from atuguigu.prompts.loader import load_prompt
from atuguigu.task.flow.flow import FlowsList


class TurnPlanner:

    async def predict(self, state: DialogueState, *,
                      flows: FlowsList,
                      knowledge_intents: dict[str, KnowledgeIntent]) -> TurnPlan:
        # 1. 构建提示词
        inputs_prompt = self._build_inputs_prompt(state, flows, knowledge_intents)

        # 2. 调用LLM模型
        turn_plan = await  self._predict_from_inputs_prompt(inputs_prompt)

        return turn_plan

    def _build_inputs_prompt(self, state: DialogueState,
                             flows_list: FlowsList,
                             knowledge_intents: dict[str, KnowledgeIntent]):
        # prompt_template = load_prompt("turn_plan")

        user_msg = HistoryBuilder._render_user_message(state.pending_turn.user_message)

        current_conversation = HistoryBuilder.build(state.current_session().turns[-10:])

        # 3. 当前激活任务(业务任务)
        active_task_json = json.dumps(state.active_task.to_dict(),
                                      ensure_ascii=False) if state.active_task is not None else None

        # 4. 中断任务
        interrupted_tasks_json = json.dumps([paused_task.to_dict() for paused_task in state.paused_tasks],
                                            ensure_ascii=False)

        # 5. 页面点击卡片获取的信息
        focused_object_json = json.dumps(state.focused_object.to_dict()) if state.focused_object is not None else None

        available_flows_json = json.dumps(
            {
                "flows": [{k: v for k, v in asdict(flow).items() if k != "steps"} for flow in flows_list.flows]
            },
            ensure_ascii=False,
        )

        # 知识意图清单

        knowledge_intents_json = json.dumps(
            [{"id": intent.id, "description": intent.description} for intent in
             knowledge_intents.values()]
        )

        return {
            "user_message": user_msg,
            "current_conversation": current_conversation,
            "active_task_json": active_task_json,
            "interrupted_tasks_json": interrupted_tasks_json,
            "focused_object_json": focused_object_json,
            "available_flows_json": available_flows_json,
            "knowledge_intents_json": knowledge_intents_json
        }

    async def _predict_from_inputs_prompt(self, inputs_prompt: Dict[str, Any]) -> TurnPlan:
        """
        1. 加载提示词模板
        2. 格式化模版
        3. 调用模型
        :param inputs_prompt:
        :return:
        """

        prompt_template_text = load_prompt("turn_plan")

        prompt_template = PromptTemplate.from_template(template=prompt_template_text, template_format="jinja2")

        # ================= 新增代码开始 =================
        # 使用 ** 解包字典，直接调用模板的 format 方法
        rendered_prompt_str = prompt_template.format(**inputs_prompt)

        # 打印出来查看，或者写入日志
        print("========== 渲染后的提示词 ==========")
        print(rendered_prompt_str)
        print("====================================")

        chain = prompt_template | llm | JsonOutputParser()

        llm_response_dict: Dict[str, Any] = await chain.ainvoke(inputs_prompt)

        return TurnPlan.from_dict(llm_response_dict)


if __name__ == '__main__':
    # print(type(json.dumps([])))  # "[]"
    data = [{"name": "zs"}]

    print(json.dumps(data))
