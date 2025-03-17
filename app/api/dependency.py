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
from app.services.memory import MemoryService
from app.services.document import DocumentService
from app.services.website import WebsiteService


@lru_cache
def get_document() -> DocumentService:
    """
    Provides a cached instance of the DocumentService.

    The lru_cache decorator ensures this function returns the same DocumentSerivce
    instance across multiple calls, optimizing resource usage.

    Returns:
        DocumentSerivce: A singleton instance of the DocumentSerivce
    """
    indexer = get_indexer()
    database = get_database()
    return DocumentService(indexer, database)


@lru_cache
def get_website() -> WebsiteService:
    """
    Provides a cached instance of the WebsiteService.

    The lru_cache decorator ensures this function returns the same WebsiteService
    instance across multiple calls, optimizing resource usage.

    Returns:
        WebsiteService: A singleton instance of the WebsiteService
    """
    indexer = get_indexer()
    database = get_database()
    return WebsiteService(indexer, database)


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
    memory = get_memory()
    return AgentService(indexer=indexer, memory=memory)


@lru_cache
def get_memory() -> MemoryService:
    return MemoryService()


def initialize_dependency():
    """
    Initilalize all the service class.
    """
    get_database()
    get_document()
    get_indexer()
    get_memory()
    get_agent()
