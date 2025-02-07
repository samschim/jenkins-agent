"""Error handling utilities for Jenkins operations."""
from typing import Dict, Any, Optional, Type
from functools import wraps
import httpx
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JenkinsError(Exception):
    """Base class for Jenkins-related errors."""
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize error with message and optional details.
        
        Args:
            message: Error message
            status_code: HTTP status code (optional)
            details: Additional error details (optional)
        """
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}

class JenkinsAPIError(JenkinsError):
    """Error for Jenkins API communication issues."""
    pass

class JenkinsAuthError(JenkinsError):
    """Error for authentication/authorization issues."""
    pass

class JenkinsNotFoundError(JenkinsError):
    """Error for resource not found issues."""
    pass

class JenkinsConfigError(JenkinsError):
    """Error for configuration issues."""
    pass

def handle_jenkins_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Handle Jenkins-related errors and return structured error response.
    
    Args:
        error: The exception to handle
        context: Additional context about the error
        
    Returns:
        Structured error response
    """
    context = context or {}
    error_response = {
        "status": "error",
        "error_type": error.__class__.__name__,
        "message": str(error),
        "context": context
    }
    
    if isinstance(error, httpx.HTTPError):
        if error.response.status_code == 401:
            error_response.update({
                "error_type": "AuthenticationError",
                "status_code": 401,
                "details": "Invalid credentials or token"
            })
        elif error.response.status_code == 403:
            error_response.update({
                "error_type": "AuthorizationError",
                "status_code": 403,
                "details": "Insufficient permissions"
            })
        elif error.response.status_code == 404:
            error_response.update({
                "error_type": "NotFoundError",
                "status_code": 404,
                "details": "Resource not found"
            })
        else:
            error_response.update({
                "status_code": error.response.status_code,
                "details": error.response.text
            })
    
    elif isinstance(error, JenkinsError):
        error_response.update({
            "status_code": error.status_code,
            "details": error.details
        })
    
    # Log the error
    logger.error(
        "Jenkins error: %s",
        error_response,
        exc_info=True
    )
    
    return error_response

def error_handler(func):
    """Decorator for handling errors in Jenkins operations.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function with error handling
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            context = {
                "function": func.__name__,
                "args": str(args),
                "kwargs": str(kwargs)
            }
            return handle_jenkins_error(e, context)
    return wrapper

def validate_response(response: httpx.Response) -> None:
    """Validate Jenkins API response and raise appropriate errors.
    
    Args:
        response: HTTP response to validate
        
    Raises:
        JenkinsAuthError: For authentication/authorization errors
        JenkinsNotFoundError: For resource not found errors
        JenkinsAPIError: For other API errors
    """
    if response.status_code == 401:
        raise JenkinsAuthError(
            "Authentication failed",
            status_code=401,
            details={"response": response.text}
        )
    elif response.status_code == 403:
        raise JenkinsAuthError(
            "Insufficient permissions",
            status_code=403,
            details={"response": response.text}
        )
    elif response.status_code == 404:
        raise JenkinsNotFoundError(
            "Resource not found",
            status_code=404,
            details={"response": response.text}
        )
    elif response.status_code >= 400:
        raise JenkinsAPIError(
            f"API request failed: {response.text}",
            status_code=response.status_code,
            details={"response": response.text}
        )

def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (JenkinsAPIError,)
):
    """Decorator for retrying operations on specific errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exceptions to retry on
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            "Attempt %d/%d failed, retrying in %.1f seconds...",
                            attempt + 1,
                            max_retries,
                            delay
                        )
                        await asyncio.sleep(delay)
                    continue
            
            # If we get here, all retries failed
            context = {
                "function": func.__name__,
                "max_retries": max_retries,
                "attempts": max_retries
            }
            return handle_jenkins_error(last_error, context)
        return wrapper
    return decorator