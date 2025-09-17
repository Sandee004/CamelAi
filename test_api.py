import requests
import json

response = requests.post('http://127.0.0.1:5000/api/rate-image', 
                        json={'image_url': 'https://images.pexels.com/photos/2295744/pexels-photo-2295744.jpeg'}, 
                        headers={'Content-Type': 'application/json'})

print('Status:', response.status_code)

if response.headers.get('content-type', '').startswith('application/json'):
    result = response.json()
    print('\nOverall Score:', result.get('overall_score', 'N/A'))
    print('\nAttribute Weights:', result.get('attribute_weights', 'N/A'))
    print('\nCategory Scores:')
    
    for cat, data in result.get('beauty_ratings', {}).items():
        category_score = data.get('category_score', 'N/A')
        num_attributes = len(data.get('attributes', []))
        print(f'  {cat}: {category_score} (avg of {num_attributes} attributes)')
        
        # Show individual attribute scores
        for attr in data.get('attributes', []):
            attr_name = attr.get('name', 'Unknown')
            attr_score = attr.get('score', 'N/A')
            print(f'    - {attr_name}: {attr_score}')
else:
    print('Error:', response.text)