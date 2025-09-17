import requests
import json

# Test with a different image to verify caching works with multiple images
print("Testing with a different image...")
response = requests.post('http://127.0.0.1:5000/api/rate-image', 
                        json={'image_url': 'https://images.unsplash.com/photo-1551963831-b3b1ca40c98e'}, 
                        headers={'Content-Type': 'application/json'})

print('Status:', response.status_code)

if response.headers.get('content-type', '').startswith('application/json'):
    result = response.json()
    print('\nOverall Score:', result.get('overall_score', 'N/A'))
    print('Processing Time:', result.get('processing_time', 'N/A'), 'seconds')
    print('Categories analyzed:', len(result.get('beauty_ratings', {})))
else:
    print('Error:', response.text)

# Test the same image again to verify caching
print("\nTesting same image again (should be cached)...")
response2 = requests.post('http://127.0.0.1:5000/api/rate-image', 
                         json={'image_url': 'https://images.unsplash.com/photo-1551963831-b3b1ca40c98e'}, 
                         headers={'Content-Type': 'application/json'})

print('Status:', response2.status_code)

if response2.headers.get('content-type', '').startswith('application/json'):
    result2 = response2.json()
    print('\nOverall Score:', result2.get('overall_score', 'N/A'))
    print('Processing Time:', result2.get('processing_time', 'N/A'), 'seconds')
    print('Categories analyzed:', len(result2.get('beauty_ratings', {})))
else:
    print('Error:', response2.text)