# Twitter Followers Tracker

## Requirements

### Python Package Management
This project uses **uv** from Astral for Python package management instead of pip.

**uv** is an extremely fast Python package installer and resolver, written in Rust.
- Documentation: https://docs.astral.sh/uv/
- Install packages with: `uv add package_name`
- Run Python scripts with: `uv run script.py`
- Create virtual environments with: `uv venv`

### Dependencies
```bash
uv add tweepy python-dotenv
```

## Auth
All keys are saved in .env

## Important notes
in products_limits.json you can find rate limits for specific api endpoints

## Vision

⚠️ **IMPORTANT UPDATE**: After investigating X API documentation, we discovered that followers endpoints are **ONLY available to Enterprise tier customers** ($42,000/month), not free tier accounts.

### Original Vision (Requires Enterprise Tier)
We are building ultimate X (known previously as Twitter) followers tracker that will work as GitHub action. Our tracker will keep file of exact usernames of new followers and unfollows. We will keep it as .csv file commited by GH action to the same repo. This repo will be private. We will also have graph of follows and unfollows over  time which will be commited to the repo by the action run. 

### Current Status
- Free tier X API cannot access followers data (Enterprise tier only)
- **CRITICAL**: Free tier rate limits are **1 request per 24 hours** for user lookup
- This means we can only check metrics once per day maximum
- Alternative approaches needed or upgrade to higher tier required

### Actual Rate Limits (Free Tier)
- `GET /2/users/:id`: **1 request / 24 hours**
- This severely limits any meaningful tracking functionality
- Daily scheduled runs are the maximum frequency possible 

## Target User Configuration
- X id of the user we need to track: 1922977760680538112 
- Username: @nibzard
- These values are now configured in .env file as TARGET_USER_ID and TARGET_USERNAME

## API Specification
- Twitter API v2 OpenAPI specification saved in `openapi.json`
- Rate limits documented in `products_limits.json`