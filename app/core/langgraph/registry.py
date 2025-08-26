"""Graph registry for managing multiple LangGraph workflows by name."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

from app.core.langgraph.graphs.base_graph import BaseGraph
from app.core.langgraph.graphs.chatbot_graph import ChatbotGraph
from app.core.logging import logger


class GraphRegistry:
    """Registry for managing different graph types by name."""
    
    _graphs: Dict[str, Type[BaseGraph]] = {}
    _instances: Dict[str, BaseGraph] = {}
    
    @classmethod
    def register(cls, name: str, graph_class: Type[BaseGraph]) -> None:
        """Register a graph type with a unique name.
        
        Args:
            name: Unique identifier for the graph type
            graph_class: The graph class that implements this graph
        """
        if name in cls._graphs:
            logger.warning(f"Graph '{name}' is already registered, overwriting")
        
        cls._graphs[name] = graph_class
        logger.info(f"Graph '{name}' registered successfully")
    
    @classmethod
    def get_graph(cls, name: str) -> Optional[BaseGraph]:
        """Get a graph instance by graph name.
        
        Args:
            name: The name of the graph to get
            
        Returns:
            BaseGraph instance or None if not found
        """
        if name not in cls._graphs:
            logger.error(f"Graph '{name}' not found in registry")
            return None
        
        # Use singleton pattern for graphs to reuse compiled graphs
        if name not in cls._instances:
            graph_class = cls._graphs[name]
            cls._instances[name] = graph_class()
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
GraphRegistry.register("chatbot", ChatbotGraph)

logger.info("Graph registry initialized with default graphs")
