from langchain.chat_models import init_chat_model

from langchain_core.language_models import BaseChatModel


from atguigu.conf.config import settings



llm:BaseChatModel=init_chat_model(
    model=settings.llm_model,
    model_provider="openai",
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
    temperature=0,
)

if __name__ == '__main__':
    invoke = llm.invoke("你好吗? 我今天好累 给我提供一些情绪价值")
    print(invoke.content)
