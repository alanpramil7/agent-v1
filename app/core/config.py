from functools import lru_cache
from pathlib import Path
from typing import Dict, Type

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_community.document_loaders.base import BaseLoader
from pydantic_settings import BaseSettings, SettingsConfigDict


@lru_cache
class Settings(BaseSettings):
    app_name: str = "AmBlue"
    app_description: str = "Amadis AI Agent"
    version: str = "0.1"

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "DEBUG"

    root_dir: Path = Path(__file__).parent.parent.parent
    data_dir: Path = root_dir / "data"

    supported_extensions: Dict[str, Type[BaseLoader]] = {
        "pdf": PyPDFLoader,
        "docx": Docx2txtLoader,
    }

    embedding_model: str = "text-embedding-3-small"
    azure_openai_endpoint: str
    azure_openai_deployment_name: str
    openai_api_version: str
    azure_openai_api_key: str
    wiki_access_token: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
