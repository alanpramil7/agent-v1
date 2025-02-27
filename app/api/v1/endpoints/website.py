"""
Website Processing API Endpoints

This module provides endpoints for processing and indexing website content.
It allows clients to submit website URLs for crawling, processing, and
adding to the vector store for later retrieval and querying.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependency import get_database, get_indexer
from app.models.website import WebsiteProcessingRequest
from app.services.database import DatabaseService
from app.services.indexer import IndexerService
from app.services.website import WebsiteService
from app.utils.logger import logger

# Website-specific router with appropriate tags and prefix
router = APIRouter(prefix="/website", tags=["website"])


@router.post(
    "",
    summary="Process and index a website",
    description="Submit a website URL for crawling, processing, and indexing in the vector store",
)
async def process_website(
    request: WebsiteProcessingRequest,
    indexer: IndexerService = Depends(get_indexer),
    database: DatabaseService = Depends(get_database),
):
    """
    Process and index a website by URL.

    This endpoint accepts a website URL, crawls its content, processes it,
    and adds it to the vector database for later retrieval. The website content
    is split into chunks and indexed for semantic search.

    Args:
        request: The website processing request containing the URL
        indexer: IndexerService dependency for content indexing
        database: DatabaseService dependency for storing website metadata

    Returns:
        dict: Status of the website processing operation

    Raises:
        HTTPException: If processing encounters an error
    """
    try:
        logger.debug(f"Processing website {request.url}")

        # Check if website was already processed
        if database.website_exists(str(request.url)):
            logger.info(f"Website {request.url} already processed, skipping")
            return {"status": "Website already processed."}

        # Initialize website service
        website_service: WebsiteService = WebsiteService(
            indexer,
            database,
        )

        # Process the website
        result = await website_service.process_website(request.url)
        logger.info(f"Successfully processed website: {request.url}")
        return result

    except Exception as e:
        logger.error(f"Error processing website {request.url}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing website: {request.url}: {str(e)}",
        )
