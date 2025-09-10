# ABOUTME: Generate visualization charts from X metrics tracking data
# ABOUTME: Creates graphs showing follower growth, engagement trends, and profile changes

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timezone
import json
import os
from typing import Optional

class MetricsVisualizer:
    """
    Creates visualizations from X metrics tracking data.
    Designed to work with limited data points (1 measurement per day max).
    """
    
    def __init__(self, csv_file: str = "metrics_history.csv"):
        """Initialize with CSV data file"""
        self.csv_file = csv_file
        self.df = None
        
        if not os.path.exists(csv_file):
            print(f"❌ CSV file not found: {csv_file}")
            return
        
        try:
            self.df = pd.read_csv(csv_file)
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            self.df.set_index('timestamp', inplace=True)
            print(f"✅ Loaded {len(self.df)} measurements from {csv_file}")
        except Exception as e:
            print(f"❌ Error loading CSV file: {e}")
    
    def create_follower_growth_chart(self, output_file: str = "follower_growth.png"):
        """Create follower growth chart over time"""
        if self.df is None or len(self.df) < 2:
            print("⚠️  Need at least 2 data points to create growth chart")
            return False
        
        try:
            plt.figure(figsize=(12, 6))
            
            # Main followers line
            plt.plot(self.df.index, self.df['followers_count'], 
                    marker='o', linewidth=2, markersize=6, 
                    color='#1DA1F2', label='Followers')
            
            # Fill area under the curve
            plt.fill_between(self.df.index, self.df['followers_count'], 
                           alpha=0.3, color='#1DA1F2')
            
            # Customize the chart
            plt.title(f'Follower Growth - @{self.df["username"].iloc[-1]}', 
                     fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Follower Count', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Format x-axis dates
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(self.df)//10)))
            plt.xticks(rotation=45)
            
            # Add annotations for first and last values
            first_val = self.df['followers_count'].iloc[0]
            last_val = self.df['followers_count'].iloc[-1]
            change = last_val - first_val
            
            plt.annotate(f'Start: {first_val:,}', 
                        xy=(self.df.index[0], first_val), 
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
            
            plt.annotate(f'Latest: {last_val:,} ({change:+,})', 
                        xy=(self.df.index[-1], last_val), 
                        xytext=(-10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7))
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Follower growth chart saved to {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating follower growth chart: {e}")
            return False
    
    def create_metrics_dashboard(self, output_file: str = "metrics_dashboard.png"):
        """Create comprehensive metrics dashboard"""
        if self.df is None or len(self.df) < 2:
            print("⚠️  Need at least 2 data points to create dashboard")
            return False
        
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # 1. Followers over time
            ax1.plot(self.df.index, self.df['followers_count'], 
                    marker='o', color='#1DA1F2', linewidth=2)
            ax1.set_title('Followers Over Time', fontweight='bold')
            ax1.set_ylabel('Followers')
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # 2. Following over time
            ax2.plot(self.df.index, self.df['following_count'], 
                    marker='s', color='#17BF63', linewidth=2)
            ax2.set_title('Following Over Time', fontweight='bold')
            ax2.set_ylabel('Following')
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            
            # 3. Tweet count over time
            ax3.plot(self.df.index, self.df['tweet_count'], 
                    marker='^', color='#E1306C', linewidth=2)
            ax3.set_title('Tweet Count Over Time', fontweight='bold')
            ax3.set_ylabel('Total Tweets')
            ax3.grid(True, alpha=0.3)
            ax3.tick_params(axis='x', rotation=45)
            
            # 4. Listed count over time
            ax4.plot(self.df.index, self.df['listed_count'], 
                    marker='d', color='#FFAD1F', linewidth=2)
            ax4.set_title('Listed Count Over Time', fontweight='bold')
            ax4.set_ylabel('Times Listed')
            ax4.grid(True, alpha=0.3)
            ax4.tick_params(axis='x', rotation=45)
            
            # Overall title
            username = self.df['username'].iloc[-1]
            fig.suptitle(f'X Metrics Dashboard - @{username}', 
                        fontsize=16, fontweight='bold', y=0.98)
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Metrics dashboard saved to {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating metrics dashboard: {e}")
            return False
    
    def create_daily_changes_chart(self, output_file: str = "daily_changes.png", days: int = 30):
        """Create chart showing daily changes in follower count"""
        if self.df is None or len(self.df) < 2:
            print("⚠️  Need at least 2 data points to show changes")
            return False
        
        try:
            # Calculate daily changes
            df_changes = self.df.copy()
            df_changes['followers_change'] = df_changes['followers_count'].diff()
            df_changes['following_change'] = df_changes['following_count'].diff()
            df_changes['tweets_change'] = df_changes['tweet_count'].diff()
            
            # Remove first row (NaN) and limit to recent days
            df_changes = df_changes.dropna().tail(days)
            
            if len(df_changes) == 0:
                print("⚠️  No change data available")
                return False
            
            plt.figure(figsize=(12, 8))
            
            # Plot daily changes
            plt.subplot(3, 1, 1)
            colors = ['green' if x >= 0 else 'red' for x in df_changes['followers_change']]
            plt.bar(df_changes.index, df_changes['followers_change'], color=colors, alpha=0.7)
            plt.title('Daily Follower Changes', fontweight='bold')
            plt.ylabel('Change')
            plt.grid(True, alpha=0.3)
            plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            plt.subplot(3, 1, 2)
            colors = ['green' if x >= 0 else 'red' for x in df_changes['following_change']]
            plt.bar(df_changes.index, df_changes['following_change'], color=colors, alpha=0.7)
            plt.title('Daily Following Changes', fontweight='bold')
            plt.ylabel('Change')
            plt.grid(True, alpha=0.3)
            plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            plt.subplot(3, 1, 3)
            colors = ['blue' if x >= 0 else 'orange' for x in df_changes['tweets_change']]
            plt.bar(df_changes.index, df_changes['tweets_change'], color=colors, alpha=0.7)
            plt.title('Daily Tweet Changes', fontweight='bold')
            plt.ylabel('Change')
            plt.xlabel('Date')
            plt.grid(True, alpha=0.3)
            plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            # Format x-axis
            for ax in plt.gcf().axes:
                ax.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Daily changes chart saved to {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating daily changes chart: {e}")
            return False
    
    def generate_summary_stats(self) -> Optional[dict]:
        """Generate summary statistics from the data"""
        if self.df is None or len(self.df) == 0:
            return None
        
        try:
            latest = self.df.iloc[-1]
            earliest = self.df.iloc[0]
            
            stats = {
                'tracking_period_days': (self.df.index[-1] - self.df.index[0]).days,
                'total_measurements': len(self.df),
                'latest_followers': int(latest['followers_count']),
                'latest_following': int(latest['following_count']),
                'latest_tweets': int(latest['tweet_count']),
                'latest_listed': int(latest['listed_count']),
                'follower_growth': int(latest['followers_count'] - earliest['followers_count']),
                'following_growth': int(latest['following_count'] - earliest['following_count']),
                'tweets_growth': int(latest['tweet_count'] - earliest['tweet_count']),
                'avg_daily_follower_growth': 0 if len(self.df) < 2 else 
                    (latest['followers_count'] - earliest['followers_count']) / max(1, (self.df.index[-1] - self.df.index[0]).days),
                'username': latest['username'],
                'name': latest['name'],
                'verified': bool(latest['verified']),
                'protected': bool(latest['protected']),
                'first_measurement': earliest.name.isoformat(),
                'latest_measurement': latest.name.isoformat()
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Error generating summary stats: {e}")
            return None
    
    def generate_all_charts(self):
        """Generate all available charts"""
        print("="*60)
        print("GENERATING X METRICS VISUALIZATIONS")
        print("="*60)
        
        if self.df is None:
            print("❌ No data available for visualization")
            return False
        
        print(f"Data points: {len(self.df)}")
        print(f"Date range: {self.df.index[0].strftime('%Y-%m-%d')} to {self.df.index[-1].strftime('%Y-%m-%d')}")
        print()
        
        success_count = 0
        
        # Generate charts
        charts = [
            (self.create_follower_growth_chart, "Follower Growth Chart"),
            (self.create_metrics_dashboard, "Metrics Dashboard"),
            (self.create_daily_changes_chart, "Daily Changes Chart")
        ]
        
        for chart_func, chart_name in charts:
            print(f"Generating {chart_name}...")
            if chart_func():
                success_count += 1
            print()
        
        # Generate summary stats
        print("Generating summary statistics...")
        stats = self.generate_summary_stats()
        if stats:
            with open('metrics_summary.json', 'w') as f:
                json.dump(stats, f, indent=2)
            print("✅ Summary statistics saved to metrics_summary.json")
            
            # Print key stats
            print("\n" + "="*40)
            print("SUMMARY STATISTICS")
            print("="*40)
            print(f"Account: @{stats['username']} ({stats['name']})")
            print(f"Tracking period: {stats['tracking_period_days']} days")
            print(f"Current followers: {stats['latest_followers']:,}")
            print(f"Follower growth: {stats['follower_growth']:+,}")
            print(f"Average daily growth: {stats['avg_daily_follower_growth']:.1f}")
            print(f"Total tweets: {stats['latest_tweets']:,}")
            success_count += 1
        
        print(f"\n✅ Generated {success_count} visualizations successfully")
        return success_count > 0

def main():
    """Main function"""
    visualizer = MetricsVisualizer()
    visualizer.generate_all_charts()

if __name__ == "__main__":
    main()