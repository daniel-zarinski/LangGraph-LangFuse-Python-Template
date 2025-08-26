"""Agent API endpoints for handling LangGraph workflows.

This module provides endpoints for executing different LangGraph workflows by name,
including regular execution and message history management.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)

from app.api.v1.auth import get_current_session
from app.core.config import settings
from app.core.langgraph.registry import GraphRegistry
from app.core.limiter import limiter
from app.core.logging import logger
from app.models.session import Session
from app.schemas.chat import (
    AgentRequest,
    ChatResponse,
)

router = APIRouter()


@router.post("/execute", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat"][0])
async def execute_graph(
    request: Request,
    agent_request: AgentRequest,
    session: Session = Depends(get_current_session),
):
    """Execute a specific LangGraph workflow by name.

    Args:
        request: The FastAPI request object for rate limiting.
        agent_request: The agent request containing graph name and messages.
        session: The current session from the auth token.

    Returns:
        ChatResponse: The processed response from the specified graph.

    Raises:
        HTTPException: If there's an error processing the request or graph not found.
    """
    try:
        logger.info(
            "agent_request_received",
            session_id=session.id,
            graph_name=agent_request.graph_name,
            message_count=len(agent_request.messages),
        )

        # Get the agent for the specified graph
        agent = GraphRegistry.get_agent(agent_request.graph_name)
        if agent is None:
            available_graphs = GraphRegistry.list_graphs()
            raise HTTPException(
                status_code=404,
                detail=f"Graph '{agent_request.graph_name}' not found. Available graphs: {', '.join(available_graphs)}"
            )

        # Execute the graph
        result = await agent.get_response(
            agent_request.messages, session.id, user_id=session.user_id
        )

        logger.info(
            "agent_request_processed", 
            session_id=session.id,
            graph_name=agent_request.graph_name,
        )

        return ChatResponse(messages=result)
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            "agent_request_failed", 
            session_id=session.id, 
            graph_name=agent_request.graph_name,
            error=str(e), 
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graphs")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def list_available_graphs(
    request: Request,
    session: Session = Depends(get_current_session),
):
    """List all available graph types.

    Args:
        request: The FastAPI request object for rate limiting.
        session: The current session from the auth token.

    Returns:
        dict: List of available graph names and their descriptions.
    """
    try:
        available_graphs = GraphRegistry.list_graphs()
        logger.info(
            "graphs_list_requested",
            session_id=session.id,
            available_graphs=available_graphs,
        )
        
        return {
            "graphs": available_graphs,
            "count": len(available_graphs),
            "message": f"Found {len(available_graphs)} available graph(s)"
        }
    except Exception as e:
        logger.error("list_graphs_failed", session_id=session.id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{graph_name}", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_session_messages(
    request: Request,
    graph_name: str,
    session: Session = Depends(get_current_session),
):
    """Get all messages for a session from a specific graph.

    Args:
        request: The FastAPI request object for rate limiting.
        graph_name: The name of the graph to get messages from.
        session: The current session from the auth token.

    Returns:
        ChatResponse: All messages in the session for the specified graph.

    Raises:
        HTTPException: If there's an error retrieving the messages or graph not found.
    """
    try:
        # Validate and normalize graph name
        graph_name = graph_name.lower()
        
        # Get the agent for the specified graph
        agent = GraphRegistry.get_agent(graph_name)
        if agent is None:
            available_graphs = GraphRegistry.list_graphs()
            raise HTTPException(
                status_code=404,
                detail=f"Graph '{graph_name}' not found. Available graphs: {', '.join(available_graphs)}"
            )

        messages = await agent.get_chat_history(session.id)
        logger.info(
            "messages_retrieved",
            session_id=session.id,
            graph_name=graph_name,
            message_count=len(messages),
        )
        return ChatResponse(messages=messages)
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            "get_messages_failed", 
            session_id=session.id, 
            graph_name=graph_name,
            error=str(e), 
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/messages/{graph_name}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def clear_chat_history(
    request: Request,
    graph_name: str,
    session: Session = Depends(get_current_session),
):
    """Clear all messages for a session from a specific graph.

    Args:
        request: The FastAPI request object for rate limiting.
        graph_name: The name of the graph to clear messages from.
        session: The current session from the auth token.

    Returns:
        dict: A message indicating the chat history was cleared.

    Raises:
        HTTPException: If there's an error clearing the history or graph not found.
    """
    try:
        # Validate and normalize graph name
        graph_name = graph_name.lower()
        
        # Get the agent for the specified graph
        agent = GraphRegistry.get_agent(graph_name)
        if agent is None:
            available_graphs = GraphRegistry.list_graphs()
            raise HTTPException(
                status_code=404,
                detail=f"Graph '{graph_name}' not found. Available graphs: {', '.join(available_graphs)}"
            )

        await agent.clear_chat_history(session.id)
        logger.info(
            "chat_history_cleared",
            session_id=session.id,
            graph_name=graph_name,
        )
        return {"message": f"Chat history cleared successfully for graph '{graph_name}'"}
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            "clear_chat_history_failed", 
            session_id=session.id, 
            graph_name=graph_name,
            error=str(e), 
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))
