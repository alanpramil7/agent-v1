"""
Document Service Module

This module provides services for processing document files uploaded by users.
It handles document loading, text extraction, chunking, and indexing into the
vector database for later retrieval and querying.

The DocumentService supports multiple document formats (PDF, DOCX) and ensures
proper validation, error handling, and deduplication of document processing.
"""

from pathlib import Path
from typing import Any, Dict, List

from fastapi import HTTPException, status
from langchain_core.documents import Document

from app.core.config import settings
from app.services.database import DatabaseService
from app.services.indexer import IndexerService
from app.utils.logger import logger


class DocumentService:
    """
    Service for processing and indexing document files.

    This service handles the complete lifecycle of document processing:
    - Loading document files and extracting text
    - Validating file formats
    - Splitting documents into chunks
    - Adding document chunks to the vector store
    - Recording processed documents in the database

    It works with the IndexerService for vector operations and
    DatabaseService for tracking processed documents.
    """

    def __init__(self, indexer: IndexerService, database: DatabaseService):
        """
        Initialize the DocumentService.

        Args:
            indexer: Service for vector indexing operations
            database: Service for tracking processed documents
        """
        self.indexer = indexer
        self.database = database
        self.supported_extension = settings.supported_extensions
        logger.debug(
            f"Document service initialized with supported extensions: {', '.join(self.supported_extension.keys())}"
        )

    async def _create_docs(self, file_path: Path) -> List[Document]:
        """
        Create document objects from a file.

        Args:
            file_path: Path to the document file

        Returns:
            List[Document]: List of document objects extracted from the file

        Raises:
            HTTPException: If file format is unsupported or loading fails
        """
        logger.debug(f"Creating documents for file: {file_path}")

        # Extract and validate file extension
        extension = Path(file_path).suffix.lower().lstrip(".")
        logger.debug(f"Detected file extension: {extension}")

        # Check if file format is supported
        if extension not in self.supported_extension:
            supported_formats = ", ".join(self.supported_extension.keys())
            logger.error(
                f"Unsupported file format: {extension}. Supported formats: {supported_formats}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Supported formats: {supported_formats}",
            )

        try:
            # Load document using appropriate loader
            loader_class = self.supported_extension[extension]
            logger.debug(f"Using loader class: {loader_class.__name__}")

            docs = loader_class(str(file_path)).load()
            logger.debug(f"Created {len(docs)} documents from file: {file_path.name}")

            return docs

        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process document: {str(e)}",
            )

    async def process_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Process a document file into chunks and add to vector store.

        Args:
            file_path: Path to the document file

        Returns:
            Dict[str, Any]: Processing status and metadata

        Raises:
            HTTPException: If processing fails
        """
        logger.info(f"Processing document: {file_path.name}")

        # Validate indexer initialization
        if not self.indexer.vector_store or not self.indexer.text_splitter:
            logger.error("Indexer not initialized properly")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Indexer is not initialized properly",
            )

        try:
            # Create document objects from file
            docs = await self._create_docs(file_path)

            # Split documents into chunks
            logger.debug("Splitting documents into chunks")
            chunks = self.indexer.text_splitter.split_documents(docs)
            logger.debug(f"Split documents into {len(chunks)} chunks")

            # Add chunks to vector store
            logger.debug("Adding chunks to vector store")
            self.indexer.vector_store.add_documents(chunks)
            logger.debug("Successfully added chunks to vector store")

            # Record document in database
            self.database.add_document(Path(file_path).name)
            logger.info(f"Successfully processed document: {file_path.name}")

            return {
                "status": "Successfully indexed file",
                "file_name": Path(file_path).name,
                "chunks": len(chunks),
            }

        except HTTPException:
            # Re-raise HTTPExceptions without wrapping
            raise

        except Exception as e:
            logger.error(f"Error processing document {file_path.name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process document: {str(e)}",
            )

    async def index_document(self, content: bytes, file_name: str) -> Dict[str, Any]:
        """
        Save and index a document from uploaded content.

        Args:
            content: Binary content of the uploaded document
            file_name: Name of the document file

        Returns:
            Dict[str, Any]: Processing status and metadata

        Raises:
            HTTPException: If processing fails
        """
        logger.debug(f"Indexing document: {file_name}")

        try:
            # Check if document already exists
            document_exists = self.database.document_exists(file_name)
            if document_exists:
                logger.info(f"Document {file_name} is already processed, skipping")
                return {"status": "Document already processed"}

            # Create directory for document storage if it doesn't exist
            docs_dir = settings.data_dir / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)

            # Save file to disk
            file_path = docs_dir / file_name
            with open(file_path, "wb") as f:
                f.write(content)
            logger.debug(f"Saved document to: {file_path}")

            # Process the saved document
            return await self.process_document(file_path)

        except Exception as e:
            logger.error(f"Error indexing document {file_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to index document: {str(e)}",
            )
