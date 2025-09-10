# ABOUTME: Unified database connection and management for X-Tracker
# ABOUTME: Handles SQLite database operations, migrations, and connection pooling

import sqlite3
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from contextlib import contextmanager
from datetime import datetime, timezone

from ...shared.config import config
from ...shared.logger import get_logger
from ...core.exceptions import DatabaseError, ConnectionError, MigrationError

logger = get_logger(__name__)

class DatabaseConnection:
    """Thread-safe database connection manager"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection"""
        self.db_path = db_path or config.database_path
        self._local = threading.local()
        
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._initialize_database()
        
        logger.info(f"Database initialized: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection'):
            try:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
                conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
                self._local.connection = conn
                logger.debug("Created new database connection")
            except Exception as e:
                raise ConnectionError(f"Failed to connect to database: {e}")
        
        return self._local.connection
    
    @contextmanager
    def get_cursor(self):
        """Get database cursor with automatic commit/rollback"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction rolled back: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            cursor.close()
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a single query"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor
    
    def executemany(self, query: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """Execute query with multiple parameter sets"""
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Fetch single row"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Fetch all rows"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def _initialize_database(self):
        """Initialize database schema"""
        try:
            self._create_core_tables()
            self._create_analytics_tables()
            self._create_cleaner_tables()
            self._run_migrations()
            logger.info("Database schema initialized successfully")
        except Exception as e:
            raise MigrationError(f"Failed to initialize database schema: {e}")
    
    def _create_core_tables(self):
        """Create core application tables"""
        
        # Users table - unified user data
        self.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                name TEXT,
                bio TEXT,
                location TEXT,
                url TEXT,
                profile_image_url TEXT,
                created_at TEXT,
                followers_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                tweet_count INTEGER DEFAULT 0,
                listed_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                verified BOOLEAN DEFAULT 0,
                protected BOOLEAN DEFAULT 0,
                first_seen TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                UNIQUE(id, username)
            )
        ''')
        
        # Create indexes for better performance
        self.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        self.execute('CREATE INDEX IF NOT EXISTS idx_users_followers ON users(followers_count)')
        
    def _create_analytics_tables(self):
        """Create analytics and metrics tables"""
        
        # Metrics history - unified metrics tracking
        self.execute('''
            CREATE TABLE IF NOT EXISTS metrics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT NOT NULL,
                followers_count INTEGER,
                following_count INTEGER,
                tweet_count INTEGER,
                listed_count INTEGER,
                like_count INTEGER,
                followers_change INTEGER DEFAULT 0,
                following_change INTEGER DEFAULT 0,
                tweets_change INTEGER DEFAULT 0,
                follower_velocity REAL DEFAULT 0,
                engagement_rate REAL DEFAULT 0,
                growth_acceleration REAL DEFAULT 0,
                rate_limit_remaining INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Competitor tracking
        self.execute('''
            CREATE TABLE IF NOT EXISTS competitor_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT NOT NULL,
                growth_velocity REAL DEFAULT 0,
                engagement_estimate REAL DEFAULT 0,
                trend_direction TEXT DEFAULT 'stable',
                rank_position INTEGER,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Create indexes
        self.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics_history(timestamp)')
        self.execute('CREATE INDEX IF NOT EXISTS idx_metrics_user ON metrics_history(user_id)')
        self.execute('CREATE INDEX IF NOT EXISTS idx_competitor_timestamp ON competitor_tracking(timestamp)')
    
    def _create_cleaner_tables(self):
        """Create inactive account cleaner tables"""
        
        # Following status - enhanced tracking
        self.execute('''
            CREATE TABLE IF NOT EXISTS following_status (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                display_name TEXT,
                bio TEXT,
                location TEXT,
                url TEXT,
                follower_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                tweet_count INTEGER DEFAULT 0,
                listed_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                verified BOOLEAN DEFAULT 0,
                protected BOOLEAN DEFAULT 0,
                profile_image_url TEXT,
                created_at TEXT,
                last_tweet_id TEXT,
                last_tweet_date TEXT,
                last_tweet_text TEXT,
                days_inactive INTEGER,
                posting_frequency REAL,
                engagement_estimate REAL,
                first_seen_date TEXT NOT NULL,
                last_checked_date TEXT,
                check_count INTEGER DEFAULT 1,
                unfollow_score INTEGER DEFAULT 0,
                is_whitelisted BOOLEAN DEFAULT 0,
                is_mutual_follow BOOLEAN DEFAULT 0,
                account_value_score REAL DEFAULT 0,
                unfollowed_date TEXT,
                unfollow_reason TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Whitelist
        self.execute('''
            CREATE TABLE IF NOT EXISTS whitelist (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                display_name TEXT,
                reason TEXT NOT NULL,
                added_date TEXT NOT NULL,
                added_by TEXT DEFAULT 'system',
                is_permanent BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Unfollow log
        self.execute('''
            CREATE TABLE IF NOT EXISTS unfollow_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                display_name TEXT,
                unfollowed_date TEXT NOT NULL,
                days_inactive INTEGER,
                follower_count INTEGER DEFAULT 0,
                last_tweet_date TEXT,
                unfollow_score INTEGER DEFAULT 0,
                reason TEXT NOT NULL,
                batch_id TEXT,
                can_rollback BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Activity check history
        self.execute('''
            CREATE TABLE IF NOT EXISTS activity_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                check_date TEXT NOT NULL,
                last_tweet_date TEXT,
                tweets_found INTEGER DEFAULT 0,
                rate_limit_remaining INTEGER,
                check_successful BOOLEAN DEFAULT 1,
                error_message TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Create indexes for cleaner tables
        self.execute('CREATE INDEX IF NOT EXISTS idx_following_status_username ON following_status(username)')
        self.execute('CREATE INDEX IF NOT EXISTS idx_following_status_inactive ON following_status(days_inactive)')
        self.execute('CREATE INDEX IF NOT EXISTS idx_following_status_score ON following_status(unfollow_score)')
        self.execute('CREATE INDEX IF NOT EXISTS idx_whitelist_username ON whitelist(username)')
        self.execute('CREATE INDEX IF NOT EXISTS idx_unfollow_log_date ON unfollow_log(unfollowed_date)')
        self.execute('CREATE INDEX IF NOT EXISTS idx_activity_checks_date ON activity_checks(check_date)')
    
    def _run_migrations(self):
        """Run database migrations"""
        # Get current schema version
        try:
            version_row = self.fetch_one("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            current_version = version_row[0] if version_row else 0
        except:
            # Create schema_version table if it doesn't exist
            self.execute('''
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_date TEXT NOT NULL,
                    description TEXT
                )
            ''')
            current_version = 0
        
        # Apply migrations
        migrations = self._get_migrations()
        
        for version, migration in migrations.items():
            if version > current_version:
                logger.info(f"Applying migration {version}: {migration['description']}")
                try:
                    # Execute each statement separately
                    for statement in migration['statements']:
                        self.execute(statement)
                    
                    self.execute('''
                        INSERT INTO schema_version (version, applied_date, description)
                        VALUES (?, ?, ?)
                    ''', (version, datetime.now(timezone.utc).isoformat(), migration['description']))
                    logger.info(f"Migration {version} applied successfully")
                except Exception as e:
                    raise MigrationError(f"Failed to apply migration {version}: {e}")
    
    def _get_migrations(self) -> Dict[int, Dict[str, Any]]:
        """Get database migrations"""
        return {
            1: {
                'description': 'Add indexes for performance optimization',
                'statements': [
                    'CREATE INDEX IF NOT EXISTS idx_users_last_updated ON users(last_updated)',
                    'CREATE INDEX IF NOT EXISTS idx_metrics_user_timestamp ON metrics_history(user_id, timestamp)'
                ]
            },
            2: {
                'description': 'Add application configuration table',
                'statements': [
                    '''CREATE TABLE IF NOT EXISTS app_config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_date TEXT NOT NULL
                    )'''
                ]
            }
        }
    
    def close(self):
        """Close database connections"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')
    
    def backup(self, backup_path: str):
        """Create database backup"""
        try:
            with sqlite3.connect(backup_path) as backup_conn:
                self._get_connection().backup(backup_conn)
            logger.info(f"Database backed up to {backup_path}")
        except Exception as e:
            raise DatabaseError(f"Failed to backup database: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        stats = {}
        
        tables = [
            'users', 'metrics_history', 'competitor_tracking',
            'following_status', 'whitelist', 'unfollow_log', 'activity_checks'
        ]
        
        for table in tables:
            try:
                count_row = self.fetch_one(f"SELECT COUNT(*) FROM {table}")
                stats[table] = count_row[0] if count_row else 0
            except:
                stats[table] = 0
        
        return stats

# Global database instance
db = DatabaseConnection()