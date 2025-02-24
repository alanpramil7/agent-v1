import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.services.indexer import IndexerService
from app.utils.logger import logger


def create_application():
    logger.debug(f"Creating FastAPI application with name: {settings.app_name}")
    application = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.version,
        docs_url="/docs",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get(
        path="/check-health",
        tags=["Health"],
        summary="Health Check Endpoint",
        description="Returns the current status and version of the service",
    )
    async def check_health() -> dict:
        logger.debug("Health check endpoint called")
        return {
            "status": "Healthy",
            "version": settings.version,
        }

    IndexerService()

    # Include API routers
    application.include_router(v1_router)

    return application


app = create_application()

if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host=settings.host,
        port=settings.port,
        reload=True,
    )
