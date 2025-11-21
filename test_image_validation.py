import requests
import json

def test_image_validation():
    """
    Test the image validation functionality
    """
    # Test with a sample camel image URL
    test_data = {
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/07._Camel_Profile%2C_near_Silverton%2C_NSW%2C_07.07.2007.jpg/1200px-07._Camel_Profile%2C_near_Silverton%2C_NSW%2C_07.07.2007.jpg",
        "gender": "unknown"
    }
    
    try:
        print("Testing image validation with camel image...")
        response = requests.post(
            "http://localhost:5000/api/rate-image",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Image validation and rating successful!")
        elif response.status_code == 400:
            print("⚠️ Image validation failed (expected for non-camel images)")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure Flask app is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_image_validation()