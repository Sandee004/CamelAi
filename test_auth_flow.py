#!/usr/bin/env python3
"""
Test script for the modified authentication flow
- Phone-only authentication
- Disabled SMS sending
- Hardcoded OTP '0000' verification
- User settings update
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:5000"

def test_auth_flow():
    print("=== Testing Modified Authentication Flow ===")
    
    # Test phone number
    test_phone = "+1234567890"
    
    print(f"\n1. Testing auth request with phone: {test_phone}")
    
    # Step 1: Request OTP
    auth_response = requests.post(f"{BASE_URL}/api/auth", 
                                 json={"phone": test_phone})
    
    print(f"Auth Response Status: {auth_response.status_code}")
    print(f"Auth Response: {auth_response.json()}")
    
    if auth_response.status_code != 200:
        print("❌ Auth request failed")
        return
    
    print("✅ Auth request successful")
    
    print(f"\n2. Testing OTP verification with hardcoded OTP '0000'")
    
    # Step 2: Verify OTP with hardcoded '0000'
    verify_response = requests.post(f"{BASE_URL}/api/verify-otp",
                                   json={
                                       "phone": test_phone,
                                       "otp": "0000"
                                   })
    
    print(f"Verify Response Status: {verify_response.status_code}")
    print(f"Verify Response: {verify_response.json()}")
    
    if verify_response.status_code != 200:
        print("❌ OTP verification failed")
        return
    
    print("✅ OTP verification successful")
    
    # Extract access token
    verify_data = verify_response.json()
    access_token = verify_data.get('access_token')
    user_id = verify_data.get('user_id')
    
    print(f"User ID: {user_id}")
    print(f"Access Token: {access_token[:50]}...")
    
    print(f"\n3. Testing user settings update")
    
    # Step 3: Update user settings
    headers = {"Authorization": f"Bearer {access_token}"}
    settings_data = {
        "name": "Test User",
        "email": "test@example.com"
    }
    
    settings_response = requests.put(f"{BASE_URL}/api/user/settings",
                                   json=settings_data,
                                   headers=headers)
    
    print(f"Settings Response Status: {settings_response.status_code}")
    print(f"Settings Response: {settings_response.json()}")
    
    if settings_response.status_code != 200:
        print("❌ Settings update failed")
        return
    
    print("✅ Settings update successful")
    
    print("\n=== All tests passed! ===")
    
def test_email_auth_disabled():
    print("\n=== Testing Email Auth Disabled ===")
    
    # Try to authenticate with email (should fail)
    email_auth_response = requests.post(f"{BASE_URL}/api/auth",
                                       json={"email": "test@example.com"})
    
    print(f"Email Auth Response Status: {email_auth_response.status_code}")
    print(f"Email Auth Response: {email_auth_response.json()}")
    
    if email_auth_response.status_code == 400:
        print("✅ Email authentication correctly disabled")
    else:
        print("❌ Email authentication should be disabled")

if __name__ == "__main__":
    try:
        test_auth_flow()
        test_email_auth_disabled()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure the Flask app is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")