# X Followers Tracker - Functional Specification

## 1. Overview

### 1.1 Purpose
The X Followers Tracker is an automated system that monitors follower changes for a specific X (formerly Twitter) account, maintaining historical records of followers and unfollowers with visual analytics.

### 1.2 Target Account
- **Configuration**: Specified via environment variables
- **User ID**: Loaded from `TARGET_USER_ID` env var
- **Username**: Loaded from `TARGET_USERNAME` env var

### 1.3 Core Functionality
- Track new followers and unfollowers daily
- Store follower data in CSV format
- Generate visual graphs of follower trends
- Operate within X API free tier rate limits
- Run automatically via GitHub Actions

## 2. System Architecture

### 2.1 Components
1. **Python Script** - Core tracking logic using Tweepy
2. **GitHub Action** - Scheduled automation
3. **CSV Storage** - Persistent data storage
4. **Visualization Module** - Graph generation
5. **Rate Limiter** - API call management

### 2.2 Data Flow
```
X API → Python Script → Data Processing → CSV Update → Graph Generation → Git Commit
```

## 3. Features

### 3.1 Follower Tracking
- **New Followers Detection**: Identify accounts that recently followed
- **Unfollower Detection**: Identify accounts that unfollowed
- **Username Recording**: Store exact usernames, not just IDs
- **Timestamp Recording**: Track when changes were detected

### 3.2 Data Storage
- **followers_history.csv**: Complete follower list snapshots
  - Columns: date, user_id, username, display_name
- **changes_log.csv**: Daily changes record
  - Columns: date, action (follow/unfollow), user_id, username, display_name
- **statistics.csv**: Aggregate statistics
  - Columns: date, total_followers, new_followers, unfollowers, net_change

### 3.3 Visualization
- **Follower Growth Chart**: Line graph showing total followers over time
- **Daily Changes Chart**: Bar chart showing daily gains/losses
- **Cumulative Change Chart**: Running total of net changes
- **Export Format**: PNG images committed to repository

### 3.4 Rate Limiting
- **Free Tier Compliance**: Strict adherence to X API v2 free tier limits
- **Endpoint Limits** (from products_limits.json):
  - GET /2/users/:id/followers: 15 requests per 15 minutes
  - Max 1000 followers per request
- **Smart Pagination**: Handle accounts with >1000 followers
- **Request Throttling**: Built-in delays to prevent rate limit violations

## 4. Technical Requirements

### 4.1 Dependencies
```python
tweepy>=4.14.0
pandas>=2.0.0
matplotlib>=3.7.0
python-dotenv>=1.0.0
```

### 4.1.1 ⚠️ CRITICAL: API Access Requirements
**IMPORTANT DISCOVERY**: The X API followers endpoints (`GET /2/users/:id/followers`) are **ONLY available to Enterprise tier customers**, not free tier accounts.

- **Free Tier**: Cannot access followers/following endpoints
- **Enterprise Tier**: Full access to followers data with higher rate limits
- **Authentication**: Requires OAuth 1.0a User Context or OAuth 2.0 for user data

**Impact on Project**: The original vision requires either:
1. Upgrading to Enterprise tier ($42,000/month)
2. Finding alternative approaches for follower tracking
3. Using different data sources or methods

### 4.2 Environment Variables (.env)
```
# X API Credentials
BEARER_TOKEN=<twitter_bearer_token>
API_KEY=<twitter_api_key>
API_KEY_SECRET=<twitter_api_key_secret>
ACCESS_TOKEN=<twitter_access_token>
ACCESS_TOKEN_SECRET=<twitter_access_token_secret>

# Target Account Configuration
TARGET_USER_ID=1922977760680538112
TARGET_USERNAME=nibzard
```

### 4.3 GitHub Action Configuration
```yaml
schedule:
  - cron: '0 12 * * *'  # Run daily at noon UTC
```

## 5. Implementation Details

### 5.1 Main Script Structure
```python
tracker.py
├── load_config()  # Load credentials + target user config
├── get_current_followers(user_id)
├── load_previous_followers()
├── detect_changes()
├── update_csv_files()
├── generate_graphs()
└── commit_changes()
```

### 5.2 Error Handling
- **API Failures**: Retry logic with exponential backoff
- **Rate Limit Exceeded**: Graceful degradation and scheduling
- **Data Corruption**: Backup and recovery mechanisms
- **Network Issues**: Timeout and retry strategies

### 5.3 Data Integrity
- **Atomic Operations**: Ensure complete updates or rollback
- **Backup Strategy**: Keep previous versions before updates
- **Validation**: Verify data consistency before commits
- **Deduplication**: Prevent duplicate entries

## 6. GitHub Action Workflow

### 6.1 Workflow Steps
1. **Checkout Repository**: Pull latest code and data
2. **Setup Python**: Configure Python environment
3. **Install Dependencies**: Install required packages
4. **Run Tracker**: Execute main tracking script
5. **Commit Changes**: Push updated CSVs and graphs
6. **Error Notification**: Alert on failures (optional)

### 6.2 Security
- **Secrets Management**: Use GitHub Secrets for API credentials and target user config
- **Private Repository**: Ensure repo remains private
- **Access Control**: Limited permissions for action token
- **Environment Variables**: All sensitive data and configuration via env vars

## 7. Output Specifications

### 7.1 CSV File Formats

**followers_history.csv**
```csv
date,user_id,username,display_name
2025-01-10,123456789,johndoe,John Doe
```

**changes_log.csv**
```csv
date,action,user_id,username,display_name
2025-01-10,follow,123456789,johndoe,John Doe
2025-01-10,unfollow,987654321,janedoe,Jane Doe
```

**statistics.csv**
```csv
date,total_followers,new_followers,unfollowers,net_change
2025-01-10,1500,10,5,5
```

### 7.2 Graph Specifications
- **Size**: 1200x600 pixels
- **Format**: PNG
- **Location**: `/graphs/` directory
- **Naming**: `followers_trend_YYYY-MM-DD.png`

## 8. Performance Targets

- **Execution Time**: < 5 minutes per run
- **Memory Usage**: < 512MB
- **API Calls**: < 15 per execution (rate limit compliance)
- **Storage Growth**: ~1MB per month (estimated)

## 9. Future Enhancements (Out of Scope for MVP)

- Multiple account tracking
- Real-time notifications
- Web dashboard
- Follower analytics (engagement, demographics)
- Automated reports
- Data export to external services

## 10. Success Criteria

- Successfully tracks followers daily without manual intervention
- Maintains accurate historical records
- Generates clear, readable visualizations
- Operates within X API free tier limits
- Commits changes automatically to GitHub repository
- Handles errors gracefully without data loss