from functools import lru_cache

from app.services.database import DatabaseService
from app.services.indexer import IndexerService


@lru_cache
def get_indexer() -> IndexerService:
    return IndexerService()


@lru_cache
def get_database() -> DatabaseService:
    return DatabaseService()
