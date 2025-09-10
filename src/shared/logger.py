# ABOUTME: Centralized logging configuration for X-Tracker
# ABOUTME: Provides structured logging with file and console output

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import os

class XTrackerLogger:
    """Custom logger for X-Tracker with structured output"""
    
    def __init__(self, name: str, log_level: str = "INFO"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console and file handlers"""
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File handler for all logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Formatters
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(console_format)
        file_handler.setFormatter(file_format)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, extra=kwargs)
    
    def api_request(self, endpoint: str, method: str, status_code: int, 
                   rate_limit_remaining: Optional[int] = None):
        """Log API request with rate limit info"""
        message = f"API {method} {endpoint} → {status_code}"
        if rate_limit_remaining is not None:
            message += f" (Rate limit: {rate_limit_remaining})"
        
        if status_code >= 400:
            self.error(message)
        else:
            self.info(message)
    
    def rate_limit_hit(self, endpoint: str, reset_time: Optional[str] = None):
        """Log rate limit hit"""
        message = f"Rate limit hit for {endpoint}"
        if reset_time:
            message += f" - resets at {reset_time}"
        self.warning(message)
    
    def database_operation(self, operation: str, table: str, count: int = 1):
        """Log database operations"""
        self.debug(f"Database {operation}: {table} ({count} records)")
    
    def unfollow_action(self, username: str, reason: str, success: bool):
        """Log unfollow actions"""
        status = "SUCCESS" if success else "FAILED"
        self.info(f"Unfollow {status}: @{username} - {reason}")
    
    def metrics_update(self, followers: int, following: int, change: int = 0):
        """Log metrics updates"""
        change_str = f" ({change:+d})" if change != 0 else ""
        self.info(f"Metrics: {followers:,} followers, {following:,} following{change_str}")

def get_logger(name: str, level: str = None) -> XTrackerLogger:
    """Get logger instance for a module"""
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO')
    return XTrackerLogger(name, level)