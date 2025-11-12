from pydantic_settings import BaseSettings
from typing import Annotated
from pathlib import Path
from dotenv import load_dotenv()

load_dotenv()


class Settings(BaseSettings):
    PRIVATE_KEY_PEM: Annotated[Path]