
import sys
import unittest
from unittest.mock import MagicMock

# 1. Mock the dependencies BEFORE importing prompt_loader
# This ensures that when prompt_loader imports these, it gets our mocks
mock_models = MagicMock()
sys.modules['core.models'] = mock_models
sys.modules['flask'] = MagicMock()
sys.modules['core.extensions'] = MagicMock()

# 2. Import the class under test
from prompt_loader import PromptLoader

class TestDynamicLearning(unittest.TestCase):
    
    def setUp(self):
        self.loader = PromptLoader()
        
    def test_build_messages_with_golden_examples(self):
        """Test that golden examples are injected into the prompt"""
        
        # 3. Configure the mock for RatingFeedback
        # The code does: RatingFeedback.query.filter_by(...).order_by(...).limit(...).all()
        
        # Create a mock feedback object
        mock_feedback_item = MagicMock()
        mock_feedback_item.image_url = "http://example.com/golden.jpg"
        mock_feedback_item.corrected_score = {"HEAD SIZE": {"score": 10, "reason": "Perfect"}}
        mock_feedback_item.reasoning = "Expert correction reasoning"

        # Setup the chain
        mock_query = mock_models.RatingFeedback.query
        mock_filter = mock_query.filter_by.return_value
        mock_order = mock_filter.order_by.return_value
        mock_limit = mock_order.limit.return_value
        mock_limit.all.return_value = [mock_feedback_item]
        
        # 4. Mock load_prompt to return simple static data
        original_load_prompt = self.loader.load_prompt
        self.loader.load_prompt = MagicMock(return_value={
            "predefined_messages": [{"role": "user", "content": "static example"}],
            "system_prompt": "System instructions"
        })
        
        try:
            # 5. Run the method
            messages = self.loader.build_messages("head", "http://example.com/target.jpg")
            
            # 6. Verify assertions
            print(f"Generated {len(messages)} messages")
            
            # Check for injection header
            has_header = any("EXPERT-VALIDATED examples" in str(m) for m in messages)
            if has_header:
                print("PASS: Found Expert Validation header")
            else:
                print("FAIL: Missing Expert Validation header")
                
            # Check for golden example content
            has_example = any("Expert correction reasoning" in str(m) for m in messages)
            if has_example:
                print("PASS: Found Golden Example reasoning")
            else:
                print("FAIL: Missing Golden Example reasoning")
                
            self.assertTrue(has_header and has_example)
            
        finally:
            # Restore method
            self.loader.load_prompt = original_load_prompt

if __name__ == '__main__':
    unittest.main()
