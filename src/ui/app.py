# ABOUTME: Main Gradio web application for X-Tracker
# ABOUTME: Professional dashboard with tabs for analytics, cleaner, and settings

import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional
import asyncio
import threading

from ..shared.config import config
from ..shared.logger import get_logger
from ..infrastructure.database.connection import db
from ..infrastructure.api.x_api_client import XAPIClient
from .components.charts import create_growth_chart, create_competitor_chart, create_metrics_summary
from .pages.dashboard import create_dashboard_tab
from .pages.analytics import create_analytics_tab  
from .pages.cleaner import create_cleaner_tab
from .pages.settings import create_settings_tab

logger = get_logger(__name__)

class XTrackerApp:
    """Main X-Tracker Gradio application"""
    
    def __init__(self):
        """Initialize the application"""
        self.api_client = None
        self.setup_api_client()
        
        logger.info("X-Tracker web app initialized")
    
    def setup_api_client(self):
        """Setup API client if credentials are available"""
        try:
            if config.validate_api_credentials():
                self.api_client = XAPIClient()
                logger.info("API client initialized successfully")
            else:
                logger.warning("API credentials not configured")
        except Exception as e:
            logger.error(f"Failed to initialize API client: {e}")
    
    def get_system_status(self) -> Dict:
        """Get overall system status"""
        status = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'api_configured': self.api_client is not None,
            'database_connected': True,  # We assume DB is working if we got this far
            'oauth_configured': config.validate_oauth_credentials()
        }
        
        # Database stats
        try:
            status['database_stats'] = db.get_stats()
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            status['database_stats'] = {}
        
        # Rate limit status
        if self.api_client:
            try:
                status['rate_limits'] = self.api_client.get_rate_limit_status()
            except Exception as e:
                logger.error(f"Failed to get rate limit status: {e}")
                status['rate_limits'] = {}
        
        return status
    
    def create_app(self) -> gr.Blocks:
        """Create and configure the Gradio app"""
        
        # Custom CSS for professional styling
        css = """
        .gradio-container {
            max-width: 1200px !important;
        }
        .status-good {
            color: #22c55e !important;
            font-weight: bold;
        }
        .status-warning {
            color: #f59e0b !important;
            font-weight: bold;
        }
        .status-error {
            color: #ef4444 !important;
            font-weight: bold;
        }
        .metric-card {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
        }
        .big-number {
            font-size: 2rem;
            font-weight: bold;
            color: #1f2937;
        }
        """
        
        with gr.Blocks(
            title="🚀 X Growth Command Center",
            theme=gr.themes.Soft(),
            css=css
        ) as app:
            
            # Header
            gr.HTML("""
            <div style="text-align: center; padding: 20px 0;">
                <h1>🚀 X Growth Command Center</h1>
                <p style="color: #666; font-size: 1.1em;">
                    Professional X (Twitter) analytics, growth intelligence & automated account management
                </p>
            </div>
            """)
            
            # Quick status bar
            with gr.Row():
                api_status = gr.HTML(label="API Status")
                db_status = gr.HTML(label="Database")
                oauth_status = gr.HTML(label="OAuth")
            
            # Main tabs
            with gr.Tabs():
                
                # Dashboard Tab
                with gr.Tab("📊 Dashboard", id="dashboard"):
                    dashboard_components = create_dashboard_tab(self)
                
                # Analytics Tab  
                with gr.Tab("📈 Analytics", id="analytics"):
                    analytics_components = create_analytics_tab(self)
                
                # Cleaner Tab
                with gr.Tab("🧹 Cleaner", id="cleaner"):
                    cleaner_components = create_cleaner_tab(self)
                
                # Settings Tab
                with gr.Tab("⚙️ Settings", id="settings"):
                    settings_components = create_settings_tab(self)
            
            # Auto-refresh status
            def update_status():
                """Update system status display"""
                status = self.get_system_status()
                
                # API Status
                if status['api_configured']:
                    api_html = '<span class="status-good">✅ API Connected</span>'
                else:
                    api_html = '<span class="status-error">❌ API Not Configured</span>'
                
                # Database Status  
                total_records = sum(status.get('database_stats', {}).values())
                db_html = f'<span class="status-good">✅ Database ({total_records:,} records)</span>'
                
                # OAuth Status
                if status['oauth_configured']:
                    oauth_html = '<span class="status-good">✅ OAuth Enabled</span>'
                else:
                    oauth_html = '<span class="status-warning">⚠️ OAuth Not Configured</span>'
                
                return api_html, db_html, oauth_html
            
            # Update status on load and every 30 seconds
            app.load(update_status, outputs=[api_status, db_status, oauth_status])
            
            # Auto-refresh timer (every 30 seconds)
            timer = gr.Timer(value=30)
            timer.tick(update_status, outputs=[api_status, db_status, oauth_status])
        
        return app
    
    def launch(self, share: bool = False, debug: bool = False):
        """Launch the application"""
        app = self.create_app()
        
        logger.info(f"Launching X-Tracker web app on {config.ui_host}:{config.ui_port}")
        
        app.launch(
            server_name=config.ui_host,
            server_port=config.ui_port,
            share=share,
            debug=debug or config.debug,
            show_error=True,
            quiet=False,
            favicon_path=None,  # Could add a favicon later
            auth=None,  # Could add authentication later
        )

# Convenience function for direct launch
def launch_app(share: bool = False, debug: bool = False):
    """Launch X-Tracker web application"""
    app = XTrackerApp()
    app.launch(share=share, debug=debug)

if __name__ == "__main__":
    launch_app(debug=True)