import asyncio
import json
from openai import AsyncOpenAI
from core.config import Config

async def test_validation():
    """Test the validation function directly"""
    
    # Initialize async OpenAI client
    async_client = AsyncOpenAI(api_key=Config.client.api_key)
    
    # Cat image URL from the test
    image_url = 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba'
    
    validation_prompt = """
You are a camel detection expert. Analyze this image and determine:

1. Does this image contain a camel?
2. If yes, are the following camel body parts clearly visible and suitable for beauty analysis?
   - Head (including ears, snout, jaw)
   - Neck 
   - Body (including withers, hump, back)
   - Legs (at least 2-3 legs should be visible)

Provide your response in JSON format with:
{
  "contains_camel": true/false,
  "visible_parts": {
    "head": true/false,
    "neck": true/false, 
    "body": true/false,
    "legs": true/false
  },
  "overall_suitability": true/false,
  "feedback": "Detailed explanation of what you see and why it is/isn't suitable for camel beauty analysis",
  "missing_parts": ["list of missing or poorly visible parts"],
  "quality_issues": ["list of image quality issues if any"]
}

Be strict in your assessment - the image should clearly show a camel with most body parts visible for accurate beauty analysis.
"""
    
    try:
        print(f"Testing validation with cat image: {image_url}")
        
        response = await async_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": validation_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        
        validation_result = json.loads(response.choices[0].message.content)
        
        print("\nValidation Result:")
        print(json.dumps(validation_result, indent=2))
        
        print(f"\nContains camel: {validation_result.get('contains_camel')}")
        print(f"Overall suitability: {validation_result.get('overall_suitability')}")
        print(f"Feedback: {validation_result.get('feedback')}")
        
    except Exception as e:
        print(f"Error in validation test: {e}")

if __name__ == "__main__":
    asyncio.run(test_validation())