from pathlib import Path

from langchain_core.prompts import PromptTemplate



def load_prompt(prompt_file_name: str) -> str:
    """
    加载prompt
    :param path:
    :return:
    """

    prompt_file_path=Path(__file__).resolve().parents[0]/"jinja2"/f"{prompt_file_name}.jinja2"

    text = prompt_file_path.read_text(encoding="utf-8")
    return text

if __name__ == '__main__':
    print(load_prompt("turn_plan"))
