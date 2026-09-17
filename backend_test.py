#!/usr/bin/env python3
"""
GiftsDates Backend API Test Suite
Tests auth persistence, health check, and core public endpoints
"""
import requests
import json
import uuid
from datetime import datetime

# Read backend URL from frontend/.env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BASE_URL = line.split('=', 1)[1].strip()
            break

API_BASE = f"{BASE_URL}/api"

print(f"Testing GiftsDates Backend API at: {API_BASE}")
print("=" * 80)

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def test_health():
    """Test 1: Health check endpoint"""
    print("\n[TEST 1] Health Check: GET /api/")
    try:
        response = requests.get(f"{API_BASE}/", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("service") == "GiftsDates" and data.get("ok") is True:
                print("✅ PASS: Health check successful")
                test_results["passed"].append("Health check")
                return True
            else:
                print(f"❌ FAIL: Unexpected response format: {data}")
                test_results["failed"].append(f"Health check - wrong format: {data}")
                return False
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            test_results["failed"].append(f"Health check - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Exception - {e}")
        test_results["failed"].append(f"Health check - exception: {e}")
        return False

def test_auth_register():
    """Test 2: User registration"""
    print("\n[TEST 2] Auth Register: POST /api/auth/register")
    
    # Generate unique email for this test run
    unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    
    payload = {
        "email": unique_email,
        "password": "SecurePass123!",
        "name": "Test User",
        "age": 25,
        "gender": "female",
        "interested_in": "male",
        "orientation": "straight",
        "city": "New York",
        "country": "USA",
        "bio": "Test user for backend testing",
        "language": "en"
    }
    
    print(f"Registering user: {unique_email}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data and "user" in data:
                token = data["token"]
                user = data["user"]
                print(f"✅ PASS: User registered successfully")
                print(f"   User ID: {user.get('id')}")
                print(f"   Email: {user.get('email')}")
                print(f"   Token: {token[:20]}...")
                test_results["passed"].append("Auth register")
                return {"email": unique_email, "password": payload["password"], "token": token, "user": user}
            else:
                print(f"❌ FAIL: Missing token or user in response")
                test_results["failed"].append("Auth register - missing token/user")
                return None
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"   Error: {response.text}")
            test_results["failed"].append(f"Auth register - status {response.status_code}: {response.text[:100]}")
            return None
    except Exception as e:
        print(f"❌ FAIL: Exception - {e}")
        test_results["failed"].append(f"Auth register - exception: {e}")
        return None

def test_auth_login(email, password):
    """Test 3: User login"""
    print("\n[TEST 3] Auth Login: POST /api/auth/login")
    
    payload = {
        "email": email,
        "password": password
    }
    
    print(f"Logging in user: {email}")
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data and "user" in data:
                token = data["token"]
                user = data["user"]
                print(f"✅ PASS: User logged in successfully")
                print(f"   User ID: {user.get('id')}")
                print(f"   Email: {user.get('email')}")
                print(f"   Token: {token[:20]}...")
                test_results["passed"].append("Auth login (first)")
                return {"token": token, "user": user}
            else:
                print(f"❌ FAIL: Missing token or user in response")
                test_results["failed"].append("Auth login - missing token/user")
                return None
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"   Error: {response.text}")
            test_results["failed"].append(f"Auth login - status {response.status_code}: {response.text[:100]}")
            return None
    except Exception as e:
        print(f"❌ FAIL: Exception - {e}")
        test_results["failed"].append(f"Auth login - exception: {e}")
        return None

def test_auth_me(token):
    """Test 4: Get current user with token"""
    print("\n[TEST 4] Auth Me: GET /api/auth/me")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"Getting user info with token: {token[:20]}...")
    
    try:
        response = requests.get(f"{API_BASE}/auth/me", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            user = response.json()
            if "id" in user and "email" in user:
                print(f"✅ PASS: User info retrieved successfully")
                print(f"   User ID: {user.get('id')}")
                print(f"   Email: {user.get('email')}")
                print(f"   Name: {user.get('name')}")
                print(f"   Coins: {user.get('coins')}")
                test_results["passed"].append("Auth me")
                return user
            else:
                print(f"❌ FAIL: Missing id or email in response")
                test_results["failed"].append("Auth me - missing id/email")
                return None
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"   Error: {response.text}")
            test_results["failed"].append(f"Auth me - status {response.status_code}: {response.text[:100]}")
            return None
    except Exception as e:
        print(f"❌ FAIL: Exception - {e}")
        test_results["failed"].append(f"Auth me - exception: {e}")
        return None

def test_auth_persistence(email, password):
    """Test 5: Login again to verify account persisted in MongoDB"""
    print("\n[TEST 5] Auth Persistence: Second login to verify MongoDB persistence")
    
    payload = {
        "email": email,
        "password": password
    }
    
    print(f"Logging in again with same credentials: {email}")
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data and "user" in data:
                token = data["token"]
                user = data["user"]
                print(f"✅ PASS: Second login successful - account persisted in MongoDB!")
                print(f"   User ID: {user.get('id')}")
                print(f"   Email: {user.get('email')}")
                print(f"   This confirms the user account was saved and retrieved from MongoDB")
                test_results["passed"].append("Auth persistence (second login)")
                return True
            else:
                print(f"❌ FAIL: Missing token or user in response")
                test_results["failed"].append("Auth persistence - missing token/user")
                return False
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"   Error: {response.text}")
            test_results["failed"].append(f"Auth persistence - status {response.status_code}: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Exception - {e}")
        test_results["failed"].append(f"Auth persistence - exception: {e}")
        return False

def test_public_endpoints():
    """Test 6: Core public/config endpoints"""
    print("\n[TEST 6] Public Endpoints")
    
    endpoints = [
        ("/meta", "Meta config"),
        ("/support/config", "Support config"),
        ("/spin/config", "Spin config")
    ]
    
    for endpoint, name in endpoints:
        print(f"\n  Testing {name}: GET {endpoint}")
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ PASS: {name} endpoint working")
                print(f"     Response keys: {list(data.keys())[:5]}")
                test_results["passed"].append(f"Public endpoint: {name}")
            elif response.status_code == 503:
                # Some endpoints may be unavailable due to missing keys
                print(f"  ⚠️  WARNING: {name} endpoint unavailable (503) - likely missing API keys")
                test_results["warnings"].append(f"Public endpoint {name} - 503 (expected if keys missing)")
            else:
                print(f"  ❌ FAIL: Expected 200, got {response.status_code}")
                print(f"     Error: {response.text[:200]}")
                test_results["failed"].append(f"Public endpoint {name} - status {response.status_code}")
        except Exception as e:
            print(f"  ❌ FAIL: Exception - {e}")
            test_results["failed"].append(f"Public endpoint {name} - exception: {e}")

def print_summary():
    """Print test summary"""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ PASSED ({len(test_results['passed'])} tests):")
    for test in test_results["passed"]:
        print(f"   - {test}")
    
    if test_results["warnings"]:
        print(f"\n⚠️  WARNINGS ({len(test_results['warnings'])} items):")
        for warning in test_results["warnings"]:
            print(f"   - {warning}")
    
    if test_results["failed"]:
        print(f"\n❌ FAILED ({len(test_results['failed'])} tests):")
        for test in test_results["failed"]:
            print(f"   - {test}")
    else:
        print(f"\n🎉 All critical tests passed!")
    
    print("\n" + "=" * 80)
    
    # Return exit code
    return 0 if len(test_results["failed"]) == 0 else 1

def main():
    """Run all tests"""
    print(f"Starting GiftsDates Backend Tests at {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Test 1: Health check
    test_health()
    
    # Test 2: Register new user
    register_result = test_auth_register()
    if not register_result:
        print("\n⚠️  Cannot continue with auth tests - registration failed")
        test_public_endpoints()
        return print_summary()
    
    email = register_result["email"]
    password = register_result["password"]
    token = register_result["token"]
    
    # Test 3: Login with registered credentials
    login_result = test_auth_login(email, password)
    if login_result:
        token = login_result["token"]  # Use new token from login
    
    # Test 4: Get user info with token
    if token:
        test_auth_me(token)
    
    # Test 5: Login again to verify persistence
    test_auth_persistence(email, password)
    
    # Test 6: Public endpoints
    test_public_endpoints()
    
    # Print summary
    return print_summary()

if __name__ == "__main__":
    exit(main())
