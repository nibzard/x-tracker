# ABOUTME: Main inactive account cleaner system with smart unfollowing logic
# ABOUTME: Leverages 40k tweet rate limit discovery for massive activity checking

import os
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import argparse
import requests
from dotenv import load_dotenv

from oauth_authenticator import XOAuthAuthenticator
from cleaner_database import CleanerDatabase

# Load environment variables
load_dotenv()

class InactiveAccountCleaner:
    """
    Advanced inactive account cleaner for X (Twitter).
    Uses OAuth user context to access following list and manage unfollows.
    Leverages 40,000 tweet request limit for massive activity checking.
    """
    
    def __init__(self, dry_run: bool = False):
        """Initialize the cleaner system"""
        self.dry_run = dry_run
        self.authenticator = XOAuthAuthenticator()
        self.db = CleanerDatabase()
        
        # Configuration
        self.config = {
            'inactive_threshold_days': 180,  # 6 months default
            'max_unfollows_per_run': 50,
            'max_unfollows_per_day': 100,
            'protect_verified': True,
            'protect_high_followers': True,
            'min_follower_threshold': 10000,
            'batch_size': 100,  # For API calls
            'request_delay': 1,  # Seconds between requests
            'min_unfollow_score': 50
        }
        
        # Load tokens for direct API access (faster than Tweepy for bulk operations)
        self.tokens = self.authenticator.load_tokens()
        if not self.tokens:
            raise ValueError("No OAuth tokens found. Run oauth_authenticator.py first.")
        
        self.headers = {
            'Authorization': f"Bearer {self.tokens['access_token']}",
            'User-Agent': 'X-Inactive-Account-Cleaner-v1.0'
        }
        
        print("🧹 Inactive Account Cleaner initialized")
        print(f"🔧 Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"📊 Inactive threshold: {self.config['inactive_threshold_days']} days")
        print(f"🎯 Max unfollows per run: {self.config['max_unfollows_per_run']}")
    
    def fetch_following_list(self) -> int:
        """Fetch complete following list and store in database"""
        print("\n📥 FETCHING FOLLOWING LIST")
        print("=" * 40)
        
        following_count = 0
        pagination_token = None
        
        while True:
            try:
                # Build request URL
                url = "https://api.twitter.com/2/users/me/following"
                params = {
                    'max_results': 1000,  # Maximum per request
                    'user.fields': 'created_at,description,location,name,pinned_tweet_id,'
                                  'profile_image_url,protected,public_metrics,url,username,'
                                  'verified,verified_type'
                }
                
                if pagination_token:
                    params['pagination_token'] = pagination_token
                
                print(f"📡 Fetching following batch... (Total so far: {following_count})")
                
                response = requests.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    users = data.get('data', [])
                    
                    # Process batch
                    for user in users:
                        if self.db.add_following_account(user):
                            following_count += 1
                    
                    print(f"   ✅ Processed {len(users)} accounts")
                    
                    # Check for more pages
                    meta = data.get('meta', {})
                    if 'next_token' in meta:
                        pagination_token = meta['next_token']
                        time.sleep(self.config['request_delay'])
                    else:
                        break
                        
                elif response.status_code == 429:
                    print("   ⚠️ Rate limited, waiting...")
                    time.sleep(60)
                    continue
                    
                else:
                    print(f"   ❌ API error: {response.status_code}")
                    print(response.text[:200])
                    break
                    
            except Exception as e:
                print(f"   💥 Exception: {e}")
                break
        
        print(f"\n✅ Following list complete: {following_count:,} accounts")
        return following_count
    
    def check_account_activity(self, user_ids: List[str]) -> int:
        """Check activity for list of user IDs using the 40k rate limit"""
        print(f"\n🔍 CHECKING ACTIVITY FOR {len(user_ids):,} ACCOUNTS")
        print("=" * 50)
        print("💡 Using 40k tweet rate limit discovery!")
        
        checked_count = 0
        
        for i, user_id in enumerate(user_ids):
            try:
                # Get user's latest tweet to check activity
                url = f"https://api.twitter.com/2/users/{user_id}/tweets"
                params = {
                    'max_results': 1,
                    'tweet.fields': 'created_at,public_metrics'
                }
                
                response = requests.get(url, headers=self.headers, params=params)
                rate_remaining = response.headers.get('x-rate-limit-remaining', 'N/A')
                
                if response.status_code == 200:
                    data = response.json()
                    tweets = data.get('data', [])
                    
                    activity_data = {
                        'rate_limit_remaining': rate_remaining
                    }
                    
                    if tweets:
                        latest_tweet = tweets[0]
                        activity_data.update({
                            'last_tweet_id': latest_tweet['id'],
                            'last_tweet_date': latest_tweet['created_at'],
                            'last_tweet_text': latest_tweet.get('text', '')[:100]
                        })
                    else:
                        # No tweets found - completely inactive
                        activity_data['last_tweet_date'] = None
                    
                    # Update database
                    self.db.update_account_activity(user_id, activity_data)
                    checked_count += 1
                    
                    if (i + 1) % 100 == 0:
                        print(f"   📊 Progress: {i + 1:,}/{len(user_ids):,} "
                              f"(Rate limit: {rate_remaining})")
                
                elif response.status_code == 404:
                    # Account doesn't exist or no tweets
                    activity_data = {
                        'last_tweet_date': None,
                        'rate_limit_remaining': rate_remaining
                    }
                    self.db.update_account_activity(user_id, activity_data)
                    checked_count += 1
                
                elif response.status_code == 401:
                    # Private account
                    print(f"   🔒 Private account: {user_id}")
                    checked_count += 1
                
                elif response.status_code == 429:
                    print(f"   ⚠️ Rate limit hit at {i+1}/{len(user_ids)}")
                    print(f"       Checked {checked_count:,} accounts so far")
                    break
                
                else:
                    print(f"   ❌ Error {response.status_code} for {user_id}")
                    continue
                
                # Small delay to be respectful
                if i < len(user_ids) - 1:
                    time.sleep(0.1)
                
            except Exception as e:
                print(f"   💥 Exception checking {user_id}: {e}")
                continue
        
        print(f"\n✅ Activity check complete: {checked_count:,} accounts checked")
        return checked_count
    
    def run_activity_analysis(self) -> int:
        """Run activity analysis on all unchecked accounts"""
        # Get unchecked accounts
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT user_id FROM following_status 
            WHERE unfollowed_date IS NULL 
              AND (last_checked_date IS NULL OR last_checked_date < datetime('now', '-7 days'))
            ORDER BY follower_count DESC
        ''')
        
        unchecked_ids = [row[0] for row in cursor.fetchall()]
        
        if not unchecked_ids:
            print("✅ All accounts already checked recently")
            return 0
        
        print(f"📋 Found {len(unchecked_ids):,} accounts to check")
        
        # Check activity in batches
        return self.check_account_activity(unchecked_ids)
    
    def calculate_and_score_accounts(self) -> int:
        """Calculate unfollow scores for all accounts"""
        print("\n🧮 CALCULATING UNFOLLOW SCORES")
        print("=" * 35)
        
        return self.db.calculate_unfollow_scores()
    
    def get_unfollow_plan(self) -> List[Dict]:
        """Get prioritized list of accounts to unfollow"""
        candidates = self.db.get_unfollow_candidates(
            limit=self.config['max_unfollows_per_run'],
            min_score=self.config['min_unfollow_score']
        )
        
        print(f"\n🎯 UNFOLLOW PLAN")
        print("=" * 20)
        print(f"Candidates found: {len(candidates)}")
        
        if candidates:
            print("\\nTop candidates:")
            for i, account in enumerate(candidates[:10], 1):
                days = account.get('days_inactive', 0)
                score = account.get('unfollow_score', 0)
                followers = account.get('follower_count', 0)
                
                print(f"  {i:2d}. @{account['username']:<20} "
                      f"({days:3d} days inactive, "
                      f"{followers:,} followers, "
                      f"score: {score})")
        
        return candidates
    
    def execute_unfollows(self, accounts: List[Dict]) -> Tuple[int, int]:
        """Execute unfollow operations"""
        if not accounts:
            return 0, 0
        
        print(f"\n{'🔥 EXECUTING UNFOLLOWS' if not self.dry_run else '🔍 DRY RUN - SIMULATING UNFOLLOWS'}")
        print("=" * 50)
        
        batch_id = str(uuid.uuid4())[:8]
        success_count = 0
        error_count = 0
        
        for i, account in enumerate(accounts, 1):
            username = account['username']
            user_id = account['user_id']
            days_inactive = account.get('days_inactive', 0)
            score = account.get('unfollow_score', 0)
            
            print(f"[{i:2d}/{len(accounts)}] {'Simulating' if self.dry_run else 'Unfollowing'} "
                  f"@{username} ({days_inactive} days inactive, score: {score})")
            
            if self.dry_run:
                # Simulate unfollow
                success_count += 1
                time.sleep(0.1)
                continue
            
            try:
                # Actual unfollow via API
                url = f"https://api.twitter.com/2/users/me/following/{user_id}"
                response = requests.delete(url, headers=self.headers)
                
                if response.status_code == 200:
                    # Log successful unfollow
                    reason = f"Inactive for {days_inactive} days (score: {score})"
                    self.db.log_unfollow(account, reason, batch_id)
                    success_count += 1
                    print(f"   ✅ Unfollowed successfully")
                    
                elif response.status_code == 404:
                    print(f"   ⚠️ Account not found or already unfollowed")
                    success_count += 1  # Count as success
                    
                elif response.status_code == 429:
                    print(f"   ⚠️ Rate limit hit - stopping unfollows")
                    break
                    
                else:
                    print(f"   ❌ Error {response.status_code}: {response.text[:100]}")
                    error_count += 1
                
                # Delay between unfollows to avoid rate limits
                time.sleep(2)
                
            except Exception as e:
                print(f"   💥 Exception: {e}")
                error_count += 1
        
        print(f"\n📊 Unfollow Results:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   🆔 Batch ID: {batch_id}")
        
        return success_count, error_count
    
    def generate_report(self) -> Dict:
        """Generate comprehensive cleaning report"""
        stats = self.db.get_statistics()
        
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'mode': 'dry_run' if self.dry_run else 'live',
            'configuration': self.config,
            'statistics': stats,
            'recommendations': []
        }
        
        # Add recommendations based on stats
        if stats.get('dead_1year', 0) > 0:
            report['recommendations'].append(
                f"Consider unfollowing {stats['dead_1year']} accounts inactive for 1+ years"
            )
        
        if stats.get('unchecked', 0) > 0:
            report['recommendations'].append(
                f"Run activity check on {stats['unchecked']} unchecked accounts"
            )
        
        if stats.get('unfollow_candidates', 0) > 100:
            report['recommendations'].append(
                "High number of unfollow candidates - consider multiple cleaning sessions"
            )
        
        return report
    
    def run_full_cleaning_cycle(self):
        """Run complete cleaning cycle"""
        print("🧹 INACTIVE ACCOUNT CLEANER - FULL CYCLE")
        print("=" * 50)
        print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Mode: {'DRY RUN (Safe)' if self.dry_run else 'LIVE (Will unfollow!)'}")
        print()
        
        try:
            # Step 1: Fetch following list
            following_count = self.fetch_following_list()
            
            # Step 2: Check activity
            checked_count = self.run_activity_analysis()
            
            # Step 3: Calculate scores
            scored_count = self.calculate_and_score_accounts()
            
            # Step 4: Get unfollow plan
            candidates = self.get_unfollow_plan()
            
            # Step 5: Execute unfollows (if not dry run)
            if candidates:
                if not self.dry_run:
                    confirm = input(f"\n⚠️ About to unfollow {len(candidates)} accounts. Continue? (y/N): ")
                    if confirm.lower() != 'y':
                        print("❌ Unfollowing cancelled by user")
                        return
                
                success_count, error_count = self.execute_unfollows(candidates)
            else:
                print("\n✅ No accounts meet unfollowing criteria")
                success_count, error_count = 0, 0
            
            # Step 6: Generate report
            report = self.generate_report()
            
            # Save report
            report_file = f"cleaning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            print(f"\n📋 CLEANING SUMMARY")
            print("=" * 25)
            print(f"Following checked: {following_count:,}")
            print(f"Activity analyzed: {checked_count:,}")
            print(f"Accounts scored: {scored_count:,}")
            print(f"Unfollowed: {success_count}")
            print(f"Errors: {error_count}")
            print(f"Report saved: {report_file}")
            
            if self.dry_run:
                print("\n💡 This was a DRY RUN - no accounts were actually unfollowed")
                print("   Remove --dry-run flag to perform actual unfollows")
            
        except Exception as e:
            print(f"\n💥 Fatal error: {e}")
            raise

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='X Inactive Account Cleaner')
    parser.add_argument('--dry-run', action='store_true', 
                      help='Simulate unfollows without actually executing them')
    parser.add_argument('--inactive-days', type=int, default=180,
                      help='Days of inactivity threshold (default: 180)')
    parser.add_argument('--max-unfollows', type=int, default=50,
                      help='Maximum unfollows per run (default: 50)')
    parser.add_argument('--min-score', type=int, default=50,
                      help='Minimum unfollow score threshold (default: 50)')
    parser.add_argument('--activity-only', action='store_true',
                      help='Only check activity, don\'t unfollow')
    parser.add_argument('--stats-only', action='store_true',
                      help='Only show statistics')
    
    args = parser.parse_args()
    
    try:
        # Initialize cleaner
        cleaner = InactiveAccountCleaner(dry_run=args.dry_run)
        
        # Update configuration
        cleaner.config.update({
            'inactive_threshold_days': args.inactive_days,
            'max_unfollows_per_run': args.max_unfollows,
            'min_unfollow_score': args.min_score
        })
        
        if args.stats_only:
            # Just show stats
            stats = cleaner.db.get_statistics()
            print("📊 DATABASE STATISTICS")
            print("=" * 30)
            for key, value in stats.items():
                print(f"{key.replace('_', ' ').title()}: {value:,}")
            return
        
        if args.activity_only:
            # Just check activity
            checked = cleaner.run_activity_analysis()
            scored = cleaner.calculate_and_score_accounts()
            print(f"✅ Activity check complete: {checked:,} checked, {scored:,} scored")
            return
        
        # Run full cleaning cycle
        cleaner.run_full_cleaning_cycle()
        
    except KeyboardInterrupt:
        print("\n👋 Cleaning interrupted by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")

if __name__ == "__main__":
    main()