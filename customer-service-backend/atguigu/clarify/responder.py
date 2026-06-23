import json

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.infrastructure import llm
from atguigu.plan.turn_plan import ClarifyReason
from atguigu.prompts.history_builder import HistoryBuilder
from atguigu.prompts.loader import load_prompt


class ClarifyResponder:
    """
    澄清回复器：当对话引擎在规划阶段发现用户意图不明确时，
    负责根据澄清原因（ClarifyReason）生成自然语言回复，引导用户补充或明确信息。
    """

    async def respond(self, state: DialogueState, reason: ClarifyReason) -> list[BotMessage]:
        """
        根据当前对话状态和澄清原因，调用 LLM 生成一条澄清回复。

        :param state: 当前对话状态，包含会话历史、用户消息、聚焦对象等信息
        :param reason: 需要澄清的原因枚举，如缺少轨道、缺少意图等
        :return: 包含一条 BotMessage 的列表，作为给用户的澄清回复
        """

        # 根据澄清原因生成初始的澄清提示文本
        clarify_message = self.build_clarify_message(reason=reason, state=state)
        # 获取当前轮次的用户消息并渲染为字符串
        user_message = state.pending_turn.user_message
        user_message_str = HistoryBuilder._render_user_message(user_message)
        # 取最近 10 轮对话历史，构建上下文字符串供 LLM 参考
        history_str = HistoryBuilder.build(state.current_session().turns[-10:])
        # 将用户当前聚焦的对象（订单/商品等）序列化为 JSON，若无则为 None
        focused_object_str = json.dumps(state.focused_object.to_dict(),
                                        ensure_ascii=False) if state.focused_object is not None else None

        # 加载澄清回复的 Jinja2 提示词模板
        prompt_text = load_prompt("clarify_respond")
        prompt_template = PromptTemplate.from_template(template=prompt_text, template_format="jinja2")
        # 构建 LangChain 链：提示词模板 -> LLM -> 字符串输出解析
        chain = prompt_template | llm | StrOutputParser()
        # 异步调用 LLM，传入用户消息、历史、聚焦对象、澄清文本和原因
        rewritten = await  chain.ainvoke({
            "user_message": user_message_str,
            "history": history_str,
            "focused_object": focused_object_str,
            "clarify_message": clarify_message,
            "reason": reason.value
        })
        return [BotMessage(text=rewritten)]


    def build_clarify_message(
            self,
            reason: ClarifyReason,
            state: DialogueState,
    ) -> str:
        """
        根据不同的澄清原因，构建对应的初始澄清提示文本。
        该文本会作为 LLM 的输入之一，由 LLM 润色后返回给用户。

        :param reason: 澄清原因枚举
        :param state: 当前对话状态，用于获取聚焦对象等上下文信息
        :return: 澄清提示文本字符串
        """
        # 用户同时涉及多个轨道（业务+咨询），需要让用户选择优先处理哪个
        if reason is ClarifyReason.MULTIPLE_TRACKS:
            return "你这次同时提到了多个方向。我们先处理一个，你想先办业务还是先咨询信息呢？"

        # 用户未提供聚焦对象（如订单号、商品），需要引导用户先发送
        if reason is ClarifyReason.MISSING_FOCUSED_OBJECT:
            return "请先发送你想咨询的对象，我再继续帮你看。"

        # 用户走知识咨询轨道但未明确具体意图（查商品、查订单、查规则等）
        if reason is ClarifyReason.MISSING_KNOWLEDGE_INTENT:
            return "你是想了解商品信息、订单信息，还是售后配送规则呢？"

        # 用户消息无法判断属于哪个轨道（业务/咨询/闲聊），需要确认方向
        if reason is ClarifyReason.MISSING_TRACK:
            return "你是想先处理业务问题，还是先咨询信息呢？"

        # 用户走业务轨道但未提供具体的任务指令（查订单、查物流、退款等）
        if reason is ClarifyReason.MISSING_TASK_COMMANDS:
            return "你这次是想办理什么业务呢？比如查订单、查物流，或者申请退款。"

        # 用户发送了聚焦对象但未说明想对该对象做什么操作，根据对象类型给出不同引导
        if reason is ClarifyReason.OBJECT_REQUIRES_INTENT:
            focused_object = state.focused_object
            if focused_object is not None and focused_object.type == "order":
                return "我已经收到这个订单了。你想查订单状态、查物流，还是申请退款呢？"
            if focused_object is not None and focused_object.type == "product":
                return "我已经收到这个商品了。你想了解它的商品信息、发货情况，还是售后相关问题呢？"

        # 兜底：无法匹配到任何已知原因时，给出通用的澄清提示
        return "我还需要再确认一下你的意思，你可以换个更具体的说法告诉我。"
