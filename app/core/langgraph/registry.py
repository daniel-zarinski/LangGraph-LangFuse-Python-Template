"""Graph registry for managing multiple LangGraph workflows by name."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

from app.core.langgraph.agents.base_agent import BaseAgent
from app.core.langgraph.agents.chatbot_agent import ChatbotAgent
from app.core.logging import logger


class GraphRegistry:
    """Registry for managing different graph types by name."""
    
    _graphs: Dict[str, Type[BaseAgent]] = {}
    _instances: Dict[str, BaseAgent] = {}
    
    @classmethod
    def register(cls, name: str, agent_class: Type[BaseAgent]) -> None:
        """Register a graph type with a unique name.
        
        Args:
            name: Unique identifier for the graph type
            agent_class: The agent class that implements this graph
        """
        if name in cls._graphs:
            logger.warning(f"Graph '{name}' is already registered, overwriting")
        
        cls._graphs[name] = agent_class
        logger.info(f"Graph '{name}' registered successfully")
    
    @classmethod
    def get_agent(cls, name: str) -> Optional[BaseAgent]:
        """Get an agent instance by graph name.
        
        Args:
            name: The name of the graph to get
            
        Returns:
            BaseAgent instance or None if not found
        """
        if name not in cls._graphs:
            logger.error(f"Graph '{name}' not found in registry")
            return None
        
        # Use singleton pattern for agents to reuse compiled graphs
        if name not in cls._instances:
            agent_class = cls._graphs[name]
            cls._instances[name] = agent_class()
            logger.info(f"Created new instance of graph '{name}'")
        
        return cls._instances[name]
    
    @classmethod
    def list_graphs(cls) -> list[str]:
        """List all registered graph names.
        
        Returns:
            List of registered graph names
        """
        return list(cls._graphs.keys())
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a graph name is registered.
        
        Args:
            name: The graph name to check
            
        Returns:
            True if registered, False otherwise
        """
        return name in cls._graphs


# Register default graphs
GraphRegistry.register("chatbot", ChatbotAgent)

logger.info("Graph registry initialized with default graphs")
