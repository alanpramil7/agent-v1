from fastapi import APIRouter

from app.api.v1.endpoints.document import router as document_router
from app.api.v1.endpoints.website import router as website_router
from app.api.v1.endpoints.wiki import router as wiki_router

router = APIRouter(
    prefix="/v1",
)

router.include_router(wiki_router)
router.include_router(document_router)
router.include_router(website_router)
