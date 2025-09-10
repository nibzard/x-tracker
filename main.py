# ABOUTME: Main entry point for X-Tracker application
# ABOUTME: Command-line interface with options for web UI and direct operations

import typer
import os
import sys
from pathlib import Path
from typing import Optional

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.shared.config import config
from src.shared.logger import get_logger
from src.ui.app import launch_app

app = typer.Typer(
    name="x-tracker",
    help="🚀 X Growth Command Center - Professional X (Twitter) analytics and automation",
    rich_markup_mode="rich"
)

logger = get_logger(__name__)

@app.command("ui")
def launch_ui(
    host: Optional[str] = typer.Option(None, "--host", "-h", help="Host to bind to"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Port to bind to"),
    share: bool = typer.Option(False, "--share", help="Create shareable Gradio link"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode")
):
    """Launch the web UI interface"""
    
    typer.echo("🚀 Starting X Growth Command Center Web UI...")
    
    # Override config if provided
    if host:
        config.ui_host = host
    if port:
        config.ui_port = port
    
    typer.echo(f"📡 Server will start at: http://{config.ui_host}:{config.ui_port}")
    
    if not config.validate_api_credentials():
        typer.echo("⚠️  Warning: API credentials not configured", color=typer.colors.YELLOW)
        typer.echo("   The UI will work but some features will be disabled")
        typer.echo("   Configure credentials in .env file")
    
    launch_app(share=share, debug=debug)

@app.command("status")
def show_status():
    """Show system status and configuration"""
    
    typer.echo("📊 X-Tracker System Status", color=typer.colors.BRIGHT_BLUE)
    typer.echo("=" * 40)
    
    # API Status
    typer.echo("🔐 API Configuration:")
    typer.echo(f"   Bearer Token: {'✅ Set' if config.bearer_token else '❌ Missing'}")
    typer.echo(f"   API Key: {'✅ Set' if config.api_key else '❌ Missing'}")
    typer.echo(f"   API Secret: {'✅ Set' if config.api_key_secret else '❌ Missing'}")
    typer.echo(f"   OAuth: {'✅ Configured' if config.validate_oauth_credentials() else '❌ Not Set'}")
    
    # Database Status
    typer.echo(f"\n🗄️ Database: {config.database_path}")
    try:
        from src.infrastructure.database.connection import db
        stats = db.get_stats()
        total_records = sum(stats.values())
        typer.echo(f"   Status: ✅ Connected ({total_records:,} total records)")
        
        for table, count in stats.items():
            if count > 0:
                typer.echo(f"   {table}: {count:,} records")
    except Exception as e:
        typer.echo(f"   Status: ❌ Error - {e}", color=typer.colors.RED)
    
    # Target Configuration
    typer.echo(f"\n🎯 Target User:")
    typer.echo(f"   Username: @{config.target_username or 'Not Set'}")
    typer.echo(f"   User ID: {config.target_user_id or 'Not Set'}")
    
    # Paths
    typer.echo(f"\n📁 Paths:")
    typer.echo(f"   Data: {config.data_dir}")
    typer.echo(f"   Reports: {config.reports_dir}")
    typer.echo(f"   Logs: {config.logs_dir}")

@app.command("test")
def test_credentials():
    """Test API credentials and connectivity"""
    
    typer.echo("🧪 Testing API credentials...", color=typer.colors.BRIGHT_BLUE)
    
    if not config.validate_api_credentials():
        typer.echo("❌ Missing required API credentials", color=typer.colors.RED)
        typer.echo("Please configure BEARER_TOKEN, API_KEY, and API_KEY_SECRET in .env file")
        raise typer.Exit(1)
    
    try:
        from src.infrastructure.api.x_api_client import XAPIClient
        
        client = XAPIClient()
        typer.echo("✅ API client initialized successfully")
        
        # Test with a simple user lookup
        if config.target_user_id:
            user = client.get_user_by_id(config.target_user_id)
            typer.echo(f"✅ Successfully fetched user: @{user.username}")
            typer.echo(f"   Name: {user.name}")
            typer.echo(f"   Followers: {user.followers_count:,}")
            typer.echo(f"   Following: {user.following_count:,}")
        else:
            typer.echo("⚠️  Target user not configured, skipping user lookup test")
        
        # Test OAuth if available
        if config.validate_oauth_credentials():
            try:
                me = client.get_me()
                typer.echo(f"✅ OAuth working - authenticated as @{me.username}")
            except:
                typer.echo("⚠️  OAuth configured but test failed")
        
        typer.echo("\n🎉 All tests passed!", color=typer.colors.GREEN)
        
    except Exception as e:
        typer.echo(f"❌ API test failed: {e}", color=typer.colors.RED)
        raise typer.Exit(1)

@app.command("init")
def initialize():
    """Initialize X-Tracker with database setup"""
    
    typer.echo("🚀 Initializing X-Tracker...", color=typer.colors.BRIGHT_BLUE)
    
    # Create directories
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.reports_dir.mkdir(parents=True, exist_ok=True)
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize database
    try:
        from src.infrastructure.database.connection import db
        stats = db.get_stats()
        typer.echo(f"✅ Database initialized at {config.database_path}")
        typer.echo(f"   Total records: {sum(stats.values()):,}")
    except Exception as e:
        typer.echo(f"❌ Database initialization failed: {e}", color=typer.colors.RED)
        raise typer.Exit(1)
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        typer.echo("⚠️  No .env file found", color=typer.colors.YELLOW)
        typer.echo("   Create .env file with your API credentials:")
        typer.echo("   BEARER_TOKEN=your_bearer_token")
        typer.echo("   API_KEY=your_api_key")  
        typer.echo("   API_KEY_SECRET=your_api_secret")
        typer.echo("   TARGET_USER_ID=your_user_id")
        typer.echo("   TARGET_USERNAME=your_username")
    
    typer.echo("\n🎉 Initialization complete!", color=typer.colors.GREEN)
    typer.echo("Run 'python main.py ui' to launch the web interface")

if __name__ == "__main__":
    # Default to launching UI if no command specified
    if len(sys.argv) == 1:
        launch_ui()
    else:
        app()