"""LLM Manager for handling different LLM providers and configurations."""

from enum import Enum
from typing import Any, Dict, Union, overload

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.core.config import Environment, settings
from app.core.langgraph.tools import tools
from app.core.logging import logger


class OpenAIModel(str, Enum):
    """Available OpenAI models."""
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5 = "gpt-5"

class GoogleModel(str, Enum):
    """Available Google Gemini models."""
    GEMINI_FLASH = "gemini-2.5-flash"
    GEMINI_FLASH_LITE = "gemini-1.5-flash-8b"
    GEMINI_PRO = "gemini-2.5-pro"


class LLMManager:
    """Manages LLM configurations and instances across different providers.
    
    Handles environment-specific settings and provider fallbacks.
    """

    def __init__(self, 
                 openai_model: OpenAIModel = OpenAIModel.GPT_4O_MINI,
                 google_model: GoogleModel = GoogleModel.GEMINI_FLASH):
        """Initialize the LLM manager with specified configurations.
        
        Args:
            openai_model: The OpenAI model to use for this LLM manager instance.
                         Defaults to GPT_4O_MINI.
            google_model: The Google model to use for this LLM manager instance.
                         Defaults to GEMINI_FLASH.
        """
        self._openai_llm = None
        self._google_llm = None
        self._openai_model = openai_model
        self._google_model = google_model
        
        logger.info("llm_manager_initialized", 
                   environment=settings.ENVIRONMENT.value,
                   openai_model=openai_model.value,
                   google_model=google_model.value)

    def _get_model_kwargs(self) -> Dict[str, Any]:
        """Get environment-specific model kwargs.

        Returns:
            Dict[str, Any]: Additional model arguments based on environment
        """
        model_kwargs = {}

        # Development - we can use lower speeds for cost savings
        if settings.ENVIRONMENT == Environment.DEVELOPMENT:
            model_kwargs["top_p"] = 0.8

        # Production - use higher quality settings
        elif settings.ENVIRONMENT == Environment.PRODUCTION:
            model_kwargs["top_p"] = 0.95
            model_kwargs["presence_penalty"] = 0.1
            model_kwargs["frequency_penalty"] = 0.1

        return model_kwargs

    @overload
    def get_llm(self, model: OpenAIModel) -> ChatOpenAI: ...

    @overload
    def get_llm(self, model: GoogleModel) -> ChatGoogleGenerativeAI: ...

    def get_llm(self, model: Union[OpenAIModel, GoogleModel]) -> Union[ChatOpenAI, ChatGoogleGenerativeAI]:
        """Get the configured LLM instance based on the model type.
        
        Args:
            model: The model enum (OpenAIModel or GoogleModel)
            
        Returns:
            The appropriate LLM instance with type safety
        """
        if isinstance(model, OpenAIModel):
            return self._get_openai_llm(model)
        elif isinstance(model, GoogleModel):
            return self._get_google_llm(model)
        else:
            raise ValueError(f"Unsupported model type: {type(model)}")

    def get_openai_llm(self) -> ChatOpenAI:
        """Get the configured OpenAI LLM instance.

        Returns:
            ChatOpenAI: Configured OpenAI LLM with tools bound.
        """
        return self._get_openai_llm(self._openai_model)

    def get_google_llm(self) -> ChatGoogleGenerativeAI:
        """Get the configured Google LLM instance.

        Returns:
            ChatGoogleGenerativeAI: Configured Google LLM with tools bound.
        """
        return self._get_google_llm(self._google_model)

    def _get_openai_llm(self, model: OpenAIModel) -> ChatOpenAI:
        """Get the configured OpenAI LLM instance for a specific model.
        
        Args:
            model: The OpenAI model to use
            
        Returns:
            ChatOpenAI: Configured OpenAI LLM with tools bound.
        """
        if self._openai_llm is None or self._openai_model != model:
            self._openai_model = model
            self._openai_llm = ChatOpenAI(
                model=model.value,
                temperature=settings.DEFAULT_LLM_TEMPERATURE,
                api_key=settings.LLM_API_KEY,
                max_tokens=settings.MAX_TOKENS,
                **self._get_model_kwargs(),
            ).bind_tools(tools)
            
            logger.info("openai_llm_created", model=model.value, environment=settings.ENVIRONMENT.value)
        
        return self._openai_llm

    def _get_google_llm(self, model: GoogleModel) -> ChatGoogleGenerativeAI:
        """Get the configured Google LLM instance for a specific model.
        
        Args:
            model: The Google model to use
            
        Returns:
            ChatGoogleGenerativeAI: Configured Google LLM with tools bound.
        """
        if self._google_llm is None or self._google_model != model:
            self._google_model = model
            self._google_llm = ChatGoogleGenerativeAI(
                model=model.value,
                google_api_key=settings.GOOGLE_API_KEY,
                max_output_tokens=settings.MAX_TOKENS,
                temperature=settings.DEFAULT_LLM_TEMPERATURE,
                **self._get_model_kwargs(),
            ).bind_tools(tools)
            
            logger.info("google_llm_created", model=model.value, environment=settings.ENVIRONMENT.value)
        
        return self._google_llm
