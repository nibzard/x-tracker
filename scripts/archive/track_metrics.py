# ABOUTME: Public metrics tracker for X accounts using free tier API
# ABOUTME: Tracks follower counts, engagement metrics, and profile changes over time

import os
import json
import csv
import time
from datetime import datetime, timezone
from typing import Dict, Optional, List
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PublicMetricsTracker:
    """
    Tracks public metrics for X accounts using free tier API access.
    This approach works within rate limits and tracks aggregate data.
    """
    
    def __init__(self):
        """Initialize the tracker with API credentials"""
        self.bearer_token = os.getenv('BEARER_TOKEN')
        self.target_user_id = os.getenv('TARGET_USER_ID')
        self.target_username = os.getenv('TARGET_USERNAME')
        
        if not all([self.bearer_token, self.target_user_id]):
            raise ValueError("Missing required environment variables: BEARER_TOKEN, TARGET_USER_ID")
        
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "X-Metrics-Tracker-v1.0"
        }
        
        print(f"Initialized metrics tracker for @{self.target_username} (ID: {self.target_user_id})")
    
    def get_user_metrics(self) -> Optional[Dict]:
        """
        Fetch public metrics for the target user.
        Uses the GET /2/users/:id endpoint which is available on free tier.
        """
        url = f"{self.base_url}/users/{self.target_user_id}"
        params = {
            "user.fields": "created_at,description,location,name,pinned_tweet_id,"
                          "profile_image_url,protected,public_metrics,url,username,verified,verified_type"
        }
        
        try:
            print(f"Fetching metrics for user {self.target_user_id}...")
            response = requests.get(url, headers=self.headers, params=params)
            
            # Check rate limit headers
            remaining = response.headers.get('x-rate-limit-remaining', 'Unknown')
            limit = response.headers.get('x-rate-limit-limit', 'Unknown')
            reset_timestamp = response.headers.get('x-rate-limit-reset', None)
            
            print(f"Rate limit: {remaining}/{limit} remaining")
            if reset_timestamp:
                reset_time = datetime.fromtimestamp(int(reset_timestamp), timezone.utc)
                print(f"Rate limit resets at: {reset_time.isoformat()}")
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('data', {})
                
                # Extract metrics
                public_metrics = user_data.get('public_metrics', {})
                metrics = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'user_id': user_data.get('id'),
                    'username': user_data.get('username'),
                    'name': user_data.get('name'),
                    'description': user_data.get('description'),
                    'location': user_data.get('location'),
                    'verified': user_data.get('verified', False),
                    'protected': user_data.get('protected', False),
                    'followers_count': public_metrics.get('followers_count', 0),
                    'following_count': public_metrics.get('following_count', 0),
                    'tweet_count': public_metrics.get('tweet_count', 0),
                    'listed_count': public_metrics.get('listed_count', 0),
                    'like_count': public_metrics.get('like_count', 0),
                    'profile_image_url': user_data.get('profile_image_url'),
                    'url': user_data.get('url'),
                    'pinned_tweet_id': user_data.get('pinned_tweet_id'),
                    'rate_limit_remaining': remaining,
                    'rate_limit_limit': limit
                }
                
                print(f"✓ Successfully fetched metrics for @{user_data.get('username')}")
                print(f"  Followers: {public_metrics.get('followers_count', 0):,}")
                print(f"  Following: {public_metrics.get('following_count', 0):,}")
                print(f"  Tweets: {public_metrics.get('tweet_count', 0):,}")
                print(f"  Listed: {public_metrics.get('listed_count', 0):,}")
                
                return metrics
                
            elif response.status_code == 429:
                print("❌ Rate limit exceeded. Need to wait before next request.")
                error_data = response.json()
                print(f"Error details: {error_data}")
                return None
                
            elif response.status_code == 403:
                print("❌ Access forbidden. This might be due to:")
                print("  - API key doesn't have sufficient permissions")
                print("  - Account is protected/private")
                print("  - Free tier limitations")
                error_data = response.json()
                print(f"Error details: {error_data}")
                return None
                
            else:
                print(f"❌ API request failed with status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Response text: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception occurred while fetching metrics: {e}")
            return None
    
    def save_metrics_to_csv(self, metrics: Dict, filename: str = "metrics_history.csv") -> bool:
        """Save metrics to CSV file with timestamp"""
        try:
            # Check if file exists to determine if we need headers
            file_exists = os.path.isfile(filename)
            
            with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'timestamp', 'user_id', 'username', 'name', 'description', 'location',
                    'verified', 'protected', 'followers_count', 'following_count', 
                    'tweet_count', 'listed_count', 'like_count', 'profile_image_url',
                    'url', 'pinned_tweet_id', 'rate_limit_remaining', 'rate_limit_limit'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header if file is new
                if not file_exists:
                    writer.writeheader()
                    print(f"✓ Created new CSV file: {filename}")
                
                writer.writerow(metrics)
                print(f"✓ Metrics saved to {filename}")
                return True
                
        except Exception as e:
            print(f"❌ Error saving metrics to CSV: {e}")
            return False
    
    def save_metrics_to_json(self, metrics: Dict, filename: str = "latest_metrics.json") -> bool:
        """Save latest metrics to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
            print(f"✓ Latest metrics saved to {filename}")
            return True
        except Exception as e:
            print(f"❌ Error saving metrics to JSON: {e}")
            return False
    
    def calculate_changes(self, current_metrics: Dict, previous_filename: str = "metrics_history.csv") -> Optional[Dict]:
        """Calculate changes since last measurement"""
        try:
            if not os.path.isfile(previous_filename):
                print("No previous data found for comparison")
                return None
            
            # Read the last entry from CSV
            with open(previous_filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            if len(rows) < 2:  # Need at least one previous entry
                print("Need at least one previous measurement for comparison")
                return None
            
            previous_metrics = rows[-2]  # Second to last (last is current)
            
            # Calculate changes
            changes = {
                'period_start': previous_metrics['timestamp'],
                'period_end': current_metrics['timestamp'],
                'followers_change': int(current_metrics['followers_count']) - int(previous_metrics['followers_count']),
                'following_change': int(current_metrics['following_count']) - int(previous_metrics['following_count']),
                'tweets_change': int(current_metrics['tweet_count']) - int(previous_metrics['tweet_count']),
                'listed_change': int(current_metrics['listed_count']) - int(previous_metrics['listed_count']),
                'likes_change': int(current_metrics['like_count']) - int(previous_metrics['like_count']),
                'name_changed': current_metrics['name'] != previous_metrics['name'],
                'description_changed': current_metrics['description'] != previous_metrics['description'],
                'location_changed': current_metrics['location'] != previous_metrics['location'],
                'profile_image_changed': current_metrics['profile_image_url'] != previous_metrics['profile_image_url'],
            }
            
            # Print changes summary
            print("\n" + "="*50)
            print("CHANGES SINCE LAST MEASUREMENT")
            print("="*50)
            print(f"Followers: {changes['followers_change']:+d}")
            print(f"Following: {changes['following_change']:+d}")
            print(f"Tweets: {changes['tweets_change']:+d}")
            print(f"Listed: {changes['listed_change']:+d}")
            print(f"Likes: {changes['likes_change']:+d}")
            
            if changes['name_changed']:
                print(f"Name changed: '{previous_metrics['name']}' → '{current_metrics['name']}'")
            if changes['description_changed']:
                print("Description changed")
            if changes['location_changed']:
                print(f"Location changed: '{previous_metrics['location']}' → '{current_metrics['location']}'")
            if changes['profile_image_changed']:
                print("Profile image changed")
            
            return changes
            
        except Exception as e:
            print(f"❌ Error calculating changes: {e}")
            return None
    
    def run_tracking_cycle(self):
        """Run a complete tracking cycle"""
        print("="*60)
        print("X PUBLIC METRICS TRACKER")
        print("="*60)
        print(f"Target: @{self.target_username} (ID: {self.target_user_id})")
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print()
        
        # Fetch current metrics
        metrics = self.get_user_metrics()
        if not metrics:
            print("❌ Failed to fetch metrics. Exiting.")
            return False
        
        # Save to files
        csv_success = self.save_metrics_to_csv(metrics)
        json_success = self.save_metrics_to_json(metrics)
        
        if not (csv_success and json_success):
            print("❌ Failed to save metrics. Exiting.")
            return False
        
        # Calculate and display changes
        changes = self.calculate_changes(metrics)
        
        print("\n✓ Tracking cycle completed successfully")
        return True

def main():
    """Main function"""
    try:
        tracker = PublicMetricsTracker()
        success = tracker.run_tracking_cycle()
        exit_code = 0 if success else 1
        exit(exit_code)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main()