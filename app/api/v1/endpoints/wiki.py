import os

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependency import get_database, get_indexer
from app.core.config import settings
from app.models.wiki import WikiProcessingRequest
from app.services.database import DatabaseService
from app.services.indexer import IndexerService
from app.services.wiki import WikiService
from app.utils.logger import logger

router = APIRouter(
    prefix="/wiki",
    tags=["wiki"],
)


@router.post("")
async def process_wiki(
    request: WikiProcessingRequest,
    indexer: IndexerService = Depends(get_indexer),
    database: DatabaseService = Depends(get_database),
):
    """Process wiki pages and store them in the vector database."""
    logger.debug(f"Processing wiki {request.wikiIdentifier}.")

    pat = settings.wiki_access_token
    if not pat:
        raise HTTPException(status_code=500, detail="Wiki access token not configured")

    wiki_service = WikiService(
        organization=request.organization,
        project=request.project,
        wiki_identifier=request.wikiIdentifier,
        pat=pat,
        database=database,
        indexer=indexer,
    )

    result = await wiki_service.process_wiki(
        request.organization,
        request.project,
        request.wikiIdentifier,
    )

    return result
