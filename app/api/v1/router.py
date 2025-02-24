from fastapi import APIRouter

from app.api.v1.endpoints.wiki import router as wiki_router

router = APIRouter(
    prefix="/v1",
)

router.include_router(wiki_router)
