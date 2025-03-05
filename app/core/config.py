"""
Application Configuration Module

This module manages application configuration using Pydantic settings management.
It centralizes all configuration variables, including application metadata,
server settings, paths, and external API configuration like Azure OpenAI.

Environment variables can override default values when loaded through the .env file.
"""

from functools import lru_cache
from pathlib import Path
from typing import Dict, Type

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_community.document_loaders.base import BaseLoader
from langchain_groq import ChatGroq
from langchain_openai import AzureChatOpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict


@lru_cache
class Settings(BaseSettings):
    """
    Application settings management using Pydantic BaseSettings.

    This class manages all application configuration with type validation.
    The @lru_cache decorator ensures this class is only instantiated once,
    improving performance across the application.

    Environment variables with matching names will override these default values.
    """

    # Application metadata
    app_name: str = "AmBlue"
    app_description: str = "Amadis AI Agent"
    version: str = "0.1"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "DEBUG"  # Should be set to INFO or WARNING in production

    # Path configurations
    root_dir: Path = Path(__file__).parent.parent.parent
    data_dir: Path = root_dir / "data"

    # Document loader configuration
    supported_extensions: Dict[str, Type[BaseLoader]] = {
        "pdf": PyPDFLoader,
        "docx": Docx2txtLoader,
    }

    # Azure OpenAI configuration
    # These values need to be provided via environment variables in production
    embedding_model: str = "text-embedding-3-small"
    azure_openai_endpoint: str
    azure_openai_deployment_name: str
    openai_api_version: str
    azure_openai_api_key: str
    wiki_access_token: str
    azure_embedding_endpoint: str
    embedding_api_version: str

    groq_api_key: str

    # Database connection string
    database: str

    @property
    def llm(self) -> AzureChatOpenAI:
        """
        Creates and returns a configured AzureChatOpenAI instance.

        This property allows lazy initialization of the language model
        with the current configuration settings.

        Returns:
            AzureChatOpenAI: Configured language model instance
        """
        return AzureChatOpenAI(
            azure_endpoint=self.azure_openai_endpoint,
            deployment_name=self.azure_openai_deployment_name,
            openai_api_version=self.openai_api_version,
            api_key=self.azure_openai_api_key,
        )

    # @property
    # def llm(self) -> ChatGroq:
    #     return ChatGroq(
    #         # model="deepseek-r1-distill-llama-70b",
    #         model="llama-3.3-70b-versatile",
    #         api_key=self.groq_api_key,
    #     )

    # Configure Pydantic to load environment variables from .env file
    model_config = SettingsConfigDict(env_file=".env")


# Create a singleton instance of Settings
# This will be imported by other modules
settings = Settings()
