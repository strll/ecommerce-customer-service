from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict, main

ENV_FILE_DIR=Path(__file__).resolve().parents[2]

EBV_FILE_PATH=ENV_FILE_DIR / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=EBV_FILE_PATH, env_file_encoding="utf-8", extra="ignore")

    # LLM
    llm_api_key: str              # ← 没有默认值 = 必填，启动期缺失直接抛 ValidationError
    llm_model: str
    llm_base_url: str

    # 数据库
    database_url: str

    # 商城 API
    commerce_api_base_url: str

    # TTS
    tts_model: str = "cosyvoice-v3-flash"  # ← 有默认值 = 可选
    # ...

settings = Settings()

if __name__ == "__main__":
    print( settings.llm_model)