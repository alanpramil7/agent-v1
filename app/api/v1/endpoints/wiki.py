"""
Wiki Processing API Endpoints

This module provides endpoints for processing and indexing wiki content from sources
like Azure DevOps wikis. It allows clients to submit wiki information for retrieval,
processing, and adding to the vector store for later querying.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependency import get_database, get_indexer
from app.core.config import settings
from app.models.wiki import WikiProcessingRequest
from app.services.database import DatabaseService
from app.services.indexer import IndexerService
from app.services.wiki import WikiService
from app.utils.logger import logger

# Wiki-specific router with appropriate tags and prefix
router = APIRouter(
    prefix="/wiki",
    tags=["wiki"],
)


@router.post(
    "",
    summary="Process and index wiki content",
    description="Submit wiki information for retrieval, processing, and indexing in the vector store",
)
async def process_wiki(
    request: WikiProcessingRequest,
    indexer: IndexerService = Depends(get_indexer),
    database: DatabaseService = Depends(get_database),
):
    """
    Process and index wiki content from sources like Azure DevOps.

    This endpoint accepts wiki information (organization, project, wiki identifier),
    retrieves its content, processes it, and adds it to the vector database for
    later retrieval. The wiki content is split into chunks and indexed for semantic search.

    Args:
        request: The wiki processing request containing organization, project, and wiki identifier
        indexer: IndexerService dependency for content indexing
        database: DatabaseService dependency for storing wiki metadata

    Returns:
        dict: Status of the wiki processing operation

    Raises:
        HTTPException: If the access token is missing or processing encounters an error
    """
    try:
        logger.debug(f"Processing wiki {request.wikiIdentifier}.")

        # Check for required access token
        pat = settings.wiki_access_token
        if not pat:
            logger.error("Wiki access token not configured in settings")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Wiki access token not configured",
            )

        # Check if wiki was already processed
        if database.wiki_exists(
            request.organization, request.project, request.wikiIdentifier
        ):
            logger.info(f"Wiki {request.wikiIdentifier} already processed, skipping")
            return {"status": "Wiki already processed."}

        # Initialize wiki service
        wiki_service = WikiService(
            organization=request.organization,
            project=request.project,
            wiki_identifier=request.wikiIdentifier,
            pat=pat,
            database=database,
            indexer=indexer,
        )

        # Process the wiki
        result = await wiki_service.process_wiki(
            request.organization,
            request.project,
            request.wikiIdentifier,
        )

        logger.info(f"Successfully processed wiki: {request.wikiIdentifier}")
        return result

    except Exception as e:
        logger.error(f"Error processing wiki {request.wikiIdentifier}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing wiki: {str(e)}",
        )
