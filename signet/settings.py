from pydantic_settings import BaseSettings
from typing import Annotated
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    PRIVATE_KEY_PEM: Annotated[Path, str]
    PUBLIC_KEY_PEM: Annotated[Path, str]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()  # ty:ignore[missing-argument], noqa
