from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependency import get_database, get_indexer
from app.services.database import DatabaseService
from app.services.document import DocumentService
from app.services.indexer import IndexerService
from app.utils.logger import logger

router = APIRouter(
    prefix="/document",
    tags=["document"],
)


@router.post("")
async def process_document(
    file: UploadFile = File(...),
    indexer: IndexerService = Depends(get_indexer),
    database: DatabaseService = Depends(get_database),
):
    """"""
    logger.debug(f"Processing file: {file.filename}")

    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File not found. Please upload the file",
        )

    content = await file.read()
    document_service = DocumentService(indexer, database)

    result = await document_service.index_document(
        content=content,
        file_name=file.filename,
    )

    return result
