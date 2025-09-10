# ABOUTME: X Competitor Intelligence System using app-only authentication
# ABOUTME: Tracks competitors and analyzes content performance with current API access

import os
import sqlite3
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class XCompetitorTracker:
    """
    X Competitor Intelligence System that works with current app-only authentication.
    Tracks competitors using GET /2/users/by/username (3 requests per 15 minutes).
    """
    
    def __init__(self):
        self.bearer_token = os.getenv('BEARER_TOKEN')
        if not self.bearer_token:
            raise ValueError("BEARER_TOKEN is required")
        
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "X-Competitor-Intelligence-v1.0"
        }
        
        # Default competitors list (you can customize this)
        self.competitors = [
            "elonmusk",       # High-profile tech figure
            "sundarpichai",   # Google CEO
            "satyanadella",   # Microsoft CEO 
            "tim_cook",       # Apple CEO
            "jeffweiner08",   # LinkedIn
            "richardbranson"  # Virgin Group
        ]
        
        self.init_database()
        print("🕵️ X Competitor Intelligence System initialized!")
        print(f"📊 Tracking {len(self.competitors)} competitors")
        print("🔑 Using app-only auth (3 requests per 15 minutes)")
    
    def init_database(self):
        """Initialize SQLite database"""
        self.conn = sqlite3.connect('competitor_intelligence.db')
        cursor = self.conn.cursor()
        
        # Competitor metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitor_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                username TEXT NOT NULL,
                user_id TEXT,
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
                created_at TEXT,
                profile_image_url TEXT,
                rate_limit_remaining INTEGER,
                UNIQUE(timestamp, username)
            )
        ''')
        
        # Competitor analysis table (derived insights)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitor_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                username TEXT NOT NULL,
                period_hours INTEGER,
                followers_change INTEGER,
                following_change INTEGER,
                tweets_change INTEGER,
                follower_velocity REAL,
                engagement_estimate REAL,
                growth_rank INTEGER,
                UNIQUE(timestamp, username)
            )
        ''')
        
        # Content analysis table for tweet performance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                tweet_id TEXT NOT NULL,
                author_username TEXT,
                content TEXT,
                created_at TEXT,
                retweet_count INTEGER,
                reply_count INTEGER,
                like_count INTEGER,
                quote_count INTEGER,
                bookmark_count INTEGER,
                impression_count INTEGER,
                engagement_rate REAL,
                viral_score REAL,
                UNIQUE(tweet_id)
            )
        ''')
        
        self.conn.commit()
        print("🗄️ Competitor intelligence database initialized")
    
    def track_competitor(self, username: str) -> Optional[Dict]:
        """Track a single competitor using /users/by/username endpoint"""
        url = f"{self.base_url}/users/by/username/{username}"
        params = {
            "user.fields": "created_at,description,location,name,pinned_tweet_id,"
                          "profile_image_url,protected,public_metrics,url,username,"
                          "verified,verified_type"
        }
        
        try:
            print(f"🔍 Tracking @{username}...")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            # Rate limit tracking
            remaining = response.headers.get('x-rate-limit-remaining', 'Unknown')
            limit = response.headers.get('x-rate-limit-limit', 'Unknown')
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('data', {})
                public_metrics = user_data.get('public_metrics', {})
                
                metrics = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'username': user_data.get('username', username),
                    'user_id': user_data.get('id'),
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
                    'created_at': user_data.get('created_at'),
                    'profile_image_url': user_data.get('profile_image_url'),
                    'rate_limit_remaining': remaining
                }
                
                print(f"   ✅ @{username}: {public_metrics.get('followers_count', 0):,} followers")
                print(f"      Rate limit: {remaining}/{limit}")
                
                return metrics
                
            elif response.status_code == 429:
                print(f"   ⚠️ Rate limited for @{username}")
                return None
                
            elif response.status_code == 404:
                print(f"   ❌ User @{username} not found")
                return None
                
            else:
                print(f"   ❌ Error {response.status_code}: {response.text[:100]}")
                return None
                
        except Exception as e:
            print(f"   💥 Exception tracking @{username}: {e}")
            return None
    
    def save_competitor_metrics(self, metrics: Dict) -> bool:
        """Save competitor metrics to database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO competitor_metrics 
                (timestamp, username, user_id, name, description, location, url,
                 verified, protected, followers_count, following_count, tweet_count,
                 listed_count, like_count, created_at, profile_image_url, rate_limit_remaining)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics['timestamp'], metrics['username'], metrics['user_id'],
                metrics['name'], metrics['description'], metrics['location'],
                metrics['url'], metrics['verified'], metrics['protected'],
                metrics['followers_count'], metrics['following_count'],
                metrics['tweet_count'], metrics['listed_count'], metrics['like_count'],
                metrics['created_at'], metrics['profile_image_url'], 
                metrics['rate_limit_remaining']
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error saving metrics for {metrics['username']}: {e}")
            return False
    
    def analyze_competitor_growth(self) -> List[Dict]:
        """Analyze competitor growth patterns"""
        try:
            cursor = self.conn.cursor()
            
            # Get growth analysis for each competitor
            growth_data = []
            
            for competitor in self.competitors:
                # Get last two measurements for this competitor
                cursor.execute('''
                    SELECT * FROM competitor_metrics 
                    WHERE username = ?
                    ORDER BY timestamp DESC 
                    LIMIT 2
                ''', (competitor,))
                
                rows = cursor.fetchall()
                if len(rows) < 2:
                    continue
                
                current = rows[0]
                previous = rows[1]
                
                # Calculate time difference
                current_time = datetime.fromisoformat(current[1].replace('Z', '+00:00'))
                previous_time = datetime.fromisoformat(previous[1].replace('Z', '+00:00'))
                time_diff = current_time - previous_time
                period_hours = time_diff.total_seconds() / 3600
                
                # Calculate changes
                followers_change = current[10] - previous[10]  # followers_count
                following_change = current[11] - previous[11]  # following_count
                tweets_change = current[12] - previous[12]     # tweet_count
                
                # Calculate velocity
                follower_velocity = (followers_change / period_hours) if period_hours > 0 else 0
                
                # Estimate engagement (rough calculation)
                engagement_estimate = 0
                if current[10] > 0:  # followers_count
                    engagement_estimate = ((tweets_change * 100) / current[10]) * 100
                
                analysis = {
                    'timestamp': current[1],
                    'username': competitor,
                    'period_hours': period_hours,
                    'followers_change': followers_change,
                    'following_change': following_change,
                    'tweets_change': tweets_change,
                    'follower_velocity': follower_velocity,
                    'engagement_estimate': engagement_estimate,
                    'current_followers': current[10],
                    'growth_rank': 0  # Will calculate below
                }
                
                growth_data.append(analysis)
            
            # Rank competitors by follower velocity
            growth_data.sort(key=lambda x: x['follower_velocity'], reverse=True)
            for i, data in enumerate(growth_data):
                data['growth_rank'] = i + 1
            
            return growth_data
            
        except Exception as e:
            print(f"❌ Error analyzing competitor growth: {e}")
            return []
    
    def generate_intelligence_report(self) -> str:
        """Generate competitor intelligence report"""
        try:
            cursor = self.conn.cursor()
            
            # Get latest metrics for all competitors
            cursor.execute('''
                SELECT DISTINCT username, 
                       MAX(timestamp) as latest_timestamp
                FROM competitor_metrics 
                GROUP BY username
            ''')
            
            latest_data = []
            for row in cursor.fetchall():
                cursor.execute('''
                    SELECT * FROM competitor_metrics 
                    WHERE username = ? AND timestamp = ?
                ''', (row[0], row[1]))
                latest_data.append(cursor.fetchone())
            
            # Generate growth analysis
            growth_analysis = self.analyze_competitor_growth()
            
            report = []
            report.append("# 🕵️ COMPETITOR INTELLIGENCE REPORT")
            report.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
            report.append("")
            
            # Current standings
            report.append("## 📊 CURRENT STANDINGS")
            report.append("")
            
            # Sort by followers
            latest_data.sort(key=lambda x: x[10], reverse=True)  # followers_count
            
            for i, competitor in enumerate(latest_data):
                if competitor:
                    username = competitor[2]
                    followers = competitor[10]
                    following = competitor[11]
                    tweets = competitor[12]
                    verified = "✅" if competitor[8] else "❌"
                    
                    report.append(f"### #{i+1} @{username}")
                    report.append(f"- **Followers**: {followers:,}")
                    report.append(f"- **Following**: {following:,}")
                    report.append(f"- **Tweets**: {tweets:,}")
                    report.append(f"- **Verified**: {verified}")
                    report.append("")
            
            # Growth velocity rankings
            if growth_analysis:
                report.append("## 🚀 GROWTH VELOCITY RANKINGS")
                report.append("")
                
                for analysis in growth_analysis:
                    velocity = analysis['follower_velocity']
                    change = analysis['followers_change']
                    username = analysis['username']
                    
                    report.append(f"### #{analysis['growth_rank']} @{username}")
                    report.append(f"- **Velocity**: {velocity:.1f} followers/hour")
                    report.append(f"- **Recent change**: {change:+,} followers")
                    report.append(f"- **Period**: {analysis['period_hours']:.1f} hours")
                    report.append("")
            
            # Key insights
            report.append("## 💡 KEY INSIGHTS")
            report.append("")
            
            if growth_analysis:
                fastest_growing = growth_analysis[0]
                report.append(f"🏆 **Fastest Growing**: @{fastest_growing['username']} ({fastest_growing['follower_velocity']:.1f}/hour)")
                
                most_active = max(growth_analysis, key=lambda x: x['tweets_change'])
                report.append(f"📝 **Most Active**: @{most_active['username']} ({most_active['tweets_change']:+} tweets)")
                
                # Calculate average metrics
                avg_velocity = sum(a['follower_velocity'] for a in growth_analysis) / len(growth_analysis)
                report.append(f"📈 **Average Growth**: {avg_velocity:.1f} followers/hour")
            
            return "\n".join(report)
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
            return "Error generating report"
    
    def run_competitor_tracking_cycle(self):
        """Run a complete competitor tracking cycle"""
        print("🕵️ X COMPETITOR INTELLIGENCE - TRACKING CYCLE")
        print("="*60)
        print(f"🕐 Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"🎯 Tracking {len(self.competitors)} competitors")
        print("⚡ Using app-only auth (works now, no OAuth needed)")
        print()
        
        successful_tracks = 0
        
        for i, competitor in enumerate(self.competitors):
            print(f"[{i+1}/{len(self.competitors)}] ", end="")
            
            metrics = self.track_competitor(competitor)
            if metrics:
                if self.save_competitor_metrics(metrics):
                    successful_tracks += 1
                    
            # Rate limiting: 3 requests per 15 minutes
            # Add small delay between requests
            if i < len(self.competitors) - 1:
                print("     ⏳ Waiting 5 seconds...")
                import time
                time.sleep(5)
        
        print(f"\n📊 Tracking Results: {successful_tracks}/{len(self.competitors)} successful")
        
        # Generate analysis
        if successful_tracks > 0:
            print("\n📈 Generating intelligence analysis...")
            growth_analysis = self.analyze_competitor_growth()
            
            if growth_analysis:
                print("\n🏆 TOP PERFORMERS:")
                for analysis in growth_analysis[:3]:
                    print(f"   #{analysis['growth_rank']} @{analysis['username']}: "
                          f"{analysis['follower_velocity']:.1f} followers/hour "
                          f"({analysis['followers_change']:+,})")
            
            # Save report
            report = self.generate_intelligence_report()
            with open('competitor_intelligence_report.md', 'w') as f:
                f.write(report)
            print("📋 Detailed report saved to competitor_intelligence_report.md")
        
        print("\n✅ Competitor tracking cycle completed!")
        return successful_tracks > 0
    
    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    """Main function"""
    try:
        tracker = XCompetitorTracker()
        success = tracker.run_competitor_tracking_cycle()
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n👋 Competitor tracking interrupted by user")
        exit(0)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main()