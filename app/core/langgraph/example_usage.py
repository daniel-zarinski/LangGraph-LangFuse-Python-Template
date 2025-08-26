"""Example usage of the new modular LangGraph structure.

This file demonstrates how to use the new modular structure for creating
different types of agents and graphs.
"""

from typing import Optional

from app.core.langgraph.agents.chatbot_agent import ChatbotAgent
from app.core.langgraph.builders.chatbot_graph_builder import ChatbotGraphBuilder
from app.core.langgraph.llm import GoogleModel, LLMManager, OpenAIModel
from app.schemas import Message


async def example_chatbot_usage():
    """Example of how to use the new ChatbotAgent."""
    # Option 1: Simple usage with default models (GPT-4o-mini + Gemini Flash)
    chatbot_agent = ChatbotAgent()
    
    # Option 2: Specify Google model only
    chatbot_agent_google = ChatbotAgent(google_model=GoogleModel.GEMINI_PRO)
    
    # Option 3: Specify OpenAI model only
    chatbot_agent_openai = ChatbotAgent(openai_model=OpenAIModel.GPT_4O)
    
    # Option 4: Specify both models
    chatbot_agent_both = ChatbotAgent(
        openai_model=OpenAIModel.GPT_4_TURBO,
        google_model=GoogleModel.GEMINI_PRO
    )
    
    # Option 5: Create your own LLMManager with specific models
    llm_manager = LLMManager(
        openai_model=OpenAIModel.GPT_4O_MINI,
        google_model=GoogleModel.GEMINI_FLASH_LITE
    )
    chatbot_agent_custom = ChatbotAgent(llm_manager)
    
    # Use the agent
    messages = [Message(role="user", content="Hello, how are you?")]
    session_id = "example-session-123"
    
    # Get a regular response
    response = await chatbot_agent.get_response(messages, session_id)
    print(f"Response: {response}")
    
    # Get a streaming response
    async for token in chatbot_agent.get_stream_response(messages, session_id):
        print(token, end="", flush=True)
    
    # Get chat history
    history = await chatbot_agent.get_chat_history(session_id)
    print(f"History: {history}")
    
    # Clean up
    await chatbot_agent.cleanup()
    await chatbot_agent_google.cleanup()
    await chatbot_agent_openai.cleanup()
    await chatbot_agent_both.cleanup()
    await chatbot_agent_custom.cleanup()


async def example_custom_graph_usage():
    """Example of how to create a custom graph using the modular structure."""
    # Create your own LLM manager with specific models
    llm_manager = LLMManager(
        openai_model=OpenAIModel.GPT_4_TURBO,
        google_model=GoogleModel.GEMINI_PRO
    )
    
    # Create a custom graph builder
    graph_builder = ChatbotGraphBuilder(llm_manager)
    
    # Build the graph
    graph = await graph_builder.build_graph()
    
    # Use the graph directly if needed
    if graph:
        # Custom graph usage here
        pass
    
    # Clean up
    await graph_builder.cleanup()


async def example_multiple_agents():
    """Example of how to share resources between multiple agents."""
    # Create a shared LLM manager with high-performance models
    shared_llm_manager = LLMManager(
        openai_model=OpenAIModel.GPT_4O,
        google_model=GoogleModel.GEMINI_PRO
    )
    
    # Create multiple agents sharing the same LLM manager
    chatbot_agent_1 = ChatbotAgent(shared_llm_manager)
    chatbot_agent_2 = ChatbotAgent(shared_llm_manager)
    
    # Both agents will share the same LLM instances and database connections
    # through their graph builders inheriting from BaseGraphBuilder
    
    # Use agents independently
    messages = [Message(role="user", content="Hello")]
    
    await chatbot_agent_1.get_response(messages, "session-1")
    await chatbot_agent_2.get_response(messages, "session-2")
    
    # Clean up
    await chatbot_agent_1.cleanup()
    await chatbot_agent_2.cleanup()


async def example_model_comparison():
    """Example comparing different models for different use cases."""
    # Fast, cost-effective setup for development/testing
    dev_agent = ChatbotAgent(
        openai_model=OpenAIModel.GPT_4O_MINI,
        google_model=GoogleModel.GEMINI_FLASH_LITE
    )
    
    # High-quality setup for productionx
    prod_agent = ChatbotAgent(
        openai_model=OpenAIModel.GPT_4_TURBO,
        google_model=GoogleModel.GEMINI_PRO
    )
    
    # Balanced setup for most use cases
    balanced_agent = ChatbotAgent(
        openai_model=OpenAIModel.GPT_4O,
        google_model=GoogleModel.GEMINI_FLASH
    )
    
    messages = [Message(role="user", content="Explain machine learning")]
    
    # Compare responses from different model configurations
    dev_response = await dev_agent.get_response(messages, "dev-session")
    prod_response = await prod_agent.get_response(messages, "prod-session")
    balanced_response = await balanced_agent.get_response(messages, "balanced-session")
    
    print(f"Dev response (fast/cheap): {dev_response}")
    print(f"Prod response (high-quality): {prod_response}")
    print(f"Balanced response: {balanced_response}")
    
    # Clean up
    await dev_agent.cleanup()
    await prod_agent.cleanup()
    await balanced_agent.cleanup()
