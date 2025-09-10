# ABOUTME: Base X API client with rate limiting and error handling
# ABOUTME: Provides unified interface for all X API interactions with automatic retries

import requests
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps

from ...shared.config import config
from ...shared.logger import get_logger
from ...core.exceptions import (
    APIError, RateLimitError, AuthenticationError, 
    AuthorizationError, AccountNotFoundError, map_api_error
)
from ...core.models import User, Tweet

logger = get_logger(__name__)

def rate_limit_handler(max_retries: int = 3):
    """Decorator to handle rate limiting with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    if attempt == max_retries:
                        raise
                    
                    # Calculate wait time (exponential backoff)
                    base_wait = 60  # 1 minute base
                    wait_time = base_wait * (2 ** attempt)
                    
                    logger.warning(f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(wait_time)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

class XAPIClient:
    """Base client for X API interactions"""
    
    def __init__(self):
        """Initialize API client with configuration"""
        if not config.validate_api_credentials():
            raise AuthenticationError("Missing required API credentials")
        
        self.base_url = "https://api.twitter.com/2"
        self.session = requests.Session()
        self.session.headers.update(config.get_x_api_headers())
        
        # Rate limiting state
        self._rate_limits: Dict[str, Dict] = {}
        
        logger.info("X API client initialized")
    
    def _check_rate_limit(self, endpoint: str) -> bool:
        """Check if endpoint is rate limited"""
        if endpoint not in self._rate_limits:
            return True
        
        limit_info = self._rate_limits[endpoint]
        reset_time = limit_info.get('reset_time')
        remaining = limit_info.get('remaining', 0)
        
        if remaining > 0:
            return True
        
        if reset_time and datetime.now(timezone.utc) > reset_time:
            # Reset time passed, clear rate limit
            del self._rate_limits[endpoint]
            return True
        
        return False
    
    def _update_rate_limit(self, endpoint: str, headers: Dict[str, str]):
        """Update rate limit state from response headers"""
        remaining = headers.get('x-rate-limit-remaining')
        reset_timestamp = headers.get('x-rate-limit-reset')
        limit = headers.get('x-rate-limit-limit')
        
        if remaining is not None:
            self._rate_limits[endpoint] = {
                'remaining': int(remaining),
                'limit': int(limit) if limit else None,
                'reset_time': datetime.fromtimestamp(int(reset_timestamp), timezone.utc) if reset_timestamp else None
            }
    
    @rate_limit_handler(max_retries=3)
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None, timeout: int = 30) -> Dict[str, Any]:
        """Make API request with error handling and rate limiting"""
        
        # Check rate limit
        if not self._check_rate_limit(endpoint):
            reset_time = self._rate_limits[endpoint].get('reset_time')
            raise RateLimitError(
                f"Rate limit exceeded for {endpoint}",
                reset_time=reset_time.isoformat() if reset_time else None
            )
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=timeout
            )
            
            # Update rate limit info
            self._update_rate_limit(endpoint, response.headers)
            
            # Log request
            logger.api_request(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                rate_limit_remaining=response.headers.get('x-rate-limit-remaining')
            )
            
            # Handle successful responses
            if response.status_code == 200:
                return response.json()
            
            # Handle errors
            error_data = {}
            try:
                error_data = response.json()
            except:
                pass
            
            error_message = error_data.get('detail', f'API request failed with status {response.status_code}')
            
            # Map to appropriate exception
            raise map_api_error(
                status_code=response.status_code,
                message=error_message,
                endpoint=endpoint,
                response_data=error_data
            )
            
        except requests.Timeout:
            raise APIError(f"Request timeout for {endpoint}")
        except requests.ConnectionError:
            raise APIError(f"Connection error for {endpoint}")
    
    def get_user_by_id(self, user_id: str, user_fields: Optional[List[str]] = None) -> User:
        """Get user by ID"""
        endpoint = f"/users/{user_id}"
        
        params = {}
        if user_fields:
            params['user.fields'] = ','.join(user_fields)
        else:
            params['user.fields'] = (
                'created_at,description,location,name,pinned_tweet_id,'
                'profile_image_url,protected,public_metrics,url,username,'
                'verified,verified_type'
            )
        
        response = self._make_request('GET', endpoint, params=params)
        user_data = response.get('data', {})
        
        return User.from_api_data(user_data)
    
    def get_user_by_username(self, username: str, user_fields: Optional[List[str]] = None) -> User:
        """Get user by username"""
        endpoint = f"/users/by/username/{username}"
        
        params = {}
        if user_fields:
            params['user.fields'] = ','.join(user_fields)
        else:
            params['user.fields'] = (
                'created_at,description,location,name,pinned_tweet_id,'
                'profile_image_url,protected,public_metrics,url,username,'
                'verified,verified_type'
            )
        
        response = self._make_request('GET', endpoint, params=params)
        user_data = response.get('data', {})
        
        return User.from_api_data(user_data)
    
    def get_me(self) -> User:
        """Get authenticated user's information (requires OAuth)"""
        endpoint = "/users/me"
        
        params = {
            'user.fields': (
                'created_at,description,location,name,pinned_tweet_id,'
                'profile_image_url,protected,public_metrics,url,username,'
                'verified,verified_type'
            )
        }
        
        response = self._make_request('GET', endpoint, params=params)
        user_data = response.get('data', {})
        
        return User.from_api_data(user_data)
    
    def get_user_tweets(self, user_id: str, max_results: int = 10, 
                       tweet_fields: Optional[List[str]] = None) -> List[Tweet]:
        """Get user's recent tweets"""
        endpoint = f"/users/{user_id}/tweets"
        
        params = {
            'max_results': min(max_results, 100),  # API limit is 100
        }
        
        if tweet_fields:
            params['tweet.fields'] = ','.join(tweet_fields)
        else:
            params['tweet.fields'] = 'created_at,public_metrics,author_id,lang'
        
        response = self._make_request('GET', endpoint, params=params)
        tweets_data = response.get('data', [])
        
        return [Tweet.from_api_data(tweet) for tweet in tweets_data]
    
    def get_following(self, user_id: str, max_results: int = 1000, 
                     pagination_token: Optional[str] = None) -> Dict[str, Any]:
        """Get users that a user is following"""
        endpoint = f"/users/{user_id}/following"
        
        params = {
            'max_results': min(max_results, 1000),
            'user.fields': (
                'created_at,description,location,name,profile_image_url,'
                'protected,public_metrics,url,username,verified'
            )
        }
        
        if pagination_token:
            params['pagination_token'] = pagination_token
        
        response = self._make_request('GET', endpoint, params=params)
        
        # Convert users to User objects
        users_data = response.get('data', [])
        users = [User.from_api_data(user_data) for user_data in users_data]
        
        return {
            'users': users,
            'meta': response.get('meta', {}),
            'next_token': response.get('meta', {}).get('next_token')
        }
    
    def unfollow_user(self, user_id: str) -> bool:
        """Unfollow a user (requires OAuth with write permissions)"""
        endpoint = f"/users/me/following/{user_id}"
        
        try:
            self._make_request('DELETE', endpoint)
            logger.info(f"Successfully unfollowed user {user_id}")
            return True
        except APIError as e:
            logger.error(f"Failed to unfollow user {user_id}: {e.message}")
            return False
    
    def get_rate_limit_status(self) -> Dict[str, Dict]:
        """Get current rate limit status for tracked endpoints"""
        return self._rate_limits.copy()