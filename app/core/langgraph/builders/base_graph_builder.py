"""Base graph builder for shared database and checkpointer infrastructure."""

from abc import ABC, abstractmethod
from typing import Optional

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph.state import CompiledStateGraph
from psycopg_pool import AsyncConnectionPool

from app.core.config import Environment, settings
from app.core.logging import logger


class BaseGraphBuilder(ABC):
    """Abstract base class for building LangGraph workflows.
    
    Manages PostgreSQL connection pooling and checkpointer setup that's shared
    across ALL graph implementations.
    """

    def __init__(self):
        """Initialize the base graph builder."""
        self._connection_pool: Optional[AsyncConnectionPool] = None

    async def _get_connection_pool(self) -> Optional[AsyncConnectionPool]:
        """Get a PostgreSQL connection pool using environment-specific settings.

        Returns:
            Optional[AsyncConnectionPool]: A connection pool for PostgreSQL database or None if init fails.
        """
        if self._connection_pool is None:
            try:
                # Configure pool size based on environment
                max_size = settings.POSTGRES_POOL_SIZE

                self._connection_pool = AsyncConnectionPool(
                    settings.POSTGRES_URL,
                    open=False,
                    max_size=max_size,
                    kwargs={
                        "autocommit": True,
                        "connect_timeout": 5,
                        "prepare_threshold": None,
                    },
                )
                await self._connection_pool.open()
                logger.info("connection_pool_created", max_size=max_size, environment=settings.ENVIRONMENT.value)
            except Exception as e:
                logger.error("connection_pool_creation_failed", error=str(e), environment=settings.ENVIRONMENT.value)
                # In production, we might want to degrade gracefully
                if settings.ENVIRONMENT == Environment.PRODUCTION:
                    logger.warning("continuing_without_connection_pool", environment=settings.ENVIRONMENT.value)
                    return None
                raise e
        return self._connection_pool

    async def _setup_checkpointer(self) -> Optional[AsyncPostgresSaver]:
        """Set up the AsyncPostgresSaver checkpointer.

        Returns:
            Optional[AsyncPostgresSaver]: Configured checkpointer or None if setup fails.
        """
        connection_pool = await self._get_connection_pool()
        if connection_pool:
            checkpointer = AsyncPostgresSaver(connection_pool)
            await checkpointer.setup()
            return checkpointer
        else:
            # In production, proceed without checkpointer if needed
            if settings.ENVIRONMENT != Environment.PRODUCTION:
                raise Exception("Connection pool initialization failed")
            return None

    @abstractmethod
    async def build_graph(self) -> Optional[CompiledStateGraph]:
        """Build and compile the graph.

        Returns:
            Optional[CompiledStateGraph]: The compiled graph or None if build fails.
        """
        pass

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._connection_pool:
            await self._connection_pool.close()
            self._connection_pool = None
            logger.info("connection_pool_closed")
