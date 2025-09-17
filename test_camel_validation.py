import requests
import asyncio
from openai import AsyncOpenAI
import os
from main import validate_camel_image

# Test a simple camel image URL
camel_url = "https://cdn.britannica.com/68/143268-050-917048EA/Dromedary-camels.jpg"

print("Testing Britannica camel image URL...")
try:
    response = requests.get(camel_url, timeout=15)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
    print(f"Content-Length: {len(response.content)} bytes")
    
    if response.status_code != 200 or 'image' not in response.headers.get('content-type', ''):
        print("❌ URL is not accessible or not an image")
        exit(1)
    else:
        print("✓ URL is accessible and is an image")
except Exception as e:
    print(f"Error accessing URL: {e}")
    exit(1)

print("\nTesting validation function directly...")

async def test_validation():
    try:
        # Initialize async OpenAI client
        async_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Test validation
        result = await validate_camel_image(camel_url, async_client)
        print(f"Validation result: {result}")
        
        if result['success']:
            validation_data = result['validation']
            print(f"\nValidation Details:")
            print(f"Contains camel: {validation_data.get('contains_camel')}")
            print(f"Overall suitability: {validation_data.get('overall_suitability')}")
            print(f"Feedback: {validation_data.get('feedback')}")
            print(f"Visible parts: {validation_data.get('visible_parts')}")
            
            if validation_data.get('contains_camel'):
                print("\n✅ SUCCESS: Image contains a camel and is suitable for analysis!")
            else:
                print("\n❌ ISSUE: Image does not contain a camel according to GPT-4o")
        else:
            print(f"\n❌ Validation failed: {result.get('error')}")
            
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")

# Run the async test
asyncio.run(test_validation())