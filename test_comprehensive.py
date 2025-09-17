import requests
import json
import time

def test_scenario(name, url, expected_status):
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"Expected Status: {expected_status}")
    
    start_time = time.time()
    response = requests.post('http://127.0.0.1:5000/api/rate-image', 
                            json={'image_url': url}, 
                            headers={'Content-Type': 'application/json'})
    end_time = time.time()
    
    print(f"Actual Status: {response.status_code}")
    print(f"Response Time: {end_time - start_time:.2f}s")
    
    if response.headers.get('content-type', '').startswith('application/json'):
        result = response.json()
        
        if response.status_code == 200:
            print(f"Overall Score: {result.get('overall_score', 'N/A')}")
            print(f"Cached: {result.get('cached', False)}")
            if result.get('beauty_ratings'):
                print(f"Categories: {list(result['beauty_ratings'].keys())}")
        else:
            print(f"Error: {result.get('error', 'N/A')}")
            print(f"Cached: {result.get('cached', False)}")
            if 'validation' in result:
                validation = result['validation']
                print(f"Contains Camel: {validation.get('contains_camel', 'N/A')}")
                print(f"Suitable: {validation.get('overall_suitability', 'N/A')}")
    else:
        print(f"Non-JSON Response: {response.text[:100]}...")
    
    return response.status_code == expected_status

# Test scenarios
test_cases = [
    ("Valid Image Analysis (Cat - Expected 400)", "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba", 400),
    ("Non-Camel Image (Cat)", "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba", 400),
    ("Invalid URL", "https://httpbin.org/status/404", 400),
    ("Non-Image URL", "https://httpbin.org/json", 400),
]

print("COMPREHENSIVE API TEST")
print("=" * 60)

results = []
for name, url, expected_status in test_cases:
    success = test_scenario(name, url, expected_status)
    results.append((name, success))
    
    # Test caching by making the same request again
    if success:
        print(f"\n--- Testing Cache for {name} ---")
        start_time = time.time()
        response2 = requests.post('http://127.0.0.1:5000/api/rate-image', 
                                 json={'image_url': url}, 
                                 headers={'Content-Type': 'application/json'})
        end_time = time.time()
        
        if response2.headers.get('content-type', '').startswith('application/json'):
            result2 = response2.json()
            cached = result2.get('cached', False)
            print(f"Second Request - Status: {response2.status_code}, Cached: {cached}, Time: {end_time - start_time:.2f}s")
            if expected_status == 400 and 'validation' in result2:
                validation = result2['validation']
                print(f"Contains Camel: {validation.get('contains_camel', 'N/A')}")
                print(f"Feedback: {validation.get('feedback', 'N/A')[:100]}...")
        
        time.sleep(1)  # Brief pause between tests

print(f"\n{'='*60}")
print("TEST SUMMARY")
print(f"{'='*60}")
for name, success in results:
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status} - {name}")

all_passed = all(success for _, success in results)
print(f"\nOverall Result: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")