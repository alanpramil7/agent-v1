"""
Indexer Service Module

This module provides vector database indexing and retrieval capabilities for the application.
It sets up and manages:
- Embedding models for text vectorization
- Vector store for efficient similarity search
- Text splitting for processing documents into manageable chunks

The IndexerService is a core component used by other services to index and retrieve
content from various sources (documents, websites, wikis).
"""

from typing import Optional

from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from langchain_text_splitters.character import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.utils.logger import logger


class IndexerService:
    """
    Service for managing document indexing and vector storage.

    This service initializes and manages the components needed for
    document processing and vector-based retrieval:
    - Embedding model: Converts text to vector embeddings
    - Vector store: Stores and retrieves embeddings efficiently
    - Text splitter: Splits documents into chunks for processing

    The service initializes these components on creation and provides
    them to other services for document processing and retrieval.
    """

    def __init__(self):
        """
        Initialize the IndexerService with required components.

        Sets up initial empty states for components and triggers
        the initialization process.
        """
        # Initialize component placeholders
        self.vector_store: Optional[Chroma] = None
        self.embedding_model: Optional[AzureOpenAIEmbeddings] = None
        self.text_splitter: Optional[RecursiveCharacterTextSplitter] = None

        # Perform initialization of components
        self._initialize()

    def _initialize(self):
        """
        Initialize all components required for the indexing service.

        This internal method sets up the embedding model, vector store,
        and text splitter in the correct sequence.
        """
        try:
            self._setup_embedding_model()
            self._setup_vector_store()
            self._setup_text_splitter()
            logger.debug("IndexerService initialization completed successfully")
        except Exception as e:
            logger.error(f"Failed to initialize IndexerService: {str(e)}")
            # In production, we might want to implement retry logic or
            # more sophisticated error handling here
            raise

    def _setup_embedding_model(self):
        """
        Initialize the embedding model for converting text to vectors.

        Uses Azure OpenAI embeddings with configuration from settings.
        """
        logger.debug("Initializing embedding model")
        try:
            embedding_model = settings.embedding_model
            self.embedding_model = AzureOpenAIEmbeddings(
                model=embedding_model,
                api_key=settings.azure_openai_api_key,
                azure_endpoint=settings.azure_embedding_endpoint,
                api_version=settings.embedding_api_version,
            )
            logger.debug("Embedding model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            raise

    def _setup_vector_store(self):
        """
        Initialize the vector store for storing and retrieving embeddings.

        Creates a Chroma vector database with the embedding model for
        efficient storage and retrieval of vector embeddings.
        """
        logger.debug("Initializing Vector store")
        try:
            # Create vector store directory if it doesn't exist
            vector_store_path = settings.data_dir / "vector_store"
            vector_store_path.mkdir(parents=True, exist_ok=True)

            # Initialize Chroma vector store with embedding model
            self.vector_store = Chroma(
                persist_directory=str(vector_store_path),
                embedding_function=self.embedding_model,
                client_settings=Settings(
                    anonymized_telemetry=False,  # Disable telemetry for production
                    is_persistent=True,  # Ensure data persistence
                ),
            )
            logger.debug("Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise

    def _setup_text_splitter(self):
        """
        Initialize the text splitter for document chunking.

        Creates a RecursiveCharacterTextSplitter with appropriate settings
        for splitting documents into manageable chunks for embedding.
        """
        logger.debug("Initializing text splitter")
        try:
            # Configure text splitter with appropriate chunk size and overlap
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=2000,  # Size of text chunks in characters
                chunk_overlap=400,  # Overlap between chunks to maintain context
                length_function=len,  # Function to measure text length
                # Separators in order of preference for splitting text
                separators=["\n\n", "\n", ".", "?", "!", " ", ""],
            )
            logger.debug("Text splitter initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize text splitter: {str(e)}")
            raise
