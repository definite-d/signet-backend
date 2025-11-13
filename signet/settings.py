from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    PRIVATE_KEY_PEM: Annotated[Path, str]
    PUBLIC_KEY_PEM: Annotated[Path, str]
    API_KEY_LENGTH: Annotated[int, str] = 24
    OPENAI_API_KEY: Annotated[SecretStr, str]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()  # ty:ignore[missing-argument], noqa
