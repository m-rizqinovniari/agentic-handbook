"""Azure OpenAI configuration and client setup."""

import os
from typing import Optional
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()


def get_azure_openai_client() -> AzureOpenAI:
    """
    Create and return Azure OpenAI client.
    
    Returns:
        Configured AzureOpenAI client
        
    Raises:
        ValueError: If required environment variables are missing
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT is not set in .env file")
    if not api_key:
        raise ValueError("AZURE_OPENAI_API_KEY is not set in .env file")
    
    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version
    )


def get_deployment_name() -> str:
    """
    Get deployment name from environment.
    
    Returns:
        Deployment name
        
    Raises:
        ValueError: If deployment name is not set
    """
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    if not deployment:
        raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME is not set in .env file")
    return deployment

