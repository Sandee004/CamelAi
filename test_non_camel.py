import requests
import json

# Test with a non-camel image (a cat image from Unsplash)
print("Testing with a non-camel image (cat)...")
response = requests.post('http://127.0.0.1:5000/api/rate-image', 
                        json={'image_url': 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba'}, 
                        headers={'Content-Type': 'application/json'})

print('Status:', response.status_code)

if response.headers.get('content-type', '').startswith('application/json'):
    result = response.json()
    print('\nOverall Score:', result.get('overall_score', 'N/A'))
    print('Processing Time:', result.get('processing_time', 'N/A'), 'seconds')
    
    print('\nCategory Scores:')
    for cat, data in result.get('beauty_ratings', {}).items():
        category_score = data.get('category_score', 'N/A')
        analysis = data.get('analysis', 'N/A')
        print(f'  {cat}: {category_score}')
        print(f'    Analysis: {analysis[:100]}...' if len(str(analysis)) > 100 else f'    Analysis: {analysis}')
        
        # Show individual attribute scores if available
        attributes = data.get('attributes', [])
        if attributes:
            print(f'    Attributes ({len(attributes)}):')
            for attr in attributes[:3]:  # Show first 3 attributes
                attr_name = attr.get('name', 'Unknown')
                attr_score = attr.get('score', 'N/A')
                print(f'      - {attr_name}: {attr_score}')
            if len(attributes) > 3:
                print(f'      ... and {len(attributes) - 3} more')
else:
    print('Error:', response.text)

# Test the same non-camel image again to verify caching works
print("\n" + "="*50)
print("Testing same non-camel image again (should be cached)...")
response2 = requests.post('http://127.0.0.1:5000/api/rate-image', 
                         json={'image_url': 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba'}, 
                         headers={'Content-Type': 'application/json'})

print('Status:', response2.status_code)

if response2.headers.get('content-type', '').startswith('application/json'):
    result2 = response2.json()
    print('\nOverall Score:', result2.get('overall_score', 'N/A'))
    print('Processing Time:', result2.get('processing_time', 'N/A'), 'seconds')
    print('Cache Status: CACHED' if result2.get('cached') else 'NOT CACHED')
else:
    print('Error:', response2.text)