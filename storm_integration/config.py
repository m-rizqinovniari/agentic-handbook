"""STORM configuration for Azure OpenAI."""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def setup_storm_environment() -> None:
    """
    Setup environment variables for STORM to use Azure OpenAI.
    
    This function configures the environment so that STORM's
    knowledge_storm package can use Azure OpenAI instead of regular OpenAI.
    """
    # Get Azure OpenAI configuration from .env
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    if not azure_endpoint or not azure_api_key or not deployment_name:
        raise ValueError(
            "Azure OpenAI configuration missing. Please check your .env file."
        )
    
    # Set environment variables for STORM
    # STORM uses these environment variables for configuration
    os.environ["OPENAI_API_TYPE"] = "azure"
    os.environ["AZURE_API_BASE"] = azure_endpoint
    os.environ["AZURE_API_VERSION"] = azure_api_version
    os.environ["OPENAI_API_KEY"] = azure_api_key
    os.environ["OPENAI_API_MODEL"] = deployment_name
    
    # Encoder configuration (for embeddings)
    encoder_type = os.getenv("ENCODER_API_TYPE", "azure")
    os.environ["ENCODER_API_TYPE"] = encoder_type
    
    # Bing Search API key for retrieval
    bing_key = os.getenv("BING_SEARCH_API_KEY")
    if bing_key:
        os.environ["BING_SEARCH_API_KEY"] = bing_key


def get_storm_lm_config() -> Dict[str, Any]:
    """
    Get language model configuration for STORM.
    
    Returns:
        Dictionary with LM configuration
    """
    setup_storm_environment()
    
    return {
        "provider": "azure",
        "model": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    }

