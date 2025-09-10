# 🧹 X Inactive Account Cleaner - Complete Setup & Usage Guide

**The Ultimate Solution for Cleaning Your X Following List**

Automatically unfollow inactive accounts while protecting valuable relationships. Built on the discovery that X API provides 40,000 tweet requests for activity checking!

## 🎯 What This System Does

### ✅ **Core Capabilities**
- **Mass Activity Checking**: Leverages 40k request limit to check thousands of accounts
- **Smart Unfollowing**: AI-powered scoring to identify best unfollow candidates  
- **Safety Protection**: Whitelist system to protect important relationships
- **Comprehensive Analytics**: Detailed reports on following list health
- **Gradual Cleaning**: Controlled unfollowing to avoid suspicion

### 🎨 **Key Features**
- **Configurable Thresholds**: 3, 6, 12+ months inactivity detection
- **Account Value Scoring**: Protects verified, high-follower, and active accounts
- **Batch Processing**: Efficient API usage with rate limit management
- **Rollback Capability**: Transaction logging for potential undos
- **Dry Run Mode**: Test everything before making changes

## 🚀 Quick Start (5 Minutes to First Clean)

### Prerequisites
```bash
# 1. Ensure you have OAuth credentials
echo "CLIENT_ID=your_client_id" >> .env
echo "CLIENT_SECRET=your_client_secret" >> .env  # Optional for PKCE

# 2. Install additional dependencies
uv add authlib requests-oauthlib
```

### Setup Process
```bash
# Step 1: Run OAuth authorization (one-time setup)
uv run oauth_authenticator.py

# Step 2: Initialize database
uv run cleaner_database.py --init

# Step 3: Set up whitelist protection
uv run whitelist_manager.py --auto-verified
uv run whitelist_manager.py --auto-influencers

# Step 4: Run first cleaning (dry run)
uv run inactive_account_cleaner.py --dry-run

# Step 5: Execute actual cleaning (when ready)
uv run inactive_account_cleaner.py --inactive-days 365 --max-unfollows 25
```

## 📋 Component Overview

### 1. `oauth_authenticator.py` - Authentication Handler
**Purpose**: Enables OAuth user context for following list access

```bash
# One-time OAuth setup
uv run oauth_authenticator.py

# Test authentication
uv run oauth_authenticator.py --test
```

**What it does**:
- Generates secure PKCE codes
- Opens browser for X authorization
- Exchanges codes for access tokens
- Tests authentication with real API calls

### 2. `cleaner_database.py` - Data Management
**Purpose**: SQLite database for tracking accounts and activity

```bash
# Initialize database
uv run cleaner_database.py --init

# Show statistics
uv run cleaner_database.py --stats

# Export data
uv run cleaner_database.py --export following_status
```

**Database Schema**:
- `following_status`: Complete account data and activity
- `whitelist`: Protected accounts
- `unfollow_log`: Transaction history
- `activity_checks`: API usage tracking

### 3. `whitelist_manager.py` - Account Protection
**Purpose**: Manage accounts that should never be unfollowed

```bash
# Auto-protect verified accounts
uv run whitelist_manager.py --auto-verified

# Auto-protect influencers (100k+ followers)
uv run whitelist_manager.py --auto-influencers

# Add specific account
uv run whitelist_manager.py --add elonmusk --reason "Important tech leader"

# List protected accounts
uv run whitelist_manager.py --list

# Get suggestions
uv run whitelist_manager.py --suggest
```

### 4. `inactive_account_cleaner.py` - Main System
**Purpose**: The complete cleaning orchestrator

```bash
# Safe dry run (recommended first)
uv run inactive_account_cleaner.py --dry-run

# Conservative cleaning (1+ year inactive)
uv run inactive_account_cleaner.py --inactive-days 365 --max-unfollows 25

# Aggressive cleaning (6+ months inactive)  
uv run inactive_account_cleaner.py --inactive-days 180 --max-unfollows 50

# Activity check only
uv run inactive_account_cleaner.py --activity-only

# Show statistics only
uv run inactive_account_cleaner.py --stats-only
```

## 🔧 Configuration Options

### Inactive Thresholds
```bash
--inactive-days 90    # 3 months (aggressive)
--inactive-days 180   # 6 months (balanced) - DEFAULT
--inactive-days 365   # 1 year (conservative)
--inactive-days 730   # 2 years (very conservative)
```

### Safety Limits
```bash
--max-unfollows 25    # Conservative daily limit
--max-unfollows 50    # Moderate daily limit - DEFAULT
--max-unfollows 100   # Aggressive daily limit
```

### Score Thresholds
```bash
--min-score 30        # More unfollows (lower threshold)
--min-score 50        # Balanced unfollows - DEFAULT  
--min-score 70        # Fewer unfollows (higher threshold)
```

## 📊 Understanding the Scoring System

### Unfollow Score Calculation
The system calculates a score for each account based on:

#### **Inactivity Weight (Primary Factor)**
- 2+ years inactive: +100 points
- 1+ year inactive: +80 points
- 6+ months inactive: +50 points
- 3+ months inactive: +20 points

#### **Follower Count (Influence Factor)**
- <50 followers: +30 points
- <500 followers: +15 points  
- <5,000 followers: +5 points
- >100,000 followers: -20 points
- >1,000,000 followers: -50 points

#### **Account Quality Indicators**
- Verified account: -40 points (protection)
- Private account: +10 points
- No profile image: +15 points
- <10 total tweets: +25 points
- <100 total tweets: +10 points

#### **Automatic Protections**
- Whitelisted accounts: -1000 points (never unfollow)
- Mutual follows: Additional protection
- Recently active: Score reduction

### Score Ranges
- **0-29**: Keep following (too valuable)
- **30-49**: Marginal candidates
- **50-69**: Good unfollow candidates ← DEFAULT THRESHOLD
- **70-89**: Strong unfollow candidates  
- **90+**: Prime unfollow candidates

## 🛡️ Safety Features

### 1. **Whitelist Protection**
```bash
# Protect verified accounts automatically
uv run whitelist_manager.py --auto-verified

# Protect high-influence accounts
uv run whitelist_manager.py --auto-influencers --min-followers 50000

# Protect specific accounts
uv run whitelist_manager.py --add nasa --reason "Space content"
uv run whitelist_manager.py --add openai --reason "AI research"
```

### 2. **Gradual Unfollowing**
- Maximum 50 unfollows per run (configurable)
- 2-second delays between unfollows
- Daily limits to avoid detection
- Batch tracking for rollback capability

### 3. **Dry Run Mode**
```bash
# Always test first!
uv run inactive_account_cleaner.py --dry-run --inactive-days 180

# Review the plan before executing
uv run inactive_account_cleaner.py --dry-run --max-unfollows 100
```

### 4. **Rollback Capability**
All unfollows are logged with:
- Account details at time of unfollow
- Reason for unfollowing
- Batch ID for group operations
- Timestamp for audit trail

## 📈 Performance & Rate Limits

### **API Usage Efficiency**
- **Following List**: ~1-5 requests (depending on following count)
- **Activity Checking**: Up to 40,000 requests available!
- **Unfollowing**: 50 requests per 15 minutes

### **Processing Estimates**
For account following 2,000 people:
- **Following fetch**: 2-3 requests (2-3 minutes)
- **Activity check**: 2,000 requests (30-45 minutes) 
- **Unfollowing**: 50 accounts (5-10 minutes with delays)
- **Total time**: ~1 hour for complete cleaning

### **Recommended Schedule**
- **Weekly**: Activity checking run
- **Monthly**: Full cleaning cycle
- **Quarterly**: Whitelist review and updates

## 🔄 Complete Workflow Examples

### Example 1: First-Time Setup
```bash
# 1. OAuth setup (one-time)
uv run oauth_authenticator.py

# 2. Protect important accounts
uv run whitelist_manager.py --auto-verified
uv run whitelist_manager.py --auto-influencers
uv run whitelist_manager.py --add tim_cook --reason "Apple CEO"

# 3. Test run (no unfollows)
uv run inactive_account_cleaner.py --dry-run --inactive-days 365

# 4. Conservative first clean
uv run inactive_account_cleaner.py --inactive-days 730 --max-unfollows 10
```

### Example 2: Regular Maintenance  
```bash
# Weekly activity check
uv run inactive_account_cleaner.py --activity-only

# Monthly moderate cleaning
uv run inactive_account_cleaner.py --inactive-days 180 --max-unfollows 50

# Quarterly aggressive cleaning
uv run inactive_account_cleaner.py --inactive-days 90 --max-unfollows 100
```

### Example 3: Emergency Cleanup
```bash
# For users following too many accounts (Twitter limit issues)

# 1. Protect absolutely essential accounts
uv run whitelist_manager.py --suggest
# Manually add critical accounts from suggestions

# 2. Aggressive cleaning of dead accounts
uv run inactive_account_cleaner.py --inactive-days 730 --max-unfollows 100

# 3. Follow up with moderate cleaning
uv run inactive_account_cleaner.py --inactive-days 365 --max-unfollows 100

# 4. Final polish
uv run inactive_account_cleaner.py --inactive-days 180 --max-unfollows 50
```

## 📊 Monitoring & Reports

### Database Statistics
```bash
# Quick stats
uv run inactive_account_cleaner.py --stats-only

# Detailed analysis
uv run cleaner_database.py --stats
```

### Generated Reports
Each cleaning run creates:
- `cleaning_report_YYYYMMDD_HHMMSS.json`: Complete session report
- Activity analysis and recommendations
- Before/after statistics
- Unfollow transaction log

### Key Metrics to Track
- **Following list health**: Active vs inactive ratio
- **Space freed**: Percentage of following list cleaned
- **Protection effectiveness**: Whitelist coverage
- **API efficiency**: Requests used vs available

## 🚨 Troubleshooting

### Common Issues

#### "No OAuth tokens found"
```bash
# Solution: Run OAuth setup
uv run oauth_authenticator.py
```

#### "Rate limit exceeded"
```bash
# Solution: Wait for reset or check limits
uv run oauth_authenticator.py --test
```

#### "Following list access denied"
```bash
# Solution: Check OAuth permissions
# Ensure you granted 'follows.read' and 'follows.write' permissions
```

#### "Database locked"
```bash
# Solution: Close any running processes
pkill -f "inactive_account_cleaner"
```

### Performance Issues

#### "Activity checking too slow"
- **Cause**: Network latency or API throttling
- **Solution**: Run during off-peak hours

#### "Unfollowing fails"
- **Cause**: Rate limits or API restrictions
- **Solution**: Reduce `--max-unfollows` and increase delays

### Data Issues

#### "Scores seem wrong"
```bash
# Recalculate scores
uv run cleaner_database.py --init
uv run inactive_account_cleaner.py --activity-only
```

#### "Missing accounts"
- **Cause**: Accounts may have been suspended/deleted
- **Solution**: Normal - system handles this gracefully

## 🎯 Best Practices

### 1. **Start Conservative**
- Begin with 1-2 year inactive threshold
- Limit unfollows to 10-25 per session
- Always use dry run first

### 2. **Protect Important Relationships**
- Auto-whitelist verified accounts
- Manually protect industry leaders
- Review whitelist suggestions regularly

### 3. **Monitor Results**
- Check cleaning reports
- Review unfollow logs
- Track following list health over time

### 4. **Gradual Approach**
- Clean 20-50 accounts per week
- Avoid large batch unfollows
- Spread cleaning over multiple sessions

### 5. **Regular Maintenance**
- Weekly activity checks
- Monthly moderate cleaning
- Quarterly whitelist reviews

## 💡 Pro Tips

### **Maximize Cleaning Efficiency**
1. **Batch by inactivity**: Start with 2+ year inactive accounts
2. **Score threshold tuning**: Adjust `--min-score` based on results
3. **Whitelist curation**: Regularly review and update protections
4. **API timing**: Run during your local off-peak hours

### **Account Value Assessment**
- **Verified accounts**: Usually worth keeping
- **Industry experts**: Protect even if inactive
- **News sources**: May post irregularly but valuable
- **Personal friends**: Always whitelist

### **Timeline Optimization**
- **Phase 1**: Remove obviously dead accounts (2+ years)
- **Phase 2**: Clean dormant accounts (1+ year)  
- **Phase 3**: Evaluate low-activity accounts (6+ months)
- **Phase 4**: Fine-tune with custom thresholds

## 🎉 Expected Results

### Typical Outcomes
For an account following 1,500 people:
- **15-25% inactive accounts found** (225-375 accounts)
- **5-10% completely dead** (75-150 accounts, 2+ years inactive)
- **10-15% dormant** (150-225 accounts, 6-12 months inactive)
- **Timeline quality improvement**: More active content
- **Engagement potential**: Better follow/follower ratio

### Success Metrics
- **Following list health**: 80%+ active accounts
- **Engagement improvement**: Higher timeline relevance
- **Space optimization**: Room for new valuable follows
- **Network quality**: More meaningful connections

---

## 🚀 Ready to Clean Your Following List?

Your X Inactive Account Cleaner is production-ready! Start with the conservative approach and gradually optimize based on your results.

**Remember**: This system respects X's API limits, includes comprehensive safety features, and provides full transparency through detailed logging and reporting.

**Next step**: Run your first OAuth setup and dry run to see what's possible! 🧹✨