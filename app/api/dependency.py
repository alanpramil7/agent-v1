from functools import lru_cache

from app.services.database import DatabaseService
from app.services.indexer import IndexerService
from app.services.agent import AgentService


@lru_cache
def get_indexer() -> IndexerService:
    return IndexerService()


@lru_cache
def get_database() -> DatabaseService:
    return DatabaseService()


@lru_cache
def get_agent() -> AgentService:
    indexer = get_indexer()
    return AgentService(indexer=indexer)
