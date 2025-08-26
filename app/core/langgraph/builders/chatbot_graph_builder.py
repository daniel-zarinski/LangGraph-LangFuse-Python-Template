"""Chatbot graph builder for creating chatbot-specific workflow graphs."""

from typing import Dict, Literal, Optional

from langchain_core.messages import ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from openai import OpenAIError

from app.core.config import Environment, settings
from app.core.langgraph.builders.base_graph_builder import BaseGraphBuilder
from app.core.langgraph.llm.llm_manager import LLMManager, OpenAIModel
from app.core.langgraph.tools import tools
from app.core.logging import logger
from app.core.metrics import llm_inference_duration_seconds
from app.core.prompts import SYSTEM_PROMPT
from app.schemas import GraphState
from app.utils import dump_messages, prepare_messages


class ChatbotGraphBuilder(BaseGraphBuilder):
    """Builds the specific chatbot workflow graph structure.
    
    Defines the nodes, edges, and routing logic unique to chatbots.
    """

    def __init__(self, llm_manager: LLMManager):
        """Initialize the chatbot graph builder.
        
        Args:
            llm_manager: The LLM manager for handling different providers.
        """
        super().__init__()
        self.llm_manager = llm_manager
        self.tools_by_name = {tool.name: tool for tool in tools}
        self._graph: Optional[CompiledStateGraph] = None

    async def _chat(self, state: GraphState) -> Dict:
        """Process the chat state and generate a response.

        Args:
            state (GraphState): The current state of the conversation.

        Returns:
            Dict: Updated state with new messages.
        """
        # Use the new dynamic method - you can now pass any OpenAI or Google model
        llm = self.llm_manager.get_llm(OpenAIModel.GPT_4O_MINI)
        messages = prepare_messages(state.messages, llm, SYSTEM_PROMPT)

        llm_calls_num = 0

        # Configure retry attempts based on environment
        max_retries = settings.MAX_LLM_CALL_RETRIES

        for attempt in range(max_retries):
            try:
                with llm_inference_duration_seconds.labels(model=llm.model_name).time():
                    generated_state = {"messages": [await llm.ainvoke(dump_messages(messages))]}
                logger.info(
                    "llm_response_generated",
                    session_id=state.session_id,
                    llm_calls_num=llm_calls_num + 1,
                    model=settings.LLM_MODEL,
                    environment=settings.ENVIRONMENT.value,
                )
                return generated_state
            except OpenAIError as e:
                logger.error(
                    "llm_call_failed",
                    llm_calls_num=llm_calls_num,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                    environment=settings.ENVIRONMENT.value,
                )
                llm_calls_num += 1

                continue

        raise Exception(f"Failed to get a response from the LLM after {max_retries} attempts")

    async def _tool_call(self, state: GraphState) -> Dict:
        """Process tool calls from the last message.

        Args:
            state: The current agent state containing messages and tool calls.

        Returns:
            Dict with updated messages containing tool responses.
        """
        outputs = []
        for tool_call in state.messages[-1].tool_calls:
            tool_result = await self.tools_by_name[tool_call["name"]].ainvoke(tool_call["args"])
            outputs.append(
                ToolMessage(
                    content=tool_result,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

    def _should_continue(self, state: GraphState) -> Literal["end", "continue"]:
        """Determine if the agent should continue or end based on the last message.

        Args:
            state: The current agent state containing messages.

        Returns:
            Literal["end", "continue"]: "end" if there are no tool calls, "continue" otherwise.
        """
        messages = state.messages
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return "end"
        # Otherwise if there is, we continue
        else:
            return "continue"

    async def build_graph(self) -> Optional[CompiledStateGraph]:
        """Create and configure the chatbot LangGraph workflow.

        Returns:
            Optional[CompiledStateGraph]: The configured LangGraph instance or None if build fails.
        """
        if self._graph is None:
            try:
                graph_builder = StateGraph(GraphState)
                graph_builder.add_node("chat", self._chat)
                graph_builder.add_node("tool_call", self._tool_call)
                graph_builder.add_conditional_edges(
                    "chat",
                    self._should_continue,
                    {"continue": "tool_call", "end": END},
                )
                graph_builder.add_edge("tool_call", "chat")
                graph_builder.set_entry_point("chat")
                graph_builder.set_finish_point("chat")

                # Set up checkpointer using base class method
                checkpointer = await self._setup_checkpointer()

                self._graph = graph_builder.compile(
                    checkpointer=checkpointer, 
                    name=f"{settings.PROJECT_NAME} Chatbot ({settings.ENVIRONMENT.value})"
                )

                logger.info(
                    "chatbot_graph_created",
                    graph_name=f"{settings.PROJECT_NAME} Chatbot",
                    environment=settings.ENVIRONMENT.value,
                    has_checkpointer=checkpointer is not None,
                )
            except Exception as e:
                logger.error("chatbot_graph_creation_failed", error=str(e), environment=settings.ENVIRONMENT.value)
                # In production, we don't want to crash the app
                if settings.ENVIRONMENT == Environment.PRODUCTION:
                    logger.warning("continuing_without_chatbot_graph")
                    return None
                raise e

        return self._graph
