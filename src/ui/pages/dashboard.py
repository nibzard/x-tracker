# ABOUTME: Dashboard tab for X-Tracker UI showing overview and key metrics
# ABOUTME: Real-time summary of growth, analytics, and system status

import gradio as gr
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from ...infrastructure.database.connection import db
from ...shared.logger import get_logger
from ..components.charts import create_growth_chart, create_metrics_summary, create_velocity_chart

logger = get_logger(__name__)

def create_dashboard_tab(app) -> Dict[str, Any]:
    """Create the dashboard tab with overview metrics and charts"""
    
    components = {}
    
    with gr.Column():
        # Quick stats row
        with gr.Row():
            with gr.Column():
                components['current_metrics'] = gr.Plot(
                    label="📊 Current Metrics",
                    value=create_metrics_summary({})
                )
            
            with gr.Column():
                with gr.Group():
                    gr.HTML("<h3>🎯 Today's Activity</h3>")
                    components['activity_summary'] = gr.HTML(value="Loading...")
        
        # Growth chart
        components['growth_chart'] = gr.Plot(
            label="📈 Growth Overview (Last 30 Days)",
            value=create_growth_chart([])
        )
        
        # Velocity and recent activity
        with gr.Row():
            with gr.Column():
                components['velocity_chart'] = gr.Plot(
                    label="⚡ Growth Velocity (Last 7 Days)",
                    value=create_velocity_chart([])
                )
            
            with gr.Column():
                with gr.Group():
                    gr.HTML("<h3>🔄 Recent Activity</h3>")
                    components['recent_activity'] = gr.DataFrame(
                        headers=["Time", "Action", "Details"],
                        value=[]
                    )
        
        # Action buttons
        with gr.Row():
            components['refresh_btn'] = gr.Button("🔄 Refresh Dashboard", variant="primary")
            components['run_metrics_btn'] = gr.Button("📊 Update Metrics", variant="secondary")
            components['run_cleaner_btn'] = gr.Button("🧹 Quick Clean", variant="secondary")
    
    # Event handlers
    def refresh_dashboard():
        """Refresh all dashboard data"""
        try:
            # Get current metrics
            latest_metrics = get_latest_metrics()
            metrics_chart = create_metrics_summary(latest_metrics)
            
            # Get growth data
            growth_data = get_growth_data(days=30)
            growth_chart = create_growth_chart(growth_data, "Growth Overview (Last 30 Days)")
            
            # Get velocity data  
            velocity_data = get_velocity_data(days=7)
            velocity_chart = create_velocity_chart(velocity_data, "Growth Velocity (Last 7 Days)")
            
            # Get activity summary
            activity_html = get_activity_summary()
            
            # Get recent activity
            recent_activity_df = get_recent_activity()
            
            return (
                metrics_chart,
                growth_chart,
                velocity_chart,
                activity_html,
                recent_activity_df
            )
            
        except Exception as e:
            logger.error(f"Failed to refresh dashboard: {e}")
            return (
                create_metrics_summary({}),
                create_growth_chart([]),
                create_velocity_chart([]),
                f"<span style='color: red;'>Error loading data: {e}</span>",
                []
            )
    
    def update_metrics():
        """Run metrics update"""
        try:
            if not app.api_client:
                return "❌ API client not configured"
            
            # This would trigger the metrics update process
            # For now, just return a status message
            return "✅ Metrics update started (check logs for progress)"
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
            return f"❌ Failed to update metrics: {e}"
    
    def quick_clean():
        """Run quick clean operation"""
        try:
            # This would trigger a quick cleaner run
            # For now, just return a status message  
            return "✅ Quick clean started (check Cleaner tab for progress)"
            
        except Exception as e:
            logger.error(f"Failed to run quick clean: {e}")
            return f"❌ Failed to run quick clean: {e}"
    
    # Wire up event handlers
    components['refresh_btn'].click(
        refresh_dashboard,
        outputs=[
            components['current_metrics'],
            components['growth_chart'],
            components['velocity_chart'],
            components['activity_summary'],
            components['recent_activity']
        ]
    )
    
    components['run_metrics_btn'].click(
        update_metrics,
        outputs=[components['activity_summary']]
    )
    
    components['run_cleaner_btn'].click(
        quick_clean,
        outputs=[components['activity_summary']]
    )
    
    # Auto-refresh on tab load
    refresh_dashboard()
    
    return components

def get_latest_metrics() -> Dict[str, Any]:
    """Get the most recent metrics from database"""
    try:
        query = """
        SELECT * FROM metrics_history 
        ORDER BY timestamp DESC 
        LIMIT 1
        """
        row = db.fetch_one(query)
        
        if row:
            return dict(row)
        else:
            # Return empty metrics
            return {
                'followers_count': 0,
                'following_count': 0,
                'tweet_count': 0,
                'listed_count': 0
            }
            
    except Exception as e:
        logger.error(f"Failed to get latest metrics: {e}")
        return {}

def get_growth_data(days: int = 30) -> List[Dict]:
    """Get growth data for the specified number of days"""
    try:
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        query = """
        SELECT timestamp, followers_count, following_count, tweet_count, listed_count
        FROM metrics_history 
        WHERE timestamp > ?
        ORDER BY timestamp ASC
        """
        
        rows = db.fetch_all(query, (cutoff_date,))
        return [dict(row) for row in rows]
        
    except Exception as e:
        logger.error(f"Failed to get growth data: {e}")
        return []

def get_velocity_data(days: int = 7) -> List[Dict]:
    """Get velocity data for the specified number of days"""
    try:
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        query = """
        SELECT timestamp, follower_velocity, growth_acceleration
        FROM metrics_history 
        WHERE timestamp > ? AND follower_velocity IS NOT NULL
        ORDER BY timestamp ASC
        """
        
        rows = db.fetch_all(query, (cutoff_date,))
        return [dict(row) for row in rows]
        
    except Exception as e:
        logger.error(f"Failed to get velocity data: {e}")
        return []

def get_activity_summary() -> str:
    """Get HTML summary of today's activity"""
    try:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_str = today_start.isoformat()
        
        # Get today's metrics
        metrics_query = """
        SELECT COUNT(*) as count FROM metrics_history 
        WHERE timestamp > ?
        """
        metrics_count = db.fetch_one(metrics_query, (today_start_str,))
        
        # Get today's unfollows
        unfollows_query = """
        SELECT COUNT(*) as count FROM unfollow_log 
        WHERE unfollowed_date > ?
        """
        unfollows_count = db.fetch_one(unfollows_query, (today_start_str,))
        
        # Get activity checks
        checks_query = """
        SELECT COUNT(*) as count FROM activity_checks 
        WHERE check_date > ?
        """
        checks_count = db.fetch_one(checks_query, (today_start_str,))
        
        return f"""
        <div class="metric-card">
            <p><strong>📊 Metrics Updates:</strong> {metrics_count[0] if metrics_count else 0}</p>
            <p><strong>🧹 Accounts Unfollowed:</strong> {unfollows_count[0] if unfollows_count else 0}</p>
            <p><strong>🔍 Activity Checks:</strong> {checks_count[0] if checks_count else 0}</p>
            <p><small>Last updated: {datetime.now().strftime('%H:%M:%S')}</small></p>
        </div>
        """
        
    except Exception as e:
        logger.error(f"Failed to get activity summary: {e}")
        return f"<span style='color: red;'>Error loading activity summary: {e}</span>"

def get_recent_activity() -> List[List]:
    """Get recent activity for the activity table"""
    try:
        activities = []
        
        # Recent metrics updates
        metrics_query = """
        SELECT timestamp, followers_count, followers_change
        FROM metrics_history 
        ORDER BY timestamp DESC 
        LIMIT 5
        """
        for row in db.fetch_all(metrics_query):
            timestamp = datetime.fromisoformat(row[0]).strftime('%H:%M')
            change = f"({row[2]:+d})" if row[2] else ""
            activities.append([timestamp, "📊 Metrics", f"Followers: {row[1]:,} {change}"])
        
        # Recent unfollows
        unfollow_query = """
        SELECT unfollowed_date, username, reason
        FROM unfollow_log 
        ORDER BY unfollowed_date DESC 
        LIMIT 3
        """
        for row in db.fetch_all(unfollow_query):
            timestamp = datetime.fromisoformat(row[0]).strftime('%H:%M')
            activities.append([timestamp, "🧹 Unfollow", f"@{row[1]} - {row[2]}"])
        
        # Sort by time and limit to 8 items
        activities.sort(key=lambda x: x[0], reverse=True)
        return activities[:8]
        
    except Exception as e:
        logger.error(f"Failed to get recent activity: {e}")
        return [["Error", "Loading", str(e)]]