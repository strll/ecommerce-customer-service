from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.infrastructure import llm
from atguigu.prompts.history_builder import HistoryBuilder
from atguigu.task.action.base import Action, ActionResult
from jinja2 import Template


class ActionResponse(Action):
    name = "action_response"

    async def run(self, state: DialogueState, action_kwargs: dict[str, Any]) -> ActionResult:
        """
        响应内容
        :param state:
        :param action_kwargs:
        :return:
        """
        text:str = action_kwargs.get('text')

        mode = action_kwargs.get('mode', 'static')

        render_text = self._render_text(state, text)

        if mode == 'static':
            return ActionResult(messages=[BotMessage(text=render_text)])
        elif mode == "rephrase":
            # 需要调用LLM 并且将text作为改写的目标传入进去
            prompt = action_kwargs['prompt']
            rephrase_text = await self._call_llm(state, prompt, render_text)
            return ActionResult(messages=[BotMessage(text=rephrase_text)])
        else:
            # 需要调用LLM,只用提供提示词即可
            prompt = action_kwargs['prompt']
            generate_text = await self._call_llm(state, prompt)
            return ActionResult(messages=[BotMessage(text=generate_text)])

    def _render_text(self, state: DialogueState,
                     text: str) -> str:
        template = Template(text)
        result = template.render(
            slots=state.active_task.slots if state.active_task else {},
            context=state.active_system_task or state.active_task,
        )
        return result



    async def _call_llm(self,
                        state: DialogueState,
                        prompt: str,
                        render_text: str = "") -> str:

        prompt_template = PromptTemplate.from_template(prompt)

        chain = prompt_template | llm | StrOutputParser()
        rephrase_text = await chain.ainvoke({
            "history": HistoryBuilder.build(state.current_session().turns[-5:]),
            "user_message": HistoryBuilder._render_user_message(state.pending_turn.user_message),
            "current_response": render_text

        })
        return rephrase_text
