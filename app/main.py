"""
FastAPI Application Entry Point

This module initializes and configures the FastAPI application, including middleware,
routes, and core services. It serves as the main entry point for the application.

Environment variables for LangSmith are configured here but should be moved to
a proper environment file or secret management system in production.
"""

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.utils.logger import logger


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Sets up CORS middleware, registers health check endpoint, initializes services,
    and includes API routers.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    logger.debug(f"Creating FastAPI application with name: {settings.app_name}")
    application = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
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

    return application


# Create the FastAPI application instance
app = create_application()

if __name__ == "__main__":
    """
    Run the application using Uvicorn server when executed directly.
    Note: In production, use a proper ASGI server configuration instead of
    running directly with reload=True.
    """
    uvicorn.run(
        app=app,
        host=settings.host,
        port=settings.port,
        reload=True,  # Set to False in production
    )
