class AppError(Exception):
    """Base application exception."""


class ConfigError(AppError):
    """Raised when required application configuration is invalid."""


class ValidationError(AppError):
    """Raised when user input does not pass validation."""


class OllamaError(AppError):
    """Base exception for Ollama-related failures."""


class OllamaUnavailableError(OllamaError):
    """Raised when Ollama cannot be reached."""


class ModelNotFoundError(OllamaError):
    """Raised when the configured model is missing in Ollama."""


class OllamaTimeoutError(OllamaError):
    """Raised when Ollama response exceeds timeout."""


class EmptyModelResponseError(OllamaError):
    """Raised when Ollama returns an empty response."""


class InvalidOllamaResponseError(OllamaError):
    """Raised when Ollama returns an unexpected payload."""

