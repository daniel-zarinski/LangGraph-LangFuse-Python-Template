"""Base graph class providing common interface and functionality."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

from asgiref.sync import sync_to_async
from langchain_core.messages import BaseMessage, convert_to_openai_messages
from langfuse.langchain import CallbackHandler
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import StateSnapshot

from app.core.config import settings
from app.core.logging import logger
from app.schemas import Message
from app.utils import dump_messages


class BaseGraph(ABC):
    """Abstract base class providing the common interface that all graphs must implement.
    
    Handles graph lifecycle and standard graph operations.
    """

    def __init__(self):
        """Initialize the base graph."""
        self._graph: Optional[CompiledStateGraph] = None

    @abstractmethod
    async def _create_graph(self) -> Optional[CompiledStateGraph]:
        """Create the graph for this graph instance.

        Returns:
            Optional[CompiledStateGraph]: The compiled graph or None if creation fails.
        """
        pass

    async def _ensure_graph(self) -> Optional[CompiledStateGraph]:
        """Ensure the graph is created and return it.

        Returns:
            Optional[CompiledStateGraph]: The compiled graph or None if creation fails.
        """
        if self._graph is None:
            self._graph = await self._create_graph()

        return self._graph

    def _create_config(self, session_id: str, user_id: Optional[str] = None) -> dict:
        """Create configuration for graph execution.

        Args:
            session_id: The session ID for the conversation.
            user_id: Optional user ID for tracking.

        Returns:
            dict: Configuration for graph execution.
        """
        return {
            "configurable": {"thread_id": session_id},
            "callbacks": [CallbackHandler()],
            "metadata": {
                "user_id": user_id,
                "session_id": session_id,
                "langfuse_session_id": session_id,
                "langfuse_user_id": user_id,
                "environment": settings.ENVIRONMENT.value,
                "debug": False,
            },
        }

    def _process_messages(self, messages: list[BaseMessage]) -> list[Message]:
        """Process BaseMessage list into Message list for API response.

        Args:
            messages: List of BaseMessage objects from the graph.

        Returns:
            list[Message]: Processed messages for API response.
        """
        openai_style_messages = convert_to_openai_messages(messages)
        # keep just assistant and user messages
        return [
            Message(**message)
            for message in openai_style_messages
            if message["role"] in ["assistant", "user"] and message["content"]
        ]

    async def get_response(
        self,
        messages: list[Message],
        session_id: str,
        user_id: Optional[str] = None,
    ) -> list[dict]:
        """Get a response from the graph.

        Args:
            messages: The messages to send to the graph.
            session_id: The session ID for tracking.
            user_id: Optional user ID for tracking.

        Returns:
            list[dict]: The response from the graph.
        """
        graph = await self._ensure_graph()
        if graph is None:
            raise Exception("Failed to create graph")

        config = self._create_config(session_id, user_id)
        
        try:
            response = await graph.ainvoke(
                {"messages": dump_messages(messages), "session_id": session_id}, config
            )
            return self._process_messages(response["messages"])
        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")
            raise e

    async def get_stream_response(
        self, 
        messages: list[Message], 
        session_id: str, 
        user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Get a stream response from the graph.

        Args:
            messages: The messages to send to the graph.
            session_id: The session ID for the conversation.
            user_id: Optional user ID for the conversation.

        Yields:
            str: Tokens of the graph response.
        """
        graph = await self._ensure_graph()
        if graph is None:
            raise Exception("Failed to create graph")

        config = self._create_config(session_id, user_id)

        try:
            async for token, _ in graph.astream(
                {"messages": dump_messages(messages), "session_id": session_id}, 
                config, 
                stream_mode="messages"
            ):
                try:
                    yield token.content
                except Exception as token_error:
                    logger.error("Error processing token", error=str(token_error), session_id=session_id)
                    # Continue with next token even if current one fails
                    continue
        except Exception as stream_error:
            logger.error("Error in stream processing", error=str(stream_error), session_id=session_id)
            raise stream_error

    async def get_chat_history(self, session_id: str) -> list[Message]:
        """Get the chat history for a given session ID.

        Args:
            session_id: The session ID for the conversation.

        Returns:
            list[Message]: The chat history.
        """
        graph = await self._ensure_graph()
        if graph is None:
            raise Exception("Failed to create graph")

        state: StateSnapshot = await sync_to_async(graph.get_state)(
            config={"configurable": {"thread_id": session_id}}
        )
        return self._process_messages(state.values["messages"]) if state.values else []

    async def clear_chat_history(self, session_id: str) -> None:
        """Clear all chat history for a given session ID.

        Args:
            session_id: The ID of the session to clear history for.

        Raises:
            Exception: If there's an error clearing the chat history.
        """
        # This method should be implemented by concrete classes that need it
        # since the clearing logic may vary based on the graph builder used
        raise NotImplementedError("Subclasses must implement clear_chat_history")
