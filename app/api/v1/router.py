"""
API Router Configuration Module (v1)

This module configures the main APIRouter for version 1 of the API.
It includes all endpoint routers from the v1 endpoints package.

The API follows a modular structure where:
- This main router (v1) handles the API version prefix
- Individual feature-specific routers handle their own routes
"""

from fastapi import APIRouter

from app.api.v1.endpoints.agent import router as agent_router
from app.api.v1.endpoints.document import router as document_router
from app.api.v1.endpoints.website import router as website_router
from app.api.v1.endpoints.wiki import router as wiki_router

# Main v1 API router
router = APIRouter(
    prefix="/v1",
)

# Include all feature-specific routers
router.include_router(wiki_router)
router.include_router(document_router)
router.include_router(website_router)
router.include_router(agent_router)
