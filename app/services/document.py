from pathlib import Path

from fastapi import HTTPException, status

from app.core.config import settings
from app.services.database import DatabaseService
from app.services.indexer import IndexerService
from app.utils.logger import logger


class DocumentService:
    def __init__(self, indexer: IndexerService, database: DatabaseService):
        self.indexer = indexer
        self.database = database
        self.supported_extension = settings.supported_extensions

    def _create_docs(self, file_path: Path):
        logger.debug(f"Creating documents for file: {file_path}")
        extension = Path(file_path).suffix.lower().lstrip(".")
        logger.debug(f"Detected file extension: {extension}")

        if extension not in self.supported_extension:
            logger.error(
                f"Unsupported file format. Supported formats: {', '.join(self.supported_extension.keys())}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unsupported file format. Supported formats: {', '.join(self.supported_extension.keys())}",
            )

        loader_class = self.supported_extension[extension]
        logger.debug(f"using loader class: {loader_class}")

        docs = loader_class(file_path).load()
        logger.debug(f"Created {len(docs)} documents.")

        return docs

    def process_document(self, file_path: Path):
        if not self.indexer.vector_store and not self.indexer.text_splitter:
            logger.error("Indexer not initialized.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Indexer is not initialized properly",
            )

        docs = self._create_docs(file_path)
        logger.debug("Splitting documents into chunks.")
        chunks = self.indexer.text_splitter.split_documents(docs)
        logger.debug(f"Split documents into {len(chunks)} chunks.")

        logger.debug("Adding chunks into vectorstore.")
        self.indexer.vector_store.add_documents(chunks)
        logger.debug("Added chunks into vectorstore.")

        self.database.add_document(Path(file_path).name)

        return {
            "status": "sucessfuly indexed file.",
            "file_name": Path(file_path).name,
            "chunks": len(chunks),
        }

    async def index_document(self, content: bytes, file_name: str):
        document_exists = self.database.document_exists(file_name)
        if document_exists:
            logger.debug(f"Document {file_name} is already processed.")
            return {"status": "Document already pocessed."}
        docs_dir = settings.data_dir / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        file_path = docs_dir / file_name
        with open(file_path, "wb") as f:
            f.write(content)

        return self.process_document(file_path)
