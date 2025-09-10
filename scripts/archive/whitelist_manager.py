# ABOUTME: Whitelist manager for protecting important accounts from unfollowing
# ABOUTME: Safety feature to ensure valuable relationships are never accidentally broken

import os
import json
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv

from oauth_authenticator import XOAuthAuthenticator
from cleaner_database import CleanerDatabase

# Load environment variables
load_dotenv()

class WhitelistManager:
    """
    Manages whitelist of accounts that should never be unfollowed.
    Provides safety protection for important relationships.
    """
    
    def __init__(self):
        """Initialize whitelist manager"""
        self.db = CleanerDatabase()
        self.authenticator = XOAuthAuthenticator()
        
        # Load tokens for API access
        self.tokens = self.authenticator.load_tokens()
        if self.tokens:
            self.headers = {
                'Authorization': f"Bearer {self.tokens['access_token']}",
                'User-Agent': 'X-Whitelist-Manager-v1.0'
            }
        else:
            self.headers = None
            print("⚠️ No OAuth tokens found - some features may be limited")
        
        print("🛡️ Whitelist Manager initialized")
    
    def add_to_whitelist(self, identifier: str, reason: str = "Manual addition") -> bool:
        """
        Add account to whitelist by username or user ID
        
        Args:
            identifier: Username (with or without @) or user ID
            reason: Reason for whitelisting
        """
        try:
            # Clean up username
            if identifier.startswith('@'):
                identifier = identifier[1:]
            
            # Check if it's a user ID (numeric) or username
            if identifier.isdigit():
                user_id = identifier
                username = self._get_username_from_id(user_id)
            else:
                username = identifier
                user_id = self._get_user_id_from_username(username)
            
            if not user_id or not username:
                print(f"❌ Could not find user: {identifier}")
                return False
            
            # Add to whitelist
            success = self.db.add_to_whitelist(user_id, username, reason)
            
            if success:
                print(f"✅ Added @{username} to whitelist")
                print(f"   Reason: {reason}")
                return True
            else:
                print(f"❌ Failed to add @{username} to whitelist")
                return False
                
        except Exception as e:
            print(f"❌ Error adding to whitelist: {e}")
            return False
    
    def _get_user_id_from_username(self, username: str) -> Optional[str]:
        """Get user ID from username using API"""
        if not self.headers:
            print("❌ No authentication available for user lookup")
            return None
        
        try:
            url = f"https://api.twitter.com/2/users/by/username/{username}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                return data['data']['id']
            else:
                print(f"❌ User lookup failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error looking up user: {e}")
            return None
    
    def _get_username_from_id(self, user_id: str) -> Optional[str]:
        """Get username from user ID using API"""
        if not self.headers:
            print("❌ No authentication available for user lookup")
            return None
        
        try:
            url = f"https://api.twitter.com/2/users/{user_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                return data['data']['username']
            else:
                print(f"❌ User lookup failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error looking up user: {e}")
            return None
    
    def remove_from_whitelist(self, identifier: str) -> bool:
        """Remove account from whitelist"""
        try:
            cursor = self.db.conn.cursor()
            
            # Clean up identifier
            if identifier.startswith('@'):
                identifier = identifier[1:]
            
            # Remove by username or user_id
            if identifier.isdigit():
                cursor.execute('DELETE FROM whitelist WHERE user_id = ?', (identifier,))
                cursor.execute('UPDATE following_status SET is_whitelisted = 0 WHERE user_id = ?', (identifier,))
            else:
                cursor.execute('DELETE FROM whitelist WHERE username = ?', (identifier,))
                cursor.execute('UPDATE following_status SET is_whitelisted = 0 WHERE username = ?', (identifier,))
            
            if cursor.rowcount > 0:
                self.db.conn.commit()
                print(f"✅ Removed {identifier} from whitelist")
                return True
            else:
                print(f"⚠️ {identifier} was not in whitelist")
                return False
                
        except Exception as e:
            print(f"❌ Error removing from whitelist: {e}")
            return False
    
    def list_whitelist(self) -> List[Dict]:
        """List all whitelisted accounts"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT user_id, username, display_name, reason, added_date 
                FROM whitelist 
                ORDER BY added_date DESC
            ''')
            
            whitelist = [dict(row) for row in cursor.fetchall()]
            
            if whitelist:
                print(f"🛡️ WHITELISTED ACCOUNTS ({len(whitelist)} total)")
                print("=" * 50)
                
                for i, account in enumerate(whitelist, 1):
                    username = account['username'] or 'N/A'
                    display_name = account['display_name'] or 'N/A'
                    reason = account['reason'] or 'No reason provided'
                    added_date = account['added_date'][:10] if account['added_date'] else 'Unknown'
                    
                    print(f"{i:2d}. @{username:<20} ({display_name})")
                    print(f"    Reason: {reason}")
                    print(f"    Added: {added_date}")
                    print()
            else:
                print("📝 No accounts in whitelist")
            
            return whitelist
            
        except Exception as e:
            print(f"❌ Error listing whitelist: {e}")
            return []
    
    def auto_whitelist_verified(self) -> int:
        """Automatically whitelist all verified accounts in following list"""
        try:
            cursor = self.db.conn.cursor()
            
            # Get verified accounts that aren't whitelisted
            cursor.execute('''
                SELECT user_id, username, display_name 
                FROM following_status 
                WHERE verified = 1 AND is_whitelisted = 0 AND unfollowed_date IS NULL
            ''')
            
            verified_accounts = cursor.fetchall()
            added_count = 0
            
            for account in verified_accounts:
                user_id = account['user_id']
                username = account['username'] or f"user_{user_id}"
                
                if self.db.add_to_whitelist(user_id, username, "Auto-added: Verified account"):
                    added_count += 1
            
            print(f"✅ Auto-whitelisted {added_count} verified accounts")
            return added_count
            
        except Exception as e:
            print(f"❌ Error auto-whitelisting verified accounts: {e}")
            return 0
    
    def auto_whitelist_high_followers(self, min_followers: int = 100000) -> int:
        """Automatically whitelist accounts with high follower counts"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute('''
                SELECT user_id, username, display_name, follower_count
                FROM following_status 
                WHERE follower_count >= ? AND is_whitelisted = 0 AND unfollowed_date IS NULL
            ''', (min_followers,))
            
            high_follower_accounts = cursor.fetchall()
            added_count = 0
            
            for account in high_follower_accounts:
                user_id = account['user_id']
                username = account['username'] or f"user_{user_id}"
                follower_count = account['follower_count']
                
                reason = f"Auto-added: High influence ({follower_count:,} followers)"
                if self.db.add_to_whitelist(user_id, username, reason):
                    added_count += 1
            
            print(f"✅ Auto-whitelisted {added_count} high-follower accounts")
            return added_count
            
        except Exception as e:
            print(f"❌ Error auto-whitelisting high-follower accounts: {e}")
            return 0
    
    def import_whitelist_from_file(self, filename: str) -> int:
        """Import whitelist from JSON or text file"""
        try:
            if not os.path.exists(filename):
                print(f"❌ File not found: {filename}")
                return 0
            
            added_count = 0
            
            if filename.endswith('.json'):
                # JSON format
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            username = item.get('username')
                            reason = item.get('reason', 'Imported from file')
                        else:
                            username = str(item)
                            reason = 'Imported from file'
                        
                        if username and self.add_to_whitelist(username, reason):
                            added_count += 1
                            
            else:
                # Text format - one username per line
                with open(filename, 'r') as f:
                    for line in f:
                        username = line.strip()
                        if username and not username.startswith('#'):
                            if self.add_to_whitelist(username, 'Imported from file'):
                                added_count += 1
            
            print(f"✅ Imported {added_count} accounts from {filename}")
            return added_count
            
        except Exception as e:
            print(f"❌ Error importing whitelist: {e}")
            return 0
    
    def export_whitelist_to_file(self, filename: str = None) -> str:
        """Export whitelist to JSON file"""
        if filename is None:
            filename = f"whitelist_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            whitelist = self.list_whitelist()
            
            with open(filename, 'w') as f:
                json.dump(whitelist, f, indent=2, default=str)
            
            print(f"📤 Exported {len(whitelist)} whitelisted accounts to {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error exporting whitelist: {e}")
            return ""
    
    def bulk_add_from_list(self, usernames: List[str], reason: str = "Bulk addition") -> int:
        """Add multiple usernames to whitelist"""
        added_count = 0
        
        print(f"🔄 Adding {len(usernames)} accounts to whitelist...")
        
        for username in usernames:
            if self.add_to_whitelist(username, reason):
                added_count += 1
        
        print(f"✅ Successfully added {added_count}/{len(usernames)} accounts")
        return added_count
    
    def suggest_whitelist_candidates(self) -> List[Dict]:
        """Suggest accounts that might be good whitelist candidates"""
        try:
            cursor = self.db.conn.cursor()
            
            # Find high-value accounts not yet whitelisted
            cursor.execute('''
                SELECT user_id, username, display_name, follower_count, verified, 
                       days_inactive, tweet_count
                FROM following_status 
                WHERE is_whitelisted = 0 AND unfollowed_date IS NULL
                  AND (
                    verified = 1 OR 
                    follower_count > 50000 OR
                    (follower_count > 10000 AND days_inactive < 30)
                  )
                ORDER BY follower_count DESC
                LIMIT 20
            ''')
            
            candidates = [dict(row) for row in cursor.fetchall()]
            
            if candidates:
                print("💡 WHITELIST SUGGESTIONS")
                print("=" * 30)
                print("These accounts might be worth protecting:")
                print()
                
                for i, account in enumerate(candidates, 1):
                    username = account['username'] or 'N/A'
                    display_name = account['display_name'] or 'N/A'
                    followers = account['follower_count'] or 0
                    verified = "✅" if account['verified'] else "❌"
                    inactive_days = account['days_inactive'] or 0
                    
                    reasons = []
                    if account['verified']:
                        reasons.append("Verified")
                    if followers > 100000:
                        reasons.append("High influence")
                    if inactive_days < 30:
                        reasons.append("Active")
                    
                    print(f"{i:2d}. @{username:<20} ({display_name})")
                    print(f"    {followers:,} followers, Verified: {verified}")
                    print(f"    Reasons: {', '.join(reasons)}")
                    print()
            else:
                print("✅ No obvious whitelist candidates found")
            
            return candidates
            
        except Exception as e:
            print(f"❌ Error finding whitelist candidates: {e}")
            return []

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='X Whitelist Manager')
    parser.add_argument('--add', type=str, help='Add username to whitelist')
    parser.add_argument('--remove', type=str, help='Remove username from whitelist')
    parser.add_argument('--list', action='store_true', help='List all whitelisted accounts')
    parser.add_argument('--reason', type=str, default='Manual addition', help='Reason for whitelisting')
    parser.add_argument('--auto-verified', action='store_true', help='Auto-whitelist verified accounts')
    parser.add_argument('--auto-influencers', action='store_true', help='Auto-whitelist high-follower accounts')
    parser.add_argument('--min-followers', type=int, default=100000, help='Minimum followers for auto-whitelist')
    parser.add_argument('--import-file', type=str, help='Import whitelist from file')
    parser.add_argument('--export-file', type=str, help='Export whitelist to file')
    parser.add_argument('--suggest', action='store_true', help='Suggest whitelist candidates')
    parser.add_argument('--bulk-add', type=str, nargs='+', help='Add multiple usernames')
    
    args = parser.parse_args()
    
    try:
        manager = WhitelistManager()
        
        if args.add:
            manager.add_to_whitelist(args.add, args.reason)
        
        elif args.remove:
            manager.remove_from_whitelist(args.remove)
        
        elif args.list:
            manager.list_whitelist()
        
        elif args.auto_verified:
            manager.auto_whitelist_verified()
        
        elif args.auto_influencers:
            manager.auto_whitelist_high_followers(args.min_followers)
        
        elif args.import_file:
            manager.import_whitelist_from_file(args.import_file)
        
        elif args.export_file:
            manager.export_whitelist_to_file(args.export_file)
        
        elif args.suggest:
            manager.suggest_whitelist_candidates()
        
        elif args.bulk_add:
            manager.bulk_add_from_list(args.bulk_add, args.reason)
        
        else:
            # Interactive mode
            print("🛡️ WHITELIST MANAGER - INTERACTIVE MODE")
            print("=" * 40)
            
            while True:
                print("\\nOptions:")
                print("1. Add account to whitelist")
                print("2. Remove account from whitelist") 
                print("3. List whitelisted accounts")
                print("4. Auto-whitelist verified accounts")
                print("5. Auto-whitelist influencers")
                print("6. Show whitelist suggestions")
                print("7. Export whitelist")
                print("8. Exit")
                
                choice = input("\\nEnter choice (1-8): ").strip()
                
                if choice == '1':
                    username = input("Enter username (with or without @): ").strip()
                    reason = input("Enter reason (optional): ").strip() or "Manual addition"
                    manager.add_to_whitelist(username, reason)
                
                elif choice == '2':
                    username = input("Enter username to remove: ").strip()
                    manager.remove_from_whitelist(username)
                
                elif choice == '3':
                    manager.list_whitelist()
                
                elif choice == '4':
                    manager.auto_whitelist_verified()
                
                elif choice == '5':
                    min_followers = input("Minimum followers (default 100000): ").strip()
                    min_followers = int(min_followers) if min_followers.isdigit() else 100000
                    manager.auto_whitelist_high_followers(min_followers)
                
                elif choice == '6':
                    manager.suggest_whitelist_candidates()
                
                elif choice == '7':
                    filename = input("Export filename (optional): ").strip()
                    manager.export_whitelist_to_file(filename if filename else None)
                
                elif choice == '8':
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid choice, please try again")
        
    except KeyboardInterrupt:
        print("\\n👋 Whitelist manager interrupted by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")

if __name__ == "__main__":
    main()