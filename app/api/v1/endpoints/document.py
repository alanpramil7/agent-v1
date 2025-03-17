"""
Document Processing API Endpoints

This module provides endpoints for processing and indexing document files.
It allows clients to upload documents which are then processed and added to the vector store
for later retrieval and querying.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependency import get_document
from app.services.document import DocumentService
from app.utils.logger import logger

# Document-specific router with appropriate tags and prefix
router = APIRouter(
    prefix="/document",
    tags=["document"],
)


@router.post(
    "",
    summary="Process and index a document",
    description="Upload a document file for processing and indexing in the vector store",
)
async def process_document(
    file: UploadFile = File(...),
    document: DocumentService = Depends(get_document),
):
    """
    Process and index an uploaded document file.

    This endpoint accepts document uploads (PDF, DOCX, etc.), processes them,
    and adds them to the vector database for later retrieval. The document
    is split into chunks and indexed for semantic search.

    Args:
        file: The uploaded document file
        indexer: IndexerService dependency for document indexing
        database: DatabaseService dependency for storing document metadata

    Returns:
        dict: Status of the document processing operation

    Raises:
        HTTPException: If file upload fails or processing encounters an error
    """
    logger.debug(f"Processing file: {file.filename}")

    try:
        # Read file content
        content = await file.read()

        # Process the uploaded document
        result = await document.index_document(
            content=content,
            file_name=file.filename,
        )

        logger.info(f"Successfully processed document: {file.filename}")
        return result

    except Exception as e:
        logger.error(f"Error processing document {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}",
        )
