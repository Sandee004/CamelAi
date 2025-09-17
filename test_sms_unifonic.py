import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import send_sms_otp
import random

def test_sms_functionality():
    """
    Test the Unifonic SMS functionality
    """
    print("Testing Unifonic SMS Integration")
    print("=" * 40)
    
    # Generate a test OTP
    test_otp = str(random.randint(100000, 999999))
    
    # Test phone number (replace with a valid international number for actual testing)
    # Format: international format without 00 or + (e.g., 966000000000 for Saudi Arabia)
    test_phone = input("Enter test phone number (international format without + or 00): ")
    
    if not test_phone:
        print("No phone number provided. Using default test number: 966000000000")
        test_phone = "966000000000"
    
    print(f"Sending OTP {test_otp} to {test_phone}...")
    
    try:
        result = send_sms_otp(test_phone, test_otp)
        
        if result:
            print("✅ SMS sent successfully!")
            print(f"OTP: {test_otp}")
            print(f"Phone: {test_phone}")
        else:
            print("❌ SMS sending failed!")
            
    except Exception as e:
        print(f"❌ Error during SMS test: {e}")

if __name__ == "__main__":
    test_sms_functionality()