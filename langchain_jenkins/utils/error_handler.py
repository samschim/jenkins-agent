"""Error handling utilities."""
import sys
import traceback
import logging
from typing import Dict, Any, Optional, Type, Callable
from functools import wraps
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.traceback import Traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('jenkins_agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize rich console
console = Console()

class ErrorHandler:
    """Error handler for Jenkins Agent."""
    
    def __init__(self):
        """Initialize error handler."""
        self.error_handlers: Dict[Type[Exception], Callable] = {}
        self.register_default_handlers()
    
    def register_default_handlers(self):
        """Register default error handlers."""
        # HTTP errors
        self.register_handler(
            httpx.HTTPError,
            self._handle_http_error
        )
        # Authentication errors
        self.register_handler(
            httpx.HTTPStatusError,
            self._handle_auth_error,
            lambda e: e.response.status_code in [401, 403]
        )
        # Connection errors
        self.register_handler(
            httpx.ConnectError,
            self._handle_connection_error
        )
        # Timeout errors
        self.register_handler(
            httpx.TimeoutException,
            self._handle_timeout_error
        )
    
    def register_handler(
        self,
        error_type: Type[Exception],
        handler: Callable,
        condition: Optional[Callable[[Exception], bool]] = None
    ):
        """Register an error handler.
        
        Args:
            error_type: Type of exception to handle
            handler: Handler function
            condition: Optional condition to check
        """
        self.error_handlers[error_type] = (handler, condition)
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle an error.
        
        Args:
            error: Exception to handle
            context: Optional context information
            
        Returns:
            Error response
        """
        context = context or {}
        logger.error(
            "Error occurred",
            exc_info=error,
            extra=context
        )
        
        # Find matching handler
        for error_type, (handler, condition) in self.error_handlers.items():
            if isinstance(error, error_type):
                if condition is None or condition(error):
                    return handler(error, context)
        
        # Default error handling
        return self._handle_default_error(error, context)
    
    def _handle_http_error(
        self,
        error: httpx.HTTPError,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle HTTP errors.
        
        Args:
            error: HTTP error
            context: Error context
            
        Returns:
            Error response
        """
        return {
            "status": "error",
            "error_type": "http_error",
            "message": str(error),
            "status_code": getattr(error.response, "status_code", None),
            "context": context
        }
    
    def _handle_auth_error(
        self,
        error: httpx.HTTPStatusError,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle authentication errors.
        
        Args:
            error: Authentication error
            context: Error context
            
        Returns:
            Error response
        """
        return {
            "status": "error",
            "error_type": "auth_error",
            "message": "Authentication failed",
            "status_code": error.response.status_code,
            "context": context
        }
    
    def _handle_connection_error(
        self,
        error: httpx.ConnectError,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle connection errors.
        
        Args:
            error: Connection error
            context: Error context
            
        Returns:
            Error response
        """
        return {
            "status": "error",
            "error_type": "connection_error",
            "message": "Failed to connect to Jenkins server",
            "context": context
        }
    
    def _handle_timeout_error(
        self,
        error: httpx.TimeoutException,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle timeout errors.
        
        Args:
            error: Timeout error
            context: Error context
            
        Returns:
            Error response
        """
        return {
            "status": "error",
            "error_type": "timeout_error",
            "message": "Request timed out",
            "context": context
        }
    
    def _handle_default_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle unknown errors.
        
        Args:
            error: Unknown error
            context: Error context
            
        Returns:
            Error response
        """
        return {
            "status": "error",
            "error_type": "unknown_error",
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context
        }
    
    def print_error(self, error_response: Dict[str, Any]):
        """Print error information using rich.
        
        Args:
            error_response: Error response from handle_error
        """
        error_type = error_response["error_type"]
        message = error_response["message"]
        
        if "traceback" in error_response:
            console.print(
                Panel(
                    Traceback.from_exception(
                        type(Exception(message)),
                        Exception(message),
                        traceback.extract_stack()
                    ),
                    title=f"[red]{error_type.replace('_', ' ').title()}[/red]",
                    border_style="red"
                )
            )
        else:
            console.print(
                Panel(
                    f"[red]{message}[/red]",
                    title=f"[red]{error_type.replace('_', ' ').title()}[/red]",
                    border_style="red"
                )
            )

def handle_errors(context: Optional[Dict[str, Any]] = None):
    """Decorator for error handling.
    
    Args:
        context: Optional context information
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_handler = ErrorHandler()
                error_response = error_handler.handle_error(e, context)
                error_handler.print_error(error_response)
                return error_response
        return wrapper
    return decorator

# Global error handler instance
error_handler = ErrorHandler()