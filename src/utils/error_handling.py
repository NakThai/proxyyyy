"""Error handling utilities for the application."""
import logging
from typing import Callable, Any
from functools import wraps

def with_error_handling(logger: logging.Logger):
    """
    Decorator for handling errors in bot operations.
    
    Args:
        logger: Logger instance to use for error reporting
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator

class BotError(Exception):
    """Base exception for bot-related errors."""
    pass

class NavigationError(BotError):
    """Raised when navigation fails."""
    pass

class SearchError(BotError):
    """Raised when search operation fails."""
    pass