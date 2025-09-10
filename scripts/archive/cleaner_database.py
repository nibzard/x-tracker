# ABOUTME: Database manager for inactive account cleaner system
# ABOUTME: Handles SQLite storage for following status, activity tracking, and unfollow logs

import sqlite3
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

class CleanerDatabase:
    """
    Database manager for the inactive account cleaner.
    Tracks following status, activity data, whitelist, and unfollow history.
    """
    
    def __init__(self, db_path: str = 'inactive_cleaner.db'):
        """Initialize database connection and create tables"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        
        self.init_database()
        print(f"🗄️ Database initialized: {db_path}")
    
    def init_database(self):
        """Create all necessary tables"""
        cursor = self.conn.cursor()
        
        # Following status and activity tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS following_status (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                display_name TEXT,
                bio TEXT,
                location TEXT,
                url TEXT,
                follower_count INTEGER,
                following_count INTEGER,
                tweet_count INTEGER,
                listed_count INTEGER,
                like_count INTEGER,
                verified BOOLEAN,
                protected BOOLEAN,
                profile_image_url TEXT,
                created_at TEXT,
                last_tweet_id TEXT,
                last_tweet_date TEXT,
                last_tweet_text TEXT,
                days_inactive INTEGER,
                posting_frequency REAL,
                engagement_estimate REAL,
                first_seen_date TEXT,
                last_checked_date TEXT,
                check_count INTEGER DEFAULT 1,
                unfollow_score INTEGER,
                is_whitelisted BOOLEAN DEFAULT 0,
                is_mutual_follow BOOLEAN DEFAULT 0,
                account_value_score REAL,
                unfollowed_date TEXT,
                unfollow_reason TEXT
            )
        ''')
        
        # Whitelist for protected accounts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS whitelist (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                display_name TEXT,
                reason TEXT,
                added_date TEXT,
                added_by TEXT,
                is_permanent BOOLEAN DEFAULT 1
            )
        ''')
        
        # Unfollow transaction log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unfollow_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                username TEXT,
                display_name TEXT,
                unfollowed_date TEXT,
                days_inactive INTEGER,
                follower_count INTEGER,
                last_tweet_date TEXT,
                unfollow_score INTEGER,
                reason TEXT,
                batch_id TEXT,
                can_rollback BOOLEAN DEFAULT 1
            )
        ''')
        
        # Activity check history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                check_date TEXT,
                last_tweet_date TEXT,
                days_inactive INTEGER,
                follower_count INTEGER,
                tweet_count INTEGER,
                api_rate_limit_remaining INTEGER
            )
        ''')
        
        # System configuration and stats
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_date TEXT
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_following_username ON following_status(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_following_inactive ON following_status(days_inactive)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_following_score ON following_status(unfollow_score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_whitelist_username ON whitelist(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_unfollow_date ON unfollow_log(unfollowed_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_checks(user_id)')
        
        self.conn.commit()
        print("📊 Database tables created/verified")
    
    def add_following_account(self, account_data: Dict) -> bool:
        """Add or update account in following_status table"""
        try:
            cursor = self.conn.cursor()
            
            # Prepare data with defaults
            data = {
                'user_id': account_data.get('id'),
                'username': account_data.get('username'),
                'display_name': account_data.get('name'),
                'bio': account_data.get('description'),
                'location': account_data.get('location'),
                'url': account_data.get('url'),
                'verified': account_data.get('verified', False),
                'protected': account_data.get('protected', False),
                'profile_image_url': account_data.get('profile_image_url'),
                'created_at': account_data.get('created_at'),
                'first_seen_date': datetime.now(timezone.utc).isoformat(),
                'last_checked_date': datetime.now(timezone.utc).isoformat()
            }
            
            # Add public metrics if available
            if 'public_metrics' in account_data:
                metrics = account_data['public_metrics']
                data.update({
                    'follower_count': metrics.get('followers_count', 0),
                    'following_count': metrics.get('following_count', 0),
                    'tweet_count': metrics.get('tweet_count', 0),
                    'listed_count': metrics.get('listed_count', 0),
                    'like_count': metrics.get('like_count', 0)
                })
            
            # Insert or update
            cursor.execute('''
                INSERT OR REPLACE INTO following_status 
                (user_id, username, display_name, bio, location, url, follower_count,
                 following_count, tweet_count, listed_count, like_count, verified,
                 protected, profile_image_url, created_at, first_seen_date, last_checked_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['user_id'], data['username'], data['display_name'], data['bio'],
                data['location'], data['url'], data.get('follower_count'),
                data.get('following_count'), data.get('tweet_count'), 
                data.get('listed_count'), data.get('like_count'), data['verified'],
                data['protected'], data['profile_image_url'], data['created_at'],
                data['first_seen_date'], data['last_checked_date']
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error adding account {account_data.get('username', 'unknown')}: {e}")
            return False
    
    def update_account_activity(self, user_id: str, activity_data: Dict) -> bool:
        """Update account activity information"""
        try:
            cursor = self.conn.cursor()
            
            # Calculate days inactive
            days_inactive = None
            if activity_data.get('last_tweet_date'):
                last_tweet = datetime.fromisoformat(activity_data['last_tweet_date'].replace('Z', '+00:00'))
                days_inactive = (datetime.now(timezone.utc) - last_tweet).days
            
            # Update activity data
            cursor.execute('''
                UPDATE following_status 
                SET last_tweet_id = ?, last_tweet_date = ?, last_tweet_text = ?,
                    days_inactive = ?, last_checked_date = ?, check_count = check_count + 1
                WHERE user_id = ?
            ''', (
                activity_data.get('last_tweet_id'),
                activity_data.get('last_tweet_date'),
                activity_data.get('last_tweet_text'),
                days_inactive,
                datetime.now(timezone.utc).isoformat(),
                user_id
            ))
            
            # Log activity check
            cursor.execute('''
                INSERT INTO activity_checks 
                (user_id, check_date, last_tweet_date, days_inactive, 
                 follower_count, tweet_count, api_rate_limit_remaining)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                datetime.now(timezone.utc).isoformat(),
                activity_data.get('last_tweet_date'),
                days_inactive,
                activity_data.get('follower_count'),
                activity_data.get('tweet_count'),
                activity_data.get('rate_limit_remaining')
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error updating activity for {user_id}: {e}")
            return False
    
    def calculate_unfollow_scores(self) -> int:
        """Calculate unfollow scores for all accounts"""
        cursor = self.conn.cursor()
        
        # Get all following accounts
        cursor.execute('''
            SELECT user_id, days_inactive, follower_count, verified, protected,
                   tweet_count, profile_image_url, is_whitelisted
            FROM following_status 
            WHERE unfollowed_date IS NULL
        ''')
        
        accounts = cursor.fetchall()
        updated_count = 0
        
        for account in accounts:
            score = self._calculate_unfollow_score(dict(account))
            
            cursor.execute('''
                UPDATE following_status 
                SET unfollow_score = ? 
                WHERE user_id = ?
            ''', (score, account['user_id']))
            
            updated_count += 1
        
        self.conn.commit()
        print(f"📊 Updated unfollow scores for {updated_count} accounts")
        return updated_count
    
    def _calculate_unfollow_score(self, account: Dict) -> int:
        """Calculate unfollow score for a single account"""
        score = 0
        
        # Skip whitelisted accounts
        if account.get('is_whitelisted'):
            return -1000  # Never unfollow
        
        # Days inactive (primary factor)
        days_inactive = account.get('days_inactive', 0)
        if days_inactive > 730:  # 2+ years
            score += 100
        elif days_inactive > 365:  # 1+ year
            score += 80
        elif days_inactive > 180:  # 6+ months
            score += 50
        elif days_inactive > 90:  # 3+ months
            score += 20
        
        # Follower count (influence factor)
        follower_count = account.get('follower_count', 0)
        if follower_count < 50:
            score += 30
        elif follower_count < 500:
            score += 15
        elif follower_count < 5000:
            score += 5
        elif follower_count > 100000:
            score -= 20
        elif follower_count > 1000000:
            score -= 50
        
        # Account quality indicators
        if account.get('verified'):
            score -= 40
        
        if account.get('protected'):
            score += 10  # Less valuable if private
        
        # Profile completeness
        if not account.get('profile_image_url') or 'default_profile' in str(account.get('profile_image_url', '')):
            score += 15
        
        # Tweet count (activity history)
        tweet_count = account.get('tweet_count', 0)
        if tweet_count < 10:
            score += 25
        elif tweet_count < 100:
            score += 10
        
        return max(0, score)  # Don't go negative (except whitelist)
    
    def get_unfollow_candidates(self, limit: int = 100, min_score: int = 50) -> List[Dict]:
        """Get accounts ranked for unfollowing"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM following_status 
            WHERE unfollowed_date IS NULL 
              AND is_whitelisted = 0
              AND unfollow_score >= ?
            ORDER BY unfollow_score DESC, days_inactive DESC
            LIMIT ?
        ''', (min_score, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def add_to_whitelist(self, user_id: str, username: str, reason: str) -> bool:
        """Add account to whitelist (never unfollow)"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO whitelist 
                (user_id, username, reason, added_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, reason, datetime.now(timezone.utc).isoformat()))
            
            # Update following_status
            cursor.execute('''
                UPDATE following_status 
                SET is_whitelisted = 1, unfollow_score = -1000
                WHERE user_id = ?
            ''', (user_id,))
            
            self.conn.commit()
            print(f"🛡️ Added @{username} to whitelist: {reason}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding to whitelist: {e}")
            return False
    
    def log_unfollow(self, account_data: Dict, reason: str, batch_id: str) -> bool:
        """Log an unfollow action"""
        try:
            cursor = self.conn.cursor()
            
            # Log the unfollow
            cursor.execute('''
                INSERT INTO unfollow_log 
                (user_id, username, display_name, unfollowed_date, days_inactive,
                 follower_count, last_tweet_date, unfollow_score, reason, batch_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                account_data['user_id'],
                account_data['username'],
                account_data['display_name'],
                datetime.now(timezone.utc).isoformat(),
                account_data.get('days_inactive'),
                account_data.get('follower_count'),
                account_data.get('last_tweet_date'),
                account_data.get('unfollow_score'),
                reason,
                batch_id
            ))
            
            # Update following_status
            cursor.execute('''
                UPDATE following_status 
                SET unfollowed_date = ?, unfollow_reason = ?
                WHERE user_id = ?
            ''', (
                datetime.now(timezone.utc).isoformat(),
                reason,
                account_data['user_id']
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error logging unfollow: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get comprehensive database statistics"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total following
        cursor.execute('SELECT COUNT(*) FROM following_status WHERE unfollowed_date IS NULL')
        stats['total_following'] = cursor.fetchone()[0]
        
        # Activity breakdown
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN days_inactive > 365 THEN 1 END) as dead_1year,
                COUNT(CASE WHEN days_inactive BETWEEN 180 AND 365 THEN 1 END) as inactive_6months,
                COUNT(CASE WHEN days_inactive BETWEEN 90 AND 180 THEN 1 END) as inactive_3months,
                COUNT(CASE WHEN days_inactive < 90 THEN 1 END) as active,
                COUNT(CASE WHEN days_inactive IS NULL THEN 1 END) as unchecked
            FROM following_status 
            WHERE unfollowed_date IS NULL
        ''')
        activity_stats = cursor.fetchone()
        stats.update(dict(activity_stats))
        
        # Unfollow candidates
        cursor.execute('''
            SELECT COUNT(*) FROM following_status 
            WHERE unfollowed_date IS NULL AND unfollow_score >= 50
        ''')
        stats['unfollow_candidates'] = cursor.fetchone()[0]
        
        # Whitelisted accounts
        cursor.execute('SELECT COUNT(*) FROM whitelist')
        stats['whitelisted_accounts'] = cursor.fetchone()[0]
        
        # Total unfollowed
        cursor.execute('SELECT COUNT(*) FROM unfollow_log')
        stats['total_unfollowed'] = cursor.fetchone()[0]
        
        # Recent activity
        cursor.execute('''
            SELECT COUNT(*) FROM activity_checks 
            WHERE check_date > datetime('now', '-1 day')
        ''')
        stats['checks_last_24h'] = cursor.fetchone()[0]
        
        return stats
    
    def export_data(self, table: str, filename: str = None) -> str:
        """Export table data to JSON"""
        if filename is None:
            filename = f"{table}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT * FROM {table}')
        
        data = [dict(row) for row in cursor.fetchall()]
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"📤 Exported {len(data)} records from {table} to {filename}")
        return filename
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()

def main():
    """Initialize or manage database"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Inactive Account Cleaner Database Manager')
    parser.add_argument('--init', action='store_true', help='Initialize database')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--export', type=str, help='Export table to JSON')
    parser.add_argument('--db', type=str, default='inactive_cleaner.db', help='Database file path')
    
    args = parser.parse_args()
    
    db = CleanerDatabase(args.db)
    
    if args.init:
        print("✅ Database initialized successfully")
    
    if args.stats:
        stats = db.get_statistics()
        print("\n📊 DATABASE STATISTICS")
        print("=" * 30)
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value:,}")
    
    if args.export:
        filename = db.export_data(args.export)
        print(f"📤 Data exported to {filename}")

if __name__ == "__main__":
    main()