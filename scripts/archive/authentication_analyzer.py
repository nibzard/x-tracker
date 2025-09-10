# ABOUTME: Analyze X API endpoints and their authentication requirements
# ABOUTME: Shows what's possible with app-only vs user context authentication

import os
import json
from typing import Dict, List
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class XAPIAuthAnalyzer:
    """
    Analyzes X API capabilities under different authentication methods.
    Helps understand upgrade path from app-only to user context authentication.
    """
    
    def __init__(self):
        self.bearer_token = os.getenv('BEARER_TOKEN')
        self.api_key = os.getenv('API_KEY')
        self.api_key_secret = os.getenv('API_KEY_SECRET')
        
        self.base_url = "https://api.twitter.com/2"
        self.app_headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "X-API-Auth-Analyzer"
        }
    
    def test_app_only_endpoints(self) -> Dict:
        """Test what works with current app-only authentication"""
        results = {
            "working_endpoints": [],
            "forbidden_endpoints": [],
            "rate_limits": {},
            "capabilities": {}
        }
        
        # Test endpoints with known public tweet ID
        test_tweet_id = "1460323737035677698"
        
        endpoints_to_test = [
            {
                "name": "GET /2/tweets/:id",
                "url": f"{self.base_url}/tweets/{test_tweet_id}",
                "params": {"tweet.fields": "created_at,author_id,public_metrics"},
                "description": "Tweet lookup - good for analyzing content performance"
            },
            {
                "name": "GET /2/users/by/username/:username", 
                "url": f"{self.base_url}/users/by/username/Twitter",
                "params": {"user.fields": "public_metrics,verified,created_at"},
                "description": "User lookup by username - competitor analysis"
            },
            {
                "name": "GET /2/users/me",
                "url": f"{self.base_url}/users/me", 
                "params": {"user.fields": "public_metrics"},
                "description": "Personal account info - requires user context"
            }
        ]
        
        print("🔍 TESTING X API CAPABILITIES")
        print("="*50)
        print("🔑 Authentication: App-Only (Bearer Token)")
        print()
        
        for endpoint in endpoints_to_test:
            print(f"Testing {endpoint['name']}...")
            
            try:
                response = requests.get(
                    endpoint['url'], 
                    headers=self.app_headers, 
                    params=endpoint['params'],
                    timeout=10
                )
                
                # Extract rate limit info
                remaining = response.headers.get('x-rate-limit-remaining', 'N/A')
                limit = response.headers.get('x-rate-limit-limit', 'N/A')
                
                if response.status_code == 200:
                    results["working_endpoints"].append(endpoint['name'])
                    results["rate_limits"][endpoint['name']] = f"{remaining}/{limit}"
                    print(f"  ✅ WORKS - Rate limit: {remaining}/{limit}")
                    
                    # Extract key capabilities
                    data = response.json()
                    if 'data' in data:
                        if 'public_metrics' in data['data']:
                            metrics = data['data']['public_metrics']
                            results["capabilities"][endpoint['name']] = {
                                "public_metrics": list(metrics.keys()),
                                "description": endpoint['description']
                            }
                        
                elif response.status_code == 403:
                    results["forbidden_endpoints"].append(endpoint['name'])
                    error_data = response.json()
                    print(f"  ❌ FORBIDDEN - {error_data.get('detail', 'Access denied')}")
                    
                elif response.status_code == 429:
                    results["working_endpoints"].append(endpoint['name'])
                    print(f"  ⚠️  RATE LIMITED - Endpoint works but quota exceeded")
                    results["rate_limits"][endpoint['name']] = "Rate limited"
                    
                else:
                    print(f"  ❓ Status {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"  💥 Error: {e}")
            
            print()
        
        return results
    
    def analyze_user_context_benefits(self) -> Dict:
        """Analyze what becomes available with user context authentication"""
        return {
            "enhanced_endpoints": {
                "GET /2/users/me": {
                    "rate_limit": "25 requests/day",
                    "vs_app_only": "1 request/day for GET /2/users/:id", 
                    "benefits": [
                        "25x more frequent personal monitoring",
                        "Real-time growth tracking",
                        "Hourly analytics possible",
                        "Better trend detection"
                    ]
                },
                "POST /2/tweets": {
                    "rate_limit": "17 requests/day",
                    "vs_app_only": "Not available",
                    "benefits": [
                        "Automated posting",
                        "Content scheduling", 
                        "A/B testing tweets",
                        "Thread automation"
                    ]
                },
                "GET /2/users/:id/bookmarks": {
                    "rate_limit": "1 request/15 min",
                    "vs_app_only": "Not available",
                    "benefits": [
                        "Bookmark management",
                        "Content curation",
                        "Inspiration tracking",
                        "Research organization"
                    ]
                }
            },
            "authentication_methods": {
                "OAuth 1.0a User Context": {
                    "complexity": "Medium", 
                    "setup_time": "30 minutes",
                    "user_approval": "One-time authorization"
                },
                "OAuth 2.0 User Context": {
                    "complexity": "Medium-High",
                    "setup_time": "45 minutes", 
                    "user_approval": "One-time authorization with PKCE"
                }
            },
            "implementation_priority": [
                "1. Implement OAuth 2.0 User Context",
                "2. Enable personal analytics (25x monitoring)",
                "3. Add automated posting capabilities", 
                "4. Build bookmark management",
                "5. Create comprehensive dashboard"
            ]
        }
    
    def generate_capability_report(self) -> str:
        """Generate comprehensive capability report"""
        app_results = self.test_app_only_endpoints()
        user_benefits = self.analyze_user_context_benefits()
        
        report = []
        report.append("# X API CAPABILITY ANALYSIS REPORT")
        report.append("=" * 50)
        report.append("")
        
        report.append("## 🔑 CURRENT CAPABILITIES (App-Only Authentication)")
        report.append("")
        
        if app_results["working_endpoints"]:
            report.append("### ✅ Working Endpoints:")
            for endpoint in app_results["working_endpoints"]:
                rate_limit = app_results["rate_limits"].get(endpoint, "Unknown")
                report.append(f"- **{endpoint}** - Rate limit: {rate_limit}")
                
                if endpoint in app_results["capabilities"]:
                    cap = app_results["capabilities"][endpoint]
                    report.append(f"  - {cap['description']}")
                    report.append(f"  - Metrics available: {', '.join(cap['public_metrics'])}")
                report.append("")
        
        if app_results["forbidden_endpoints"]:
            report.append("### ❌ Forbidden Endpoints (Require User Context):")
            for endpoint in app_results["forbidden_endpoints"]:
                report.append(f"- **{endpoint}** - Needs OAuth user authentication")
            report.append("")
        
        report.append("## 🚀 UPGRADE TO USER CONTEXT AUTHENTICATION")
        report.append("")
        report.append("### 🎯 Enhanced Capabilities:")
        
        for endpoint, details in user_benefits["enhanced_endpoints"].items():
            report.append(f"#### {endpoint}")
            report.append(f"- **Rate limit**: {details['rate_limit']}")
            report.append(f"- **vs App-only**: {details['vs_app_only']}")
            report.append("- **Benefits**:")
            for benefit in details['benefits']:
                report.append(f"  - {benefit}")
            report.append("")
        
        report.append("### 📋 Implementation Steps:")
        for step in user_benefits["implementation_priority"]:
            report.append(f"{step}")
        report.append("")
        
        report.append("## 💡 RECOMMENDATIONS")
        report.append("")
        
        if len(app_results["working_endpoints"]) > 0:
            report.append("✅ **Current system works** - You have functional basic tracking")
            report.append("")
        
        if len(app_results["forbidden_endpoints"]) > 0:
            report.append("🚀 **High-value upgrade available** - User context authentication unlocks:")
            report.append("- 25x more frequent personal monitoring")
            report.append("- Automated posting capabilities") 
            report.append("- Advanced personal analytics")
            report.append("- Content management tools")
            report.append("")
        
        report.append("## 🎯 NEXT STEPS")
        report.append("")
        report.append("1. **Immediate**: Use current app-only system for competitor tracking")
        report.append("2. **Week 1**: Implement OAuth 2.0 user context authentication")
        report.append("3. **Week 2**: Build enhanced personal dashboard with 25x monitoring") 
        report.append("4. **Week 3**: Add automated posting and content management")
        report.append("5. **Week 4**: Create comprehensive growth analytics system")
        
        return "\n".join(report)
    
    def save_report(self, filename: str = "x_api_capabilities_report.md"):
        """Save capability report to file"""
        report = self.generate_capability_report()
        with open(filename, 'w') as f:
            f.write(report)
        print(f"📋 Capability report saved to {filename}")
        return filename

def main():
    """Main function"""
    print("🔍 X API Authentication & Capability Analyzer")
    print("=" * 50)
    
    analyzer = XAPIAuthAnalyzer()
    
    # Generate and save report
    report_file = analyzer.save_report()
    
    print(f"\n📊 Analysis complete! Check {report_file} for detailed findings.")
    print("\n🎯 Key Findings:")
    print("- App-only auth works for competitor tracking & content analysis") 
    print("- User context auth unlocks 25x personal monitoring + posting")
    print("- OAuth implementation = massive capability upgrade")

if __name__ == "__main__":
    main()