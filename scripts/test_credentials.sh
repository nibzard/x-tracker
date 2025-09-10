#!/bin/bash

# ABOUTME: Simple script to test X API credentials without consuming daily rate limits
# ABOUTME: Uses tweet lookup endpoint which has 1 request per 15 minutes instead of per day

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if bearer token is set
if [ -z "$BEARER_TOKEN" ]; then
    echo "❌ BEARER_TOKEN not found in environment variables"
    echo "Make sure your .env file contains BEARER_TOKEN=your_token_here"
    exit 1
fi

echo "🔍 Testing X API credentials..."
echo "Using GET /2/tweets/:id endpoint (1 request per 15 minutes limit)"
echo "Testing with a known public tweet ID..."
echo ""

# Use Twitter's own announcement tweet about API v2 (a safe, public tweet)
TEST_TWEET_ID="1460323737035677698"

# Make the API call
echo "Making API request..."
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -H "User-Agent: X-API-Credentials-Test" \
  "https://api.twitter.com/2/tweets/${TEST_TWEET_ID}?tweet.fields=created_at,author_id,public_metrics")

# Extract HTTP status code
http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2)
response_body=$(echo "$response" | sed '/HTTP_STATUS:/d')

echo ""
echo "📊 Results:"
echo "HTTP Status: $http_status"
echo ""

case $http_status in
    200)
        echo "✅ SUCCESS! Your API credentials are valid"
        echo "📄 Response:"
        echo "$response_body" | jq . 2>/dev/null || echo "$response_body"
        echo ""
        echo "🎉 You can now proceed with the metrics tracking!"
        echo "⚠️  Remember: User lookup has only 1 request per 24 hours"
        ;;
    401)
        echo "❌ UNAUTHORIZED - Invalid bearer token"
        echo "Check your BEARER_TOKEN in .env file"
        echo "Response: $response_body"
        ;;
    403)
        echo "❌ FORBIDDEN - Access denied"
        echo "Your API key may not have sufficient permissions"
        echo "Response: $response_body"
        ;;
    429)
        echo "⚠️  RATE LIMITED - Too many requests"
        echo "Wait 15 minutes before testing again"
        echo "Response: $response_body"
        ;;
    *)
        echo "❌ UNEXPECTED ERROR (Status: $http_status)"
        echo "Response: $response_body"
        ;;
esac

echo ""
echo "Rate limit info:"
echo "- Tweet lookup: 1 request per 15 minutes ✅"
echo "- User lookup: 1 request per 24 hours ⚠️"
echo "- This test used the tweet lookup limit, not your daily user lookup limit"