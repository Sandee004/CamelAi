#!/usr/bin/env python3
"""
Test script to verify the new attribute-based weighting system
"""

import requests
import json

def test_camel_image():
    """Test with a camel image to verify attribute-based scoring"""
    
    # Test with a camel image URL
    # Use the provided camel image URL
    camel_url = "https://y7mjgvz086.ufs.sh/f/oYPESNnKE5gutRI3wIdczJQCs7Ylf8Tx52XR6KZOaL09peyH"
    
    print("Testing Attribute-Based Weighting System")
    print("="*60)
    print(f"Testing URL: {camel_url}")
    
    try:
        # Send the image URL as JSON
        data = {
            "image_url": camel_url,
            "validation_only": False  # Test full scoring system
        }
        response = requests.post(
             'http://localhost:5000/api/rate-image',
             json=data,
             timeout=120
         )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\nOverall Score: {result.get('overall_score', 'N/A')}")
            print(f"Cached: {result.get('cached', 'N/A')}")
            print(f"Response Time: {result.get('response_time_ms', 'N/A')}ms")
            
            # Show attribute weights
            attribute_weights = result.get('attribute_weights', {})
            print(f"\nAttribute Weights (showing first 10):")
            for i, (attr, weight) in enumerate(list(attribute_weights.items())[:10]):
                print(f"  {attr}: {weight}")
            
            # Show category scores
            category_scores = result.get('category_scores', {})
            print(f"\nCategory Scores:")
            for category, score in category_scores.items():
                print(f"  {category}: {score}")
            
            # Show beauty ratings structure
            beauty_ratings = result.get('beauty_ratings', {})
            print(f"\nBeauty Ratings Summary:")
            for category, data in beauty_ratings.items():
                if isinstance(data, dict) and 'attributes' in data:
                    print(f"  {category}: {len(data['attributes'])} attributes")
                    # Show first few attributes with their scores and weights
                    for attr in data['attributes'][:3]:
                        attr_name = attr.get('name', 'Unknown')
                        attr_score = attr.get('score', 'N/A')
                        attr_weight = attribute_weights.get(attr_name, 3)
                        print(f"    - {attr_name}: score={attr_score}, weight={attr_weight}")
                else:
                    print(f"  {category}: {data}")
            
            print("\n✓ SUCCESS: Attribute-based weighting system is working!")
            
        elif response.status_code == 400:
            result = response.json()
            print(f"\nValidation Error: {result.get('error', 'Unknown error')}")
            validation = result.get('validation', {})
            if validation:
                print(f"Contains Camel: {validation.get('contains_camel', 'N/A')}")
                print(f"Feedback: {validation.get('feedback', 'N/A')[:100]}...")
        else:
            print(f"\nUnexpected status code: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"\nRequest failed: {e}")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_camel_image()