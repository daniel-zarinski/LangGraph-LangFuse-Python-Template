"""Example usage of the new modular LangGraph structure.

This file demonstrates how to use the new modular structure for creating
different types of graphs.
"""

from app.core.langgraph.builders.chatbot_graph_builder import ChatbotGraphBuilder
from app.core.langgraph.graphs.chatbot_graph import ChatbotGraph
from app.core.langgraph.llm import GoogleModel, LLMManager, OpenAIModel
from app.schemas import Message


async def example_chatbot_usage():
    """Example of how to use the new ChatbotGraph."""
    # Option 1: Simple usage with default models (GPT-4o-mini + Gemini Flash)
    chatbot_graph = ChatbotGraph()
    
    # Option 2: Specify Google model only
    chatbot_graph_google = ChatbotGraph(google_model=GoogleModel.GEMINI_PRO)
    
    # Option 3: Specify OpenAI model only
    chatbot_graph_openai = ChatbotGraph(openai_model=OpenAIModel.GPT_4O)
    
    # Option 4: Specify both models
    chatbot_graph_both = ChatbotGraph(
        openai_model=OpenAIModel.GPT_4_TURBO,
        google_model=GoogleModel.GEMINI_PRO
    )
    
    # Option 5: Create your own LLMManager with specific models
    llm_manager = LLMManager(
        openai_model=OpenAIModel.GPT_4O_MINI,
        google_model=GoogleModel.GEMINI_FLASH_LITE
    )
    chatbot_graph_custom = ChatbotGraph(llm_manager)
    
    # Use the graph
    messages = [Message(role="user", content="Hello, how are you?")]
    session_id = "example-session-123"
    
    # Get a regular response
    response = await chatbot_graph.get_response(messages, session_id)
    print(f"Response: {response}")
    
    # Get a streaming response
    async for token in chatbot_graph.get_stream_response(messages, session_id):
        print(token, end="", flush=True)
    
    # Get chat history
    history = await chatbot_graph.get_chat_history(session_id)
    print(f"History: {history}")
    
    # Clean up
    await chatbot_graph.cleanup()
    await chatbot_graph_google.cleanup()
    await chatbot_graph_openai.cleanup()
    await chatbot_graph_both.cleanup()
    await chatbot_graph_custom.cleanup()


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


async def example_multiple_graphs():
    """Example of how to share resources between multiple graphs."""
    # Create a shared LLM manager with high-performance models
    shared_llm_manager = LLMManager(
        openai_model=OpenAIModel.GPT_4O,
        google_model=GoogleModel.GEMINI_PRO
    )
    
    # Create multiple graphs sharing the same LLM manager
    chatbot_graph_1 = ChatbotGraph(shared_llm_manager)
    chatbot_graph_2 = ChatbotGraph(shared_llm_manager)
    
    # Both graphs will share the same LLM instances and database connections
    # through their graph builders inheriting from BaseGraphBuilder
    
    # Use graphs independently
    messages = [Message(role="user", content="Hello")]
    
    await chatbot_graph_1.get_response(messages, "session-1")
    await chatbot_graph_2.get_response(messages, "session-2")
    
    # Clean up
    await chatbot_graph_1.cleanup()
    await chatbot_graph_2.cleanup()


async def example_model_comparison():
    """Example comparing different models for different use cases."""
    # Fast, cost-effective setup for development/testing
    dev_graph = ChatbotGraph(
        openai_model=OpenAIModel.GPT_4O_MINI,
        google_model=GoogleModel.GEMINI_FLASH_LITE
    )
    
    # High-quality setup for productionx
    prod_graph = ChatbotGraph(
        openai_model=OpenAIModel.GPT_4_TURBO,
        google_model=GoogleModel.GEMINI_PRO
    )
    
    # Balanced setup for most use cases
    balanced_graph = ChatbotGraph(
        openai_model=OpenAIModel.GPT_4O,
        google_model=GoogleModel.GEMINI_FLASH
    )
    
    messages = [Message(role="user", content="Explain machine learning")]
    
    # Compare responses from different model configurations
    dev_response = await dev_graph.get_response(messages, "dev-session")
    prod_response = await prod_graph.get_response(messages, "prod-session")
    balanced_response = await balanced_graph.get_response(messages, "balanced-session")
    
    print(f"Dev response (fast/cheap): {dev_response}")
    print(f"Prod response (high-quality): {prod_response}")
    print(f"Balanced response: {balanced_response}")
    
    # Clean up
    await dev_graph.cleanup()
    await prod_graph.cleanup()
    await balanced_graph.cleanup()
