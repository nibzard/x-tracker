# ABOUTME: Centralized configuration management for X-Tracker
# ABOUTME: Handles environment variables, settings validation, and default values

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration management"""
    
    def __init__(self):
        self._config_cache: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """Load all configuration from environment variables"""
        # API Configuration
        self.bearer_token = os.getenv('BEARER_TOKEN')
        self.api_key = os.getenv('API_KEY')
        self.api_key_secret = os.getenv('API_KEY_SECRET')
        self.access_token = os.getenv('ACCESS_TOKEN')
        self.access_token_secret = os.getenv('ACCESS_TOKEN_SECRET')
        
        # Target User Configuration
        self.target_user_id = os.getenv('TARGET_USER_ID')
        self.target_username = os.getenv('TARGET_USERNAME')
        
        # Database Configuration
        self.database_path = os.getenv('DATABASE_PATH', 'data/x_tracker.db')
        
        # Rate Limiting
        self.max_requests_per_window = int(os.getenv('MAX_REQUESTS_PER_WINDOW', '15'))
        self.rate_limit_window_minutes = int(os.getenv('RATE_LIMIT_WINDOW_MINUTES', '15'))
        
        # Cleaner Configuration
        self.inactive_threshold_days = int(os.getenv('INACTIVE_THRESHOLD_DAYS', '180'))
        self.max_unfollows_per_run = int(os.getenv('MAX_UNFOLLOWS_PER_RUN', '50'))
        self.max_unfollows_per_day = int(os.getenv('MAX_UNFOLLOWS_PER_DAY', '100'))
        self.protect_verified = os.getenv('PROTECT_VERIFIED', 'true').lower() == 'true'
        self.protect_high_followers = os.getenv('PROTECT_HIGH_FOLLOWERS', 'true').lower() == 'true'
        self.min_follower_threshold = int(os.getenv('MIN_FOLLOWER_THRESHOLD', '10000'))
        
        # UI Configuration
        self.ui_host = os.getenv('UI_HOST', '127.0.0.1')
        self.ui_port = int(os.getenv('UI_PORT', '7860'))
        
        # Paths
        self.data_dir = Path(os.getenv('DATA_DIR', 'data'))
        self.reports_dir = Path(os.getenv('REPORTS_DIR', 'reports'))
        self.logs_dir = Path(os.getenv('LOGS_DIR', 'logs'))
        
        # Create directories if they don't exist
        for dir_path in [self.data_dir, self.reports_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def validate_api_credentials(self) -> bool:
        """Validate that required API credentials are present"""
        required_fields = ['bearer_token', 'api_key', 'api_key_secret']
        return all(getattr(self, field) for field in required_fields)
    
    def validate_oauth_credentials(self) -> bool:
        """Validate OAuth credentials for enhanced features"""
        oauth_fields = ['access_token', 'access_token_secret']
        return all(getattr(self, field) for field in oauth_fields)
    
    def get_x_api_headers(self, include_oauth: bool = False) -> Dict[str, str]:
        """Get headers for X API requests"""
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'User-Agent': 'X-Growth-Command-Center-v2.0',
            'Content-Type': 'application/json'
        }
        
        if include_oauth and self.validate_oauth_credentials():
            # OAuth headers would be handled by the OAuth library
            pass
        
        return headers
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        return f'sqlite:///{self.database_path}'
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'production'
    
    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled"""
        return os.getenv('DEBUG', 'false').lower() == 'true'

# Global config instance
config = Config()