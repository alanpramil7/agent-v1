from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings
from app.utils.logger import logger


class MemoryService:
    def __init__(self):
        self._pool = None

    async def get_pool(self) -> AsyncConnectionPool:
        """
        Get or create an async PostgreSQL connection pool.

        Returns:
            AsyncConnectionPool: Asynchronous PostgreSQL connection pool.
        """
        logger.debug("Initializing connection pool")

        if self._pool is None:
            connection_string = (
                settings.database
            )  # Alternatively, build your connection string here.

            self._pool = AsyncConnectionPool(
                conninfo=connection_string,
                max_size=20,
                open=False,
                kwargs={
                    "autocommit": True,
                    "prepare_threshold": 0,
                    "row_factory": dict_row,
                },
            )

            try:
                # Explicitly open the pool, as opening in the constructor is deprecated.
                await self._pool.open()
                logger.debug("Connection pool successfully opened.")
            except Exception as e:
                logger.error("Failed to open connection pool", exc_info=e)
                raise

        return self._pool

    async def get_memory_saver(self):
        """
        Create and return postgresql memory saver
        Returns:
            AsyncPostgresSaver: Async postgressql memory saver for langgraph
        """
        pool = await self.get_pool()
        # Get a connection from the pool but don't close it after the block
        # because AsyncPostgresSaver needs to keep it
        logger.debug("Getting connection...")
        conn = await pool.getconn()

        # Create the memory saver with the connection
        memory = AsyncPostgresSaver(conn)

        # Set up a finalizer or context manager to return the connection to the pool when done
        # This depends on how AsyncPostgresSaver uses the connection

        return memory

    async def setup_memory_table(self):
        """
        Setup postgres tables for checkpoint
        This should be called only once during application setup
        """
        try:
            pool = await self.get_pool()
            async with pool.connection() as conn:
                memory = AsyncPostgresSaver(conn)
                await memory.setup()
                logger.debug("Postgres tables for agent memory has been setup.")
        except Exception as e:
            logger.error(f"Error connecting to the database: {e}")
