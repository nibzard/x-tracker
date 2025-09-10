# ABOUTME: Custom exceptions for X-Tracker application
# ABOUTME: Domain-specific error handling with proper error codes and messages

from typing import Optional, Dict, Any

class XTrackerError(Exception):
    """Base exception for X-Tracker application"""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}

class APIError(XTrackerError):
    """Base class for API-related errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 endpoint: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.endpoint = endpoint

class AuthenticationError(APIError):
    """Authentication failed with X API"""
    pass

class AuthorizationError(APIError):
    """Authorization failed - insufficient permissions"""
    pass

class RateLimitError(APIError):
    """Rate limit exceeded"""
    
    def __init__(self, message: str, reset_time: Optional[str] = None, 
                 remaining: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.reset_time = reset_time
        self.remaining = remaining

class AccountNotFoundError(APIError):
    """User account not found or inaccessible"""
    pass

class ProtectedAccountError(APIError):
    """Account is protected and cannot be accessed"""
    pass

class DatabaseError(XTrackerError):
    """Database operation failed"""
    
    def __init__(self, message: str, operation: Optional[str] = None, 
                 table: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.operation = operation
        self.table = table

class ConnectionError(DatabaseError):
    """Database connection failed"""
    pass

class MigrationError(DatabaseError):
    """Database migration failed"""
    pass

class ValidationError(XTrackerError):
    """Data validation failed"""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 value: Optional[Any] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.field = field
        self.value = value

class ConfigurationError(XTrackerError):
    """Configuration error"""
    
    def __init__(self, message: str, setting: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.setting = setting

class CleanerError(XTrackerError):
    """Inactive account cleaner error"""
    pass

class WhitelistError(CleanerError):
    """Whitelist operation error"""
    pass

class UnfollowError(CleanerError):
    """Unfollow operation error"""
    
    def __init__(self, message: str, user_id: Optional[str] = None, 
                 username: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.user_id = user_id
        self.username = username

class UIError(XTrackerError):
    """User interface error"""
    pass

class ReportGenerationError(XTrackerError):
    """Report generation error"""
    
    def __init__(self, message: str, report_type: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.report_type = report_type

# Error code mappings for API responses
API_ERROR_MAPPING = {
    400: ValidationError,
    401: AuthenticationError,
    403: AuthorizationError,
    404: AccountNotFoundError,
    429: RateLimitError,
}

def map_api_error(status_code: int, message: str, endpoint: str = None, 
                  response_data: Dict[str, Any] = None) -> APIError:
    """Map HTTP status code to appropriate exception"""
    error_class = API_ERROR_MAPPING.get(status_code, APIError)
    
    # Extract additional info from response
    kwargs = {'status_code': status_code, 'endpoint': endpoint}
    
    if response_data:
        if status_code == 429:  # Rate limit
            kwargs.update({
                'reset_time': response_data.get('reset_time'),
                'remaining': response_data.get('remaining', 0)
            })
    
    return error_class(message, **kwargs)