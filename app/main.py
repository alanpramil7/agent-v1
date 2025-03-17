"""
FastAPI Application Entry Point

This module initializes and configures the FastAPI application, including middleware,
routes, and core services. It serves as the main entry point for the application.
"""

import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependency import get_agent, get_memory
from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.utils.logger import logger

# TODO: Move these environment variables to a proper configuration management
# system in production. Avoid hardcoding sensitive information like API keys.
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "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"
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGSMITH_PROJECT"] = "sql-agent"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug("Initializing lifespan.")
    memory_service = get_memory()
    await memory_service.setup_memory_table()
    agent = get_agent()
    await agent.ainit()

    yield


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    logger.debug(f"Creating FastAPI application with : {settings.app_name}")
    application = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        lifespan=lifespan,
        version=settings.version,
        docs_url="/docs",
    )

    # Configure CORS middleware
    # Note: For production, restrict allow_origins to specific domains
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict to specific domains in production
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
        """
        Health check endpoint to verify service is running correctly.

        Returns:
            dict: Service status and version information
        """
        logger.debug("Health check endpoint called")
        return {
            "status": "Healthy",
            "version": settings.version,
        }

    # Include API routers
    application.include_router(v1_router)

    logger.debug(f"Created FastAPI application with : {settings.app_name}")

    return application


# Create the FastAPI application instance
app = create_application()

if __name__ == "__main__":
    """
    Run the application using Uvicorn server when executed directly.
    """
    uvicorn.run(
        app=app,
        host=settings.host,
        port=settings.port,
        reload=True,
    )
