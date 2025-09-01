"""Configuration management for Journal LLM application."""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from modules.exceptions import InvalidAPIKeyError, JournalLLMError
from modules.logger import get_logger

logger = get_logger(__name__)


class ConfigurationError(JournalLLMError):
    """Raised when configuration is invalid or incomplete."""
    pass


@dataclass
class VideoConfig:
    """Configuration for video processing."""
    video_output_dir: str = "downloads"
    audio_output_dir: str = "audio"
    youtube_format: str = "best[height<=729]/best"
    quiet_mode: bool = True
    delete_files_after: bool = True
    
    def __post_init__(self):
        """Create output directories if they don't exist."""
        Path(self.video_output_dir).mkdir(exist_ok=True)
        Path(self.audio_output_dir).mkdir(exist_ok=True)


@dataclass
class AIConfig:
    """Configuration for AI models."""
    gemini_api_key: str
    whisper_model: str = "base"
    
    def validate(self):
        """Validate AI configuration."""
        if not self.gemini_api_key:
            raise InvalidAPIKeyError("GEMINI_API_KEY is required but not set")
        
        if not self.gemini_api_key.strip():
            raise InvalidAPIKeyError("GEMINI_API_KEY cannot be empty")
        
        # TODO(human): Add validation for API key format if needed
        # Consider checking key length, prefix patterns, etc.


@dataclass
class NotionConfig:
    """Configuration for Notion integration."""
    api_key: Optional[str] = None
    database_id: Optional[str] = None
    enabled: bool = field(init=False)
    
    def __post_init__(self):
        """Determine if Notion is enabled based on credentials."""
        self.enabled = bool(self.api_key and self.database_id)
        
        if self.enabled:
            logger.info("Notion integration enabled")
        else:
            logger.info("Notion integration disabled (missing credentials)")
    
    def validate(self):
        """Validate Notion configuration if enabled."""
        if not self.enabled:
            return
        
        if not self.api_key or not self.api_key.strip():
            raise InvalidAPIKeyError("NOTION_API_KEY is set but empty")
        
        if not self.database_id or not self.database_id.strip():
            raise ConfigurationError("NOTION_DATABASE_ID is set but empty")


@dataclass
class UIConfig:
    """Configuration for user interface."""
    spinner_style: str = "arrow3"
    spinner_color: str = "red"
    text_color: str = "bold blue"
    log_level: str = "WARNING"


@dataclass
class Config:
    """Central configuration for Journal LLM application."""
    video: VideoConfig
    ai: AIConfig
    notion: NotionConfig
    ui: UIConfig
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables.
        
        Returns:
            Config: Validated configuration object
            
        Raises:
            ConfigurationError: If required configuration is missing or invalid
        """
        load_dotenv()
        
        # Load delete files setting
        delete_files = bool(os.getenv("DELETE_UNNEEDED_FILES", "1") == "1")
        
        # Create sub-configurations
        video_config = VideoConfig(delete_files_after=delete_files)
        
        ai_config = AIConfig(
            gemini_api_key=os.getenv("GEMINI_API_KEY", "")
        )
        
        notion_config = NotionConfig(
            api_key=os.getenv("NOTION_API_KEY"),
            database_id=os.getenv("NOTION_DATABASE_ID")
        )
        
        ui_config = UIConfig()
        
        # Create main config
        config = cls(
            video=video_config,
            ai=ai_config,
            notion=notion_config,
            ui=ui_config
        )
        
        # Validate all configurations
        config.validate()
        
        return config
    
    def validate(self):
        """Validate all configuration sections.
        
        Raises:
            ConfigurationError: If any configuration is invalid
        """
        try:
            self.ai.validate()
            self.notion.validate()
            logger.info("Configuration validated successfully")
        except JournalLLMError:
            raise
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {str(e)}")
    
    def summary(self) -> dict:
        """Get a summary of the configuration for logging.
        
        Returns:
            dict: Configuration summary (with sensitive data masked)
        """
        return {
            "video": {
                "output_dirs": [self.video.video_output_dir, self.video.audio_output_dir],
                "delete_after": self.video.delete_files_after,
                "quiet_mode": self.video.quiet_mode
            },
            "ai": {
                "gemini_key_set": bool(self.ai.gemini_api_key),
                "whisper_model": self.ai.whisper_model
            },
            "notion": {
                "enabled": self.notion.enabled,
                "credentials_set": self.notion.enabled
            },
            "ui": {
                "spinner": f"{self.ui.spinner_style} ({self.ui.spinner_color})",
                "log_level": self.ui.log_level
            }
        }