#!/usr/bin/env python3
"""
Discover and test the staging deployment URL.
This script tries multiple methods to find the active staging environment.
"""

import subprocess
import requests
import sys
from typing import Optional

def run_command(cmd: str) -> Optional[str]:
    """Run a shell command and return output or None on failure"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except subprocess.TimeoutExpired:
        print(f"⏰ Command timed out: {cmd}")
        return None
    except Exception as e:
        print(f"❌ Command failed: {cmd} - {e}")
        return None

def test_url(url: str) -> bool:
    """Test if a URL is accessible and returns expected content"""
    try:
        print(f"🧪 Testing: {url}")
        response = requests.get(f"{url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                print("✅ Health check passed")
                return True
        print(f"❌ Health check failed: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_staging_endpoints(base_url: str):
    """Test various endpoints on the staging server"""
    print(f"\n🚀 Testing staging endpoints: {base_url}")
    
    endpoints = [
        ("/health", "Health check"),
        ("/metrics", "Metrics endpoint"),
        ("/recommend?lat=47.6&lon=-122.3&radius=25", "Recommendations API"),
    ]
    
    for endpoint, description in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {description}: OK")
                if 'recommend' in endpoint:
                    data = response.json()
                    results = data.get('results', [])
                    print(f"   📍 Found {len(results)} locations")
                    if results:
                        print(f"   🏆 Top result: {results[0].get('name')} (score: {results[0].get('score')})")
            else:
                print(f"❌ {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: {str(e)[:50]}...")

def main():
    print("🔍 Discovering Staging Deployment")
    print("=" * 40)
    
    # Method 1: Try to get URL from gcloud (if available)
    print("\n1. Checking Google Cloud Run...")
    service_url = run_command("gcloud run services describe sun-chaser-staging --region=us-west1 --format='value(status.url)' 2>/dev/null")
    if service_url and service_url.startswith('https://'):
        print(f"🎯 Found service URL: {service_url}")
        if test_url(service_url):
            test_staging_endpoints(service_url)
            print(f"\n✨ Staging URL: {service_url}")
            return service_url
    
    # Method 2: Try common Cloud Run URL patterns
    print("\n2. Trying common URL patterns...")
    base_patterns = [
        "https://sun-chaser-staging-081623-uw.a.run.app",
        "https://sun-chaser-staging-sun-chaser-081623-uw.a.run.app", 
        "https://sun-chaser-staging-081623-us-west1.a.run.app",
    ]
    
    for url in base_patterns:
        if test_url(url):
            test_staging_endpoints(url)
            print(f"\n✨ Staging URL: {url}")
            return url
    
    # Method 3: Check GitHub Actions for recent deployment
    print("\n3. Checking recent deployments...")
    print("💡 Check https://github.com/Slybry2000/Sunchaserjuly27/actions")
    print("   Look for the latest 'Deploy to Cloud Run (staging)' workflow")
    print("   The deployment logs will contain the service URL")
    
    print("\n❌ Could not automatically discover staging URL")
    print("\n📋 Manual steps:")
    print("1. Visit GitHub Actions: https://github.com/Slybry2000/Sunchaserjuly27/actions") 
    print("2. Find the latest successful 'Deploy to Cloud Run (staging)' run")
    print("3. Check the logs for the service URL")
    print("4. Or run: gcloud run services list --region=us-west1")
    
    return None

if __name__ == "__main__":
    staging_url = main()
    if staging_url:
        print(f"\n🎉 Success! Staging is live at: {staging_url}")
        sys.exit(0)
    else:
        print("\n⚠️  Staging URL needs manual discovery")
        sys.exit(1)
