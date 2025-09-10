# ABOUTME: OAuth 2.0 authentication handler for X API user context access
# ABOUTME: Enables following list access and account management capabilities

import os
import json
import secrets
import hashlib
import base64
import webbrowser
import urllib.parse
from urllib.parse import urlencode, parse_qs, urlparse
from datetime import datetime, timezone
import requests
import tweepy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class XOAuthAuthenticator:
    """
    OAuth 2.0 authenticator for X API with PKCE support.
    Enables user context authentication for following list access and account management.
    """
    
    def __init__(self):
        """Initialize OAuth authenticator"""
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.redirect_uri = os.getenv('REDIRECT_URI', 'http://localhost:8080/callback')
        
        # OAuth endpoints
        self.auth_url = "https://twitter.com/i/oauth2/authorize"
        self.token_url = "https://api.twitter.com/2/oauth2/token"
        
        # Token storage
        self.token_file = '.oauth_tokens.json'
        
        if not self.client_id:
            raise ValueError("CLIENT_ID is required in environment variables")
            
        print("🔐 OAuth Authenticator initialized")
        print(f"📋 Client ID: {self.client_id[:8]}...")
        print(f"🔗 Redirect URI: {self.redirect_uri}")
    
    def generate_pkce_codes(self):
        """Generate PKCE code verifier and challenge for secure OAuth flow"""
        # Generate cryptographically secure random string
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Create SHA256 hash of verifier
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def build_authorization_url(self):
        """Build authorization URL with PKCE"""
        code_verifier, code_challenge = self.generate_pkce_codes()
        
        # Store code verifier for token exchange
        with open('.oauth_state.json', 'w') as f:
            json.dump({
                'code_verifier': code_verifier,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, f)
        
        # Required scopes for inactive account cleaner
        scopes = [
            'tweet.read',      # Read tweets to check activity
            'users.read',      # Read user profiles
            'follows.read',    # Read following list
            'follows.write'    # Unfollow accounts
        ]
        
        auth_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(scopes),
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'state': secrets.token_urlsafe(32)  # CSRF protection
        }
        
        auth_url = f"{self.auth_url}?{urlencode(auth_params)}"
        return auth_url
    
    def exchange_code_for_tokens(self, authorization_code):
        """Exchange authorization code for access tokens"""
        try:
            # Load PKCE code verifier
            with open('.oauth_state.json', 'r') as f:
                state = json.load(f)
                code_verifier = state['code_verifier']
            
            # Token exchange request
            token_data = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'redirect_uri': self.redirect_uri,
                'code_verifier': code_verifier,
                'client_id': self.client_id
            }
            
            # Add client secret if available (optional for PKCE)
            if self.client_secret:
                token_data['client_secret'] = self.client_secret
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'X-Inactive-Account-Cleaner-v1.0'
            }
            
            print("🔄 Exchanging authorization code for tokens...")
            response = requests.post(self.token_url, data=token_data, headers=headers)
            
            if response.status_code == 200:
                tokens = response.json()
                
                # Add metadata
                tokens['obtained_at'] = datetime.now(timezone.utc).isoformat()
                tokens['expires_at'] = None
                if 'expires_in' in tokens:
                    from datetime import timedelta
                    expires_at = datetime.now(timezone.utc) + timedelta(seconds=tokens['expires_in'])
                    tokens['expires_at'] = expires_at.isoformat()
                
                # Save tokens securely
                self.save_tokens(tokens)
                
                print("✅ OAuth tokens obtained successfully!")
                print(f"🔑 Access token: {tokens['access_token'][:20]}...")
                if 'refresh_token' in tokens:
                    print(f"🔄 Refresh token: {tokens['refresh_token'][:20]}...")
                
                return tokens
                
            else:
                error_data = response.json() if response.content else {}
                print(f"❌ Token exchange failed: {response.status_code}")
                print(f"Error: {error_data}")
                return None
                
        except Exception as e:
            print(f"❌ Exception during token exchange: {e}")
            return None
        finally:
            # Clean up state file
            if os.path.exists('.oauth_state.json'):
                os.remove('.oauth_state.json')
    
    def save_tokens(self, tokens):
        """Save OAuth tokens securely"""
        try:
            with open(self.token_file, 'w') as f:
                json.dump(tokens, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(self.token_file, 0o600)
            print(f"💾 Tokens saved to {self.token_file}")
            
        except Exception as e:
            print(f"❌ Error saving tokens: {e}")
    
    def load_tokens(self):
        """Load saved OAuth tokens"""
        try:
            if not os.path.exists(self.token_file):
                return None
                
            with open(self.token_file, 'r') as f:
                tokens = json.load(f)
            
            # Check if tokens are expired
            if 'expires_at' in tokens and tokens['expires_at']:
                expires_at = datetime.fromisoformat(tokens['expires_at'].replace('Z', '+00:00'))
                if datetime.now(timezone.utc) >= expires_at:
                    print("⚠️ Access token has expired")
                    return None
            
            return tokens
            
        except Exception as e:
            print(f"❌ Error loading tokens: {e}")
            return None
    
    def get_authenticated_client(self):
        """Get Tweepy client with user context authentication"""
        tokens = self.load_tokens()
        if not tokens:
            print("❌ No valid tokens found. Run OAuth flow first.")
            return None
        
        try:
            # Create Tweepy client with user context
            client = tweepy.Client(
                bearer_token=os.getenv('BEARER_TOKEN'),  # For app-only endpoints
                consumer_key=os.getenv('API_KEY'),
                consumer_secret=os.getenv('API_KEY_SECRET'),
                access_token=tokens['access_token'],
                access_token_secret=tokens.get('refresh_token', ''),  # OAuth 2.0 doesn't use token secret
                wait_on_rate_limit=True
            )
            
            print("✅ Authenticated Tweepy client created")
            return client
            
        except Exception as e:
            print(f"❌ Error creating authenticated client: {e}")
            return None
    
    def test_authentication(self):
        """Test OAuth authentication by accessing user context endpoints"""
        tokens = self.load_tokens()
        if not tokens:
            print("❌ No tokens available for testing")
            return False
        
        try:
            headers = {
                'Authorization': f"Bearer {tokens['access_token']}",
                'User-Agent': 'X-OAuth-Test'
            }
            
            # Test user context access
            print("🧪 Testing OAuth authentication...")
            
            # Test 1: Get authenticated user info
            response = requests.get(
                'https://api.twitter.com/2/users/me',
                headers=headers,
                params={'user.fields': 'public_metrics,verified'}
            )
            
            if response.status_code == 200:
                user_data = response.json()['data']
                print(f"✅ Authentication successful!")
                print(f"📊 Authenticated as: @{user_data['username']} ({user_data['name']})")
                print(f"👥 Followers: {user_data['public_metrics']['followers_count']:,}")
                print(f"➡️ Following: {user_data['public_metrics']['following_count']:,}")
                
                # Test 2: Check following access
                following_response = requests.get(
                    'https://api.twitter.com/2/users/me/following?max_results=5',
                    headers=headers
                )
                
                if following_response.status_code == 200:
                    following_data = following_response.json()
                    following_count = len(following_data.get('data', []))
                    print(f"✅ Following list access confirmed ({following_count} accounts in sample)")
                    return True
                else:
                    print(f"⚠️ Following list access issue: {following_response.status_code}")
                    print(following_response.text[:200])
                    return False
                    
            else:
                print(f"❌ Authentication test failed: {response.status_code}")
                print(response.text[:200])
                return False
                
        except Exception as e:
            print(f"❌ Authentication test error: {e}")
            return False
    
    def start_oauth_flow(self):
        """Start complete OAuth flow"""
        print("🚀 STARTING X OAUTH AUTHENTICATION FLOW")
        print("=" * 50)
        print("This will enable:")
        print("✅ Access to your following list")
        print("✅ Ability to unfollow inactive accounts")
        print("✅ Activity checking for any account")
        print("✅ Complete account management capabilities")
        print()
        
        # Build authorization URL
        auth_url = self.build_authorization_url()
        
        print("📋 AUTHORIZATION STEPS:")
        print("1. Your browser will open to X authorization page")
        print("2. Log in to X if needed")
        print("3. Review and authorize the application")
        print("4. Copy the callback URL from your browser")
        print("5. Paste it here when prompted")
        print()
        
        # Open browser
        print("🌐 Opening authorization URL in browser...")
        webbrowser.open(auth_url)
        
        print("\nIf browser doesn't open, visit this URL:")
        print(auth_url)
        print()
        
        # Wait for user to complete authorization
        try:
            callback_url = input("📎 Paste the complete callback URL here: ").strip()
            
            # Parse authorization code from callback URL
            parsed_url = urlparse(callback_url)
            params = parse_qs(parsed_url.query)
            
            if 'code' not in params:
                print("❌ No authorization code found in URL")
                if 'error' in params:
                    print(f"Authorization error: {params['error'][0]}")
                return False
            
            authorization_code = params['code'][0]
            print(f"✅ Authorization code received: {authorization_code[:20]}...")
            
            # Exchange code for tokens
            tokens = self.exchange_code_for_tokens(authorization_code)
            
            if tokens:
                print("\n🎉 OAuth setup completed successfully!")
                
                # Test authentication
                if self.test_authentication():
                    print("\n✅ Ready for inactive account cleaning!")
                    return True
                else:
                    print("\n⚠️ Authentication test failed")
                    return False
            else:
                print("\n❌ OAuth setup failed")
                return False
                
        except KeyboardInterrupt:
            print("\n👋 OAuth setup cancelled by user")
            return False
        except Exception as e:
            print(f"\n❌ OAuth setup error: {e}")
            return False

def main():
    """Main function for OAuth setup"""
    try:
        authenticator = XOAuthAuthenticator()
        
        # Check if already authenticated
        if authenticator.test_authentication():
            print("✅ Already authenticated! No setup needed.")
            
            # Ask if user wants to re-authenticate
            re_auth = input("\nRe-run OAuth setup anyway? (y/N): ").lower()
            if re_auth != 'y':
                print("👍 Using existing authentication")
                return
        
        # Run OAuth flow
        success = authenticator.start_oauth_flow()
        
        if success:
            print("\n🎯 NEXT STEPS:")
            print("1. Run the inactive account cleaner:")
            print("   uv run inactive_account_cleaner.py --dry-run")
            print()
            print("2. Check your following list:")
            print("   uv run following_analyzer.py")
            print()
            print("3. Set up whitelist for important accounts:")
            print("   uv run whitelist_manager.py")
        else:
            print("\n❌ OAuth setup failed. Please try again or check your credentials.")
            
    except Exception as e:
        print(f"💥 Fatal error: {e}")

if __name__ == "__main__":
    main()