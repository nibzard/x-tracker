# ABOUTME: Settings tab for configuration and system management
# ABOUTME: API credentials, database management, and system configuration

import gradio as gr
from typing import Dict, Any
from ...shared.config import config

def create_settings_tab(app) -> Dict[str, Any]:
    """Create settings tab for system configuration"""
    
    components = {}
    
    with gr.Column():
        gr.HTML("<h2>⚙️ System Settings</h2>")
        
        with gr.Tabs():
            with gr.Tab("API Configuration"):
                with gr.Group():
                    gr.HTML("<h3>🔐 API Credentials Status</h3>")
                    
                    # API Status display
                    api_status_html = f"""
                    <div class="metric-card">
                        <p><strong>Bearer Token:</strong> {'✅ Configured' if config.bearer_token else '❌ Not Set'}</p>
                        <p><strong>API Key:</strong> {'✅ Configured' if config.api_key else '❌ Not Set'}</p>
                        <p><strong>API Secret:</strong> {'✅ Configured' if config.api_key_secret else '❌ Not Set'}</p>
                        <p><strong>OAuth Tokens:</strong> {'✅ Configured' if config.validate_oauth_credentials() else '❌ Not Set'}</p>
                    </div>
                    """
                    gr.HTML(api_status_html)
                    
                    gr.HTML("""
                    <p><strong>Note:</strong> API credentials are loaded from environment variables (.env file).</p>
                    <p>To configure credentials, edit your .env file and restart the application.</p>
                    """)
                
            with gr.Tab("Database"):
                with gr.Group():
                    gr.HTML("<h3>🗄️ Database Information</h3>")
                    
                    # Database stats
                    try:
                        from ...infrastructure.database.connection import db
                        stats = db.get_stats()
                        
                        stats_html = "<div class='metric-card'>"
                        for table, count in stats.items():
                            stats_html += f"<p><strong>{table.replace('_', ' ').title()}:</strong> {count:,} records</p>"
                        stats_html += "</div>"
                        
                        gr.HTML(stats_html)
                        
                    except Exception as e:
                        gr.HTML(f"<span style='color: red;'>Error loading database stats: {e}</span>")
                
            with gr.Tab("System Info"):
                gr.HTML("🚧 System information features coming soon...")
    
    return components