from typing import Optional

from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from langchain_text_splitters.character import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.utils.logger import logger


class IndexerService:
    def __init__(self):
        self.vector_store: Optional[Chroma] = None
        self.embedding_model: Optional[AzureOpenAIEmbeddings] = None
        self.text_splitter: Optional[RecursiveCharacterTextSplitter] = None
        self._initialize()

    def _initialize(self):
        self._setup_embedding_model()
        self._setup_vector_store()
        self._setup_text_splitter()

    def _setup_embedding_model(self):
        logger.debug("Initializing embedding model")
        embedding_model = settings.embedding_model
        self.embedding_model = AzureOpenAIEmbeddings(
            model=embedding_model,
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_embedding_endpoint,
            api_version=settings.embedding_api_version,
        )
        logger.debug("Embedding model initialized.")

    def _setup_vector_store(self):
        logger.debug("Initializing Vector store.")
        vector_store = settings.data_dir / "vector_store"
        vector_store.mkdir(parents=True, exist_ok=True)

        self.vector_store = Chroma(
            persist_directory=str(vector_store),
            embedding_function=self.embedding_model,
            client_settings=Settings(
                anonymized_telemetry=False,
                is_persistent=True,
            ),
        )
        logger.debug("Vector store initialized successfully.")

    def _setup_text_splitter(self):
        logger.debug("Initializing text splitter.")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=400,
            length_function=len,
            separators=["\n\n", "\n", ".", "?", "!", " ", ""],
        )
        logger.debug("Text splitter initialzed sucessfully.")
