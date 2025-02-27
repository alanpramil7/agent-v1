"""
API Dependencies Module

This module provides dependency functions for FastAPI dependency injection.
These functions create and cache service instances to be used across the API.
Using the lru_cache decorator ensures each service is only instantiated once per application instance.
"""

from functools import lru_cache

from app.services.agent import AgentService
from app.services.database import DatabaseService
from app.services.indexer import IndexerService


@lru_cache
def get_indexer() -> IndexerService:
    """
    Provides a cached instance of the IndexerService.

    The lru_cache decorator ensures this function returns the same IndexerService
    instance across multiple calls, optimizing resource usage.

    Returns:
        IndexerService: A singleton instance of the IndexerService
    """
    return IndexerService()


@lru_cache
def get_database() -> DatabaseService:
    """
    Provides a cached instance of the DatabaseService.

    The lru_cache decorator ensures this function returns the same DatabaseService
    instance across multiple calls, optimizing resource usage.

    Returns:
        DatabaseService: A singleton instance of the DatabaseService
    """
    return DatabaseService()


@lru_cache
def get_agent() -> AgentService:
    """
    Provides a cached instance of the AgentService.

    This dependency has its own dependencies (IndexerService) which are
    automatically resolved through the get_indexer dependency.

    Returns:
        AgentService: A singleton instance of the AgentService
    """
    indexer = get_indexer()
    return AgentService(indexer=indexer)
