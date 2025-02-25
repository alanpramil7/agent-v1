from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependency import get_database, get_indexer
from app.models.website import WebsiteProcessingRequest
from app.services.database import DatabaseService
from app.services.indexer import IndexerService
from app.services.website import WebsiteService
from app.utils.logger import logger

router = APIRouter(prefix="/website", tags=["website"])


@router.post("")
async def process_website(
    request: WebsiteProcessingRequest,
    indexer: IndexerService = Depends(get_indexer),
    database: DatabaseService = Depends(get_database),
):
    try:
        logger.debug(f"Processing website {request.url}")
        if database.website_exists(str(request.url)):
            return {"status": "Website already processed."}

        website_service: WebsiteService = WebsiteService(
            indexer,
            database,
        )

        return await website_service.process_website(request.url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webiste: {request.url}: {e}",
        )
