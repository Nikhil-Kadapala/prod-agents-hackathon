"""Configuration management for the application."""

import os
from typing import Optional
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables and config files."""
    
    # Application
    app_name: str = Field(default="Learning Resource Curator")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # Anthropic API (Claude Agent SDK)
    anthropic_api_key: str = Field(default="")
    claude_model: str = Field(default="claude-3-5-sonnet-20241022")
    claude_max_tokens: int = Field(default=4000)
    claude_temperature: float = Field(default=0.2)
    
    # Agent SDK Settings
    agent_permission_mode: str = Field(default="acceptEdits")  # acceptEdits, ask, reject
    agent_cwd: Optional[str] = Field(default=None)  # Working directory for agents
    agent_system_prompt: str = Field(default="You are an expert autonomous AI agent.")
    
    # Redis
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = Field(default=None)
    cache_ttl_days: int = Field(default=7)
    semantic_similarity_threshold: float = Field(default=0.85)
    
    # Parallel Search API
    parallel_api_key: str = Field(default="")
    parallel_api_endpoint: str = Field(default="https://api.parallel.ai")
    parallel_api_timeout: int = Field(default=60)  # HTTP request timeout for Search API
    
    # Skyflow (Phase 3)
    skyflow_vault_id: str = Field(default="")
    skyflow_vault_url: str = Field(default="")
    skyflow_credentials_path: str = Field(default="./config/skyflow_credentials.json")
    
    # NotebookLM (Phase 3)
    notebooklm_api_key: str = Field(default="")
    notebooklm_api_endpoint: str = Field(
        default="https://notebooklm.google.com/api/v1"
    )
    
    # Agent Configuration
    max_concurrent_searches: int = Field(default=10)
    resource_search_timeout: int = Field(default=30)
    min_quality_resources: int = Field(default=3)
    relevance_threshold: float = Field(default=0.7)
    
    # API Server
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_reload: bool = Field(default=True)
    
    # Feature Flags
    enable_cache: bool = Field(default=True)
    enable_judge: bool = Field(default=False)  # TODO: Fix Claude Agent SDK send_message() API issue
    enable_pii_masking: bool = Field(default=False)
    enable_notebooklm: bool = Field(default=False)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields (like old AWS credentials)


# Global settings instance
_settings: Optional[Settings] = None


def load_yaml_config(config_file: str) -> dict:
    """Load configuration from YAML file.
    
    Args:
        config_file: Path to YAML config file
        
    Returns:
        Configuration dictionary
    """
    config_path = Path(config_file)
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config or {}


def get_config(config_file: Optional[str] = None) -> Settings:
    """Get application configuration.
    
    Args:
        config_file: Optional path to YAML config file
        
    Returns:
        Settings instance
    """
    global _settings
    
    if _settings is None:
        # Load from environment variables
        _settings = Settings()
        
        # Override with YAML config if provided
        if config_file:
            yaml_config = load_yaml_config(config_file)
            
            # Flatten nested config
            flat_config = _flatten_dict(yaml_config)
            
            # Update settings
            for key, value in flat_config.items():
                if hasattr(_settings, key):
                    setattr(_settings, key, value)
        
        # Auto-detect environment
        elif os.getenv("ENV"):
            env = os.getenv("ENV")
            config_path = f"config/{env}.yaml"
            if Path(config_path).exists():
                return get_config(config_path)
    
    return _settings


def _flatten_dict(d: dict, parent_key: str = '', sep: str = '_') -> dict:
    """Flatten nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator character
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def reload_config():
    """Reload configuration from environment and files."""
    global _settings
    _settings = None
    return get_config()

