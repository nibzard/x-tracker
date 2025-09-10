# ABOUTME: X Growth Command Center - Enhanced personal analytics with 25x daily monitoring
# ABOUTME: Leverages superior rate limits on /users/me endpoint for powerful growth insights

import os
import json
import csv
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List, Any
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class XGrowthCenter:
    """
    X Growth Command Center - Personal analytics dashboard with enhanced monitoring.
    Uses GET /2/users/me endpoint which allows 25 requests per day (vs 1 for regular user lookup).
    """
    
    def __init__(self):
        """Initialize the X Growth Center"""
        self.bearer_token = os.getenv('BEARER_TOKEN')
        self.api_key = os.getenv('API_KEY')
        self.api_key_secret = os.getenv('API_KEY_SECRET')
        
        if not self.bearer_token:
            raise ValueError("BEARER_TOKEN is required in environment variables")
        
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "X-Growth-Command-Center-v1.0"
        }
        
        # Initialize database
        self.init_database()
        print("🚀 X Growth Command Center initialized!")
        print("✨ Enhanced monitoring: 25 requests per day (vs 1 for basic tracking)")
    
    def init_database(self):
        """Initialize SQLite database for efficient data storage and querying"""
        self.conn = sqlite3.connect('x_growth_data.db')
        cursor = self.conn.cursor()
        
        # Personal metrics table (25x daily measurements)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personal_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                username TEXT,
                name TEXT,
                description TEXT,
                location TEXT,
                url TEXT,
                verified BOOLEAN,
                protected BOOLEAN,
                followers_count INTEGER,
                following_count INTEGER,
                tweet_count INTEGER,
                listed_count INTEGER,
                like_count INTEGER,
                profile_image_url TEXT,
                pinned_tweet_id TEXT,
                created_at TEXT,
                rate_limit_remaining INTEGER,
                UNIQUE(timestamp)
            )
        ''')
        
        # Growth calculations table (derived metrics)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS growth_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                period_minutes INTEGER,
                followers_change INTEGER,
                following_change INTEGER,
                tweets_change INTEGER,
                listed_change INTEGER,
                likes_change INTEGER,
                follower_velocity REAL,  -- followers per hour
                engagement_rate REAL,    -- estimated based on available data
                growth_acceleration REAL,
                UNIQUE(timestamp)
            )
        ''')
        
        # Competitor tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitor_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                competitor_username TEXT,
                competitor_user_id TEXT,
                followers_count INTEGER,
                following_count INTEGER,
                tweet_count INTEGER,
                listed_count INTEGER,
                verified BOOLEAN,
                description TEXT,
                location TEXT,
                UNIQUE(timestamp, competitor_username)
            )
        ''')
        
        self.conn.commit()
        print("📊 Database initialized with advanced analytics tables")
    
    def get_personal_metrics(self) -> Optional[Dict]:
        """
        Fetch personal account metrics using /users/me endpoint.
        This endpoint allows 25 requests per day - much better than regular user lookup!
        """
        url = f"{self.base_url}/users/me"
        params = {
            "user.fields": "created_at,description,location,name,pinned_tweet_id,"
                          "profile_image_url,protected,public_metrics,url,username,"
                          "verified,verified_type"
        }
        
        try:
            print("📈 Fetching personal metrics...")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            # Extract rate limit info
            remaining = response.headers.get('x-rate-limit-remaining', 'Unknown')
            limit = response.headers.get('x-rate-limit-limit', 'Unknown')
            reset_timestamp = response.headers.get('x-rate-limit-reset', None)
            
            print(f"🚦 Rate limit: {remaining}/{limit} remaining")
            if reset_timestamp:
                reset_time = datetime.fromtimestamp(int(reset_timestamp), timezone.utc)
                print(f"⏰ Resets at: {reset_time.strftime('%H:%M UTC')}")
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('data', {})
                public_metrics = user_data.get('public_metrics', {})
                
                # Prepare metrics dictionary
                metrics = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'user_id': user_data.get('id'),
                    'username': user_data.get('username'),
                    'name': user_data.get('name'),
                    'description': user_data.get('description'),
                    'location': user_data.get('location'),
                    'url': user_data.get('url'),
                    'verified': user_data.get('verified', False),
                    'protected': user_data.get('protected', False),
                    'followers_count': public_metrics.get('followers_count', 0),
                    'following_count': public_metrics.get('following_count', 0),
                    'tweet_count': public_metrics.get('tweet_count', 0),
                    'listed_count': public_metrics.get('listed_count', 0),
                    'like_count': public_metrics.get('like_count', 0),
                    'profile_image_url': user_data.get('profile_image_url'),
                    'pinned_tweet_id': user_data.get('pinned_tweet_id'),
                    'created_at': user_data.get('created_at'),
                    'rate_limit_remaining': remaining
                }
                
                print(f"✅ Personal metrics collected for @{user_data.get('username')}")
                print(f"   Followers: {public_metrics.get('followers_count', 0):,}")
                print(f"   Following: {public_metrics.get('following_count', 0):,}")
                print(f"   Tweets: {public_metrics.get('tweet_count', 0):,}")
                print(f"   Listed: {public_metrics.get('listed_count', 0):,}")
                
                return metrics
                
            elif response.status_code == 429:
                print("⚠️  Rate limit exceeded for /users/me")
                print("💡 This endpoint allows 25 requests per day")
                return None
                
            elif response.status_code == 401:
                print("❌ Authentication failed - check BEARER_TOKEN")
                return None
                
            else:
                print(f"❌ API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception in get_personal_metrics: {e}")
            return None
    
    def save_personal_metrics(self, metrics: Dict) -> bool:
        """Save personal metrics to database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO personal_metrics 
                (timestamp, user_id, username, name, description, location, url,
                 verified, protected, followers_count, following_count, tweet_count,
                 listed_count, like_count, profile_image_url, pinned_tweet_id, 
                 created_at, rate_limit_remaining)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics['timestamp'], metrics['user_id'], metrics['username'],
                metrics['name'], metrics['description'], metrics['location'],
                metrics['url'], metrics['verified'], metrics['protected'],
                metrics['followers_count'], metrics['following_count'],
                metrics['tweet_count'], metrics['listed_count'], metrics['like_count'],
                metrics['profile_image_url'], metrics['pinned_tweet_id'],
                metrics['created_at'], metrics['rate_limit_remaining']
            ))
            
            self.conn.commit()
            print("💾 Personal metrics saved to database")
            return True
            
        except Exception as e:
            print(f"❌ Error saving personal metrics: {e}")
            return False
    
    def calculate_growth_metrics(self) -> Optional[Dict]:
        """Calculate growth metrics from recent measurements"""
        try:
            cursor = self.conn.cursor()
            
            # Get last two measurements
            cursor.execute('''
                SELECT * FROM personal_metrics 
                ORDER BY timestamp DESC 
                LIMIT 2
            ''')
            
            rows = cursor.fetchall()
            if len(rows) < 2:
                print("📊 Need at least 2 measurements to calculate growth")
                return None
            
            # Parse timestamps and calculate time difference
            current = rows[0]
            previous = rows[1]
            
            current_time = datetime.fromisoformat(current[1].replace('Z', '+00:00'))
            previous_time = datetime.fromisoformat(previous[1].replace('Z', '+00:00'))
            
            time_diff = current_time - previous_time
            period_minutes = time_diff.total_seconds() / 60
            
            # Calculate changes
            followers_change = current[9] - previous[9]  # followers_count
            following_change = current[10] - previous[10]  # following_count
            tweets_change = current[11] - previous[11]   # tweet_count
            listed_change = current[12] - previous[12]   # listed_count
            likes_change = current[13] - previous[13]    # like_count
            
            # Calculate velocity (followers per hour)
            follower_velocity = (followers_change / period_minutes) * 60 if period_minutes > 0 else 0
            
            # Calculate estimated engagement rate
            # (likes + tweets changes) / followers ratio
            engagement_rate = 0
            if current[9] > 0:  # followers_count
                engagement_rate = ((likes_change + tweets_change * 10) / current[9]) * 100
            
            # Calculate growth acceleration (change in velocity)
            growth_acceleration = 0
            cursor.execute('''
                SELECT follower_velocity FROM growth_metrics 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            last_velocity = cursor.fetchone()
            if last_velocity:
                growth_acceleration = follower_velocity - last_velocity[0]
            
            growth_data = {
                'timestamp': current[1],
                'period_minutes': period_minutes,
                'followers_change': followers_change,
                'following_change': following_change,
                'tweets_change': tweets_change,
                'listed_change': listed_change,
                'likes_change': likes_change,
                'follower_velocity': follower_velocity,
                'engagement_rate': engagement_rate,
                'growth_acceleration': growth_acceleration
            }
            
            # Save to database
            cursor.execute('''
                INSERT OR REPLACE INTO growth_metrics 
                (timestamp, period_minutes, followers_change, following_change,
                 tweets_change, listed_change, likes_change, follower_velocity,
                 engagement_rate, growth_acceleration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                growth_data['timestamp'], growth_data['period_minutes'],
                growth_data['followers_change'], growth_data['following_change'],
                growth_data['tweets_change'], growth_data['listed_change'],
                growth_data['likes_change'], growth_data['follower_velocity'],
                growth_data['engagement_rate'], growth_data['growth_acceleration']
            ))
            
            self.conn.commit()
            
            print("\n📈 GROWTH ANALYSIS")
            print("="*40)
            print(f"Time period: {period_minutes:.1f} minutes")
            print(f"Followers change: {followers_change:+d}")
            print(f"Follower velocity: {follower_velocity:.2f}/hour")
            print(f"Engagement rate: {engagement_rate:.3f}%")
            print(f"Growth acceleration: {growth_acceleration:+.2f}")
            
            return growth_data
            
        except Exception as e:
            print(f"❌ Error calculating growth metrics: {e}")
            return None
    
    def get_insights_summary(self) -> Dict:
        """Generate insights summary from recent data"""
        try:
            cursor = self.conn.cursor()
            
            # Get stats from last 24 hours
            cursor.execute('''
                SELECT 
                    COUNT(*) as measurements,
                    MAX(followers_count) - MIN(followers_count) as daily_follower_change,
                    AVG(follower_velocity) as avg_velocity,
                    MAX(follower_velocity) as peak_velocity,
                    AVG(engagement_rate) as avg_engagement
                FROM personal_metrics p
                LEFT JOIN growth_metrics g ON p.timestamp = g.timestamp
                WHERE p.timestamp > datetime('now', '-1 day')
            ''')
            
            stats = cursor.fetchone()
            
            # Get latest metrics
            cursor.execute('''
                SELECT * FROM personal_metrics 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            latest = cursor.fetchone()
            
            if latest:
                summary = {
                    'measurements_today': stats[0] if stats[0] else 0,
                    'daily_follower_change': stats[1] if stats[1] else 0,
                    'avg_velocity_per_hour': stats[2] if stats[2] else 0,
                    'peak_velocity_per_hour': stats[3] if stats[3] else 0,
                    'avg_engagement_rate': stats[4] if stats[4] else 0,
                    'current_followers': latest[9],
                    'current_following': latest[10],
                    'current_tweets': latest[11],
                    'username': latest[2],
                    'verified': latest[7],
                    'rate_limit_remaining': latest[17]
                }
                
                return summary
            
            return {}
            
        except Exception as e:
            print(f"❌ Error generating insights: {e}")
            return {}
    
    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle"""
        print("🚀 X GROWTH COMMAND CENTER - MONITORING CYCLE")
        print("="*60)
        print(f"🕐 Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("✨ Enhanced Personal Analytics (25x better than basic tracking)")
        print()
        
        # Fetch and save personal metrics
        metrics = self.get_personal_metrics()
        if not metrics:
            print("❌ Failed to fetch personal metrics")
            return False
        
        if not self.save_personal_metrics(metrics):
            print("❌ Failed to save personal metrics")
            return False
        
        # Calculate growth metrics
        growth_data = self.calculate_growth_metrics()
        
        # Generate insights
        insights = self.get_insights_summary()
        if insights:
            print("\n🎯 TODAY'S INSIGHTS")
            print("="*40)
            print(f"Measurements today: {insights['measurements_today']}/25")
            print(f"Daily follower change: {insights['daily_follower_change']:+d}")
            print(f"Average velocity: {insights['avg_velocity_per_hour']:.2f}/hour")
            print(f"Peak velocity: {insights['peak_velocity_per_hour']:.2f}/hour")
            print(f"Engagement rate: {insights['avg_engagement_rate']:.3f}%")
            print(f"Rate limit remaining: {insights['rate_limit_remaining']}")
        
        print("\n✅ Monitoring cycle completed successfully!")
        return True
    
    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    """Main function"""
    try:
        growth_center = XGrowthCenter()
        success = growth_center.run_monitoring_cycle()
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n👋 Monitoring interrupted by user")
        exit(0)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main()