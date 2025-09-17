import requests
import json

# Test with an invalid image URL to check error handling
print("Testing with invalid image URL...")
response = requests.post('http://127.0.0.1:5000/api/rate-image', 
                        json={'image_url': 'https://invalid-url-that-does-not-exist.com/image.jpg'}, 
                        headers={'Content-Type': 'application/json'})

print('Status:', response.status_code)
print('Response:', response.text)

# Test with a valid but non-image URL
print("\nTesting with non-image URL...")
response2 = requests.post('http://127.0.0.1:5000/api/rate-image', 
                         json={'image_url': 'https://www.google.com'}, 
                         headers={'Content-Type': 'application/json'})

print('Status:', response2.status_code)
print('Response:', response2.text)

# Test with missing image_url parameter
print("\nTesting with missing image_url...")
response3 = requests.post('http://127.0.0.1:5000/api/rate-image', 
                         json={}, 
                         headers={'Content-Type': 'application/json'})

print('Status:', response3.status_code)
print('Response:', response3.text)