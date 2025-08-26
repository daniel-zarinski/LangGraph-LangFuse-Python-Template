"""Chatbot agent implementation for orchestrating chatbot workflows."""

from typing import Optional

from langgraph.graph.state import CompiledStateGraph

from app.core.config import settings
from app.core.langgraph.agents.base_agent import BaseAgent
from app.core.langgraph.builders.chatbot_graph_builder import ChatbotGraphBuilder
from app.core.langgraph.llm import GoogleModel, LLMManager, OpenAIModel
from app.core.logging import logger


class ChatbotAgent(BaseAgent):
    """Implements chatbot-specific logic and integrates all chatbot components.
    
    The main orchestrator for chatbot functionality.
    """

    def __init__(self, 
                 llm_manager: Optional[LLMManager] = None, 
                 openai_model: OpenAIModel = OpenAIModel.GPT_4O_MINI,
                 google_model: GoogleModel = GoogleModel.GEMINI_FLASH):
        """Initialize the chatbot agent.

        Args:
            llm_manager: Optional LLM manager. If not provided, creates a new one with the specified models.
            openai_model: The OpenAI model to use if creating a new LLM manager. Defaults to GPT_4O_MINI.
            google_model: The Google model to use if creating a new LLM manager. Defaults to GEMINI_FLASH.
        """
        super().__init__()
        self.llm_manager = llm_manager or LLMManager(
            openai_model=openai_model,
            google_model=google_model
        )
        self.graph_builder = ChatbotGraphBuilder(self.llm_manager)

    async def _create_graph(self) -> Optional[CompiledStateGraph]:
        """Create the chatbot graph.

        Returns:
            Optional[CompiledStateGraph]: The compiled chatbot graph or None if creation fails.
        """
        return await self.graph_builder.build_graph()

    async def clear_chat_history(self, session_id: str) -> None:
        """Clear all chat history for a given session ID.

        Args:
            session_id: The ID of the session to clear history for.

        Raises:
            Exception: If there's an error clearing the chat history.
        """
        try:
            # Get the connection pool from the graph builder
            conn_pool = await self.graph_builder._get_connection_pool()
            if conn_pool is None:
                raise Exception("No connection pool available")

            # Use a new connection for this specific operation
            async with conn_pool.connection() as conn:
                for table in settings.CHECKPOINT_TABLES:
                    try:
                        await conn.execute(f"DELETE FROM {table} WHERE thread_id = %s", (session_id,))
                        logger.info(f"Cleared {table} for session {session_id}")
                    except Exception as e:
                        logger.error(f"Error clearing {table}", error=str(e))
                        raise

        except Exception as e:
            logger.error("Failed to clear chat history", error=str(e))
            raise

    @property
    def model_name(self) -> str:
        """Get the current model name for metrics and logging.
        
        Returns:
            str: The model name of the primary LLM.
        """
        return self.llm_manager.get_openai_llm().model_name

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        await self.graph_builder.cleanup()
        logger.info("chatbot_agent_cleanup_completed")
