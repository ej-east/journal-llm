"""Custom exceptions for Journal LLM application."""

class JournalLLMError(Exception):
    """Base exception for all Journal LLM errors."""
    pass


class VideoProcessingError(JournalLLMError):
    """Base exception for video processing related errors."""
    pass


class VideoDownloadError(VideoProcessingError):
    """Raised when video download fails."""
    pass


class InvalidURLError(VideoProcessingError):
    """Raised when provided URL is invalid or unreachable."""
    pass


class AudioExtractionError(VideoProcessingError):
    """Raised when audio extraction from video fails."""
    pass


class FileNotFoundError(VideoProcessingError):
    """Raised when required file doesn't exist."""
    pass


class AIProcessingError(JournalLLMError):
    """Base exception for AI processing related errors."""
    pass


class TranscriptionError(AIProcessingError):
    """Raised when audio transcription fails."""
    pass


class SummarizationError(AIProcessingError):
    """Raised when text summarization fails."""
    pass


class InvalidAPIKeyError(AIProcessingError):
    """Raised when API key is invalid or missing."""
    pass


class ModelLoadError(AIProcessingError):
    """Raised when AI model fails to load."""
    pass


class NotionIntegrationError(JournalLLMError):
    """Base exception for Notion integration errors."""
    pass


class NotionAPIError(NotionIntegrationError):
    """Raised when Notion API call fails."""
    pass


class NotionDatabaseError(NotionIntegrationError):
    """Raised when database operations fail."""
    pass