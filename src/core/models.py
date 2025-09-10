# ABOUTME: Core domain models for X-Tracker
# ABOUTME: Data structures for User, Tweet, Metrics and other domain entities

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from enum import Enum

class UserStatus(Enum):
    """Status of a user account"""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    PROTECTED = "protected"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"

class UnfollowReason(Enum):
    """Reasons for unfollowing a user"""
    INACTIVE = "inactive"
    LOW_ENGAGEMENT = "low_engagement"
    SPAM = "spam"
    PROTECTED = "protected"
    MANUAL = "manual"

@dataclass
class User:
    """Represents a Twitter/X user"""
    id: str
    username: str
    name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    profile_image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    
    # Metrics
    followers_count: int = 0
    following_count: int = 0
    tweet_count: int = 0
    listed_count: int = 0
    like_count: int = 0
    
    # Status
    verified: bool = False
    protected: bool = False
    status: UserStatus = UserStatus.UNKNOWN
    
    # Tracking data
    first_seen: Optional[datetime] = None
    last_checked: Optional[datetime] = None
    last_tweet_date: Optional[datetime] = None
    check_count: int = 0
    
    # Calculated fields
    days_inactive: Optional[int] = None
    unfollow_score: Optional[int] = None
    is_whitelisted: bool = False
    is_mutual_follow: bool = False
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.first_seen is None:
            self.first_seen = datetime.now(timezone.utc)
    
    @property
    def is_inactive(self) -> bool:
        """Check if user is inactive based on last tweet date"""
        if not self.last_tweet_date:
            return True
        
        days_since_tweet = (datetime.now(timezone.utc) - self.last_tweet_date).days
        return days_since_tweet > 180  # 6 months threshold
    
    @property
    def engagement_estimate(self) -> float:
        """Estimate engagement rate based on available metrics"""
        if self.followers_count == 0:
            return 0.0
        
        # Simple heuristic: likes per follower
        return (self.like_count / self.followers_count) * 100
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'User':
        """Create User instance from API response data"""
        public_metrics = data.get('public_metrics', {})
        
        return cls(
            id=str(data.get('id')),
            username=data.get('username'),
            name=data.get('name'),
            bio=data.get('description'),
            location=data.get('location'),
            url=data.get('url'),
            profile_image_url=data.get('profile_image_url'),
            created_at=cls._parse_datetime(data.get('created_at')),
            followers_count=public_metrics.get('followers_count', 0),
            following_count=public_metrics.get('following_count', 0),
            tweet_count=public_metrics.get('tweet_count', 0),
            listed_count=public_metrics.get('listed_count', 0),
            like_count=public_metrics.get('like_count', 0),
            verified=data.get('verified', False),
            protected=data.get('protected', False)
        )
    
    @staticmethod
    def _parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from API"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

@dataclass
class Tweet:
    """Represents a tweet"""
    id: str
    text: str
    author_id: str
    created_at: datetime
    
    # Metrics
    retweet_count: int = 0
    like_count: int = 0
    reply_count: int = 0
    quote_count: int = 0
    bookmark_count: int = 0
    impression_count: int = 0
    
    # Metadata
    lang: Optional[str] = None
    reply_to: Optional[str] = None
    
    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate"""
        if self.impression_count == 0:
            return 0.0
        
        total_engagements = (
            self.retweet_count + self.like_count + 
            self.reply_count + self.quote_count
        )
        
        return (total_engagements / self.impression_count) * 100
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Tweet':
        """Create Tweet instance from API response data"""
        public_metrics = data.get('public_metrics', {})
        non_public_metrics = data.get('non_public_metrics', {})
        
        return cls(
            id=str(data.get('id')),
            text=data.get('text', ''),
            author_id=str(data.get('author_id')),
            created_at=datetime.fromisoformat(data.get('created_at').replace('Z', '+00:00')),
            retweet_count=public_metrics.get('retweet_count', 0),
            like_count=public_metrics.get('like_count', 0),
            reply_count=public_metrics.get('reply_count', 0),
            quote_count=public_metrics.get('quote_count', 0),
            bookmark_count=non_public_metrics.get('bookmark_count', 0),
            impression_count=non_public_metrics.get('impression_count', 0),
            lang=data.get('lang')
        )

@dataclass
class Metrics:
    """Growth metrics snapshot"""
    timestamp: datetime
    user_id: str
    
    # Current metrics
    followers_count: int
    following_count: int
    tweet_count: int
    listed_count: int
    like_count: int
    
    # Changes since last measurement
    followers_change: int = 0
    following_change: int = 0
    tweets_change: int = 0
    
    # Calculated metrics
    follower_velocity: float = 0.0  # followers per hour
    engagement_rate: float = 0.0
    growth_acceleration: float = 0.0
    
    # Rate limit info
    rate_limit_remaining: Optional[int] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)

@dataclass
class UnfollowRecord:
    """Record of an unfollow action"""
    id: Optional[int] = None
    user_id: str = ""
    username: str = ""
    display_name: Optional[str] = None
    unfollowed_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    days_inactive: Optional[int] = None
    follower_count: int = 0
    last_tweet_date: Optional[datetime] = None
    unfollow_score: int = 0
    reason: str = ""
    batch_id: Optional[str] = None
    can_rollback: bool = True

@dataclass 
class CompetitorData:
    """Data for competitor tracking"""
    user: User
    timestamp: datetime
    growth_velocity: float = 0.0
    engagement_estimate: float = 0.0
    trend_direction: str = "stable"  # up, down, stable
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)