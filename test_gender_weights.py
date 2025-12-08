import unittest
from attribute_weights import get_attribute_weight, calculate_weighted_score, GENDER_SPECIFIC_WEIGHTS

class TestGenderWeights(unittest.TestCase):
    def test_get_attribute_weight_gender(self):
        """Test getting attribute weights with gender specified"""
        # Default weight for bone thickness is likely 3 (medium) or whatever fallback
        # But for gender:
        # Male should be 5
        self.assertEqual(get_attribute_weight("BONE THICKNESS", "male"), 5)
        self.assertEqual(get_attribute_weight("BONE THICKNESS", "MALE"), 5)
        
        # Female should be 1
        self.assertEqual(get_attribute_weight("BONE THICKNESS", "female"), 1)
        self.assertEqual(get_attribute_weight("BONE THICKNESS", "FEMALE"), 1)
        
        # Other attributes should remain default (assuming 3 for moderate)
        # Use an attribute not in GENDER_SPECIFIC_WEIGHTS
        self.assertEqual(get_attribute_weight("SOME_OTHER_ATTR", "male"), 3)
        self.assertEqual(get_attribute_weight("SOME_OTHER_ATTR", "female"), 3)

    def test_calculate_weighted_score_gender(self):
        """Test that gender affects the overall score calculation"""
        # Create a dummy attribute list where BONE THICKNESS is the only variable
        # Let's say we have BONE THICKNESS with score 10
        # And another attribute CONSTANT with score 5 and weight 3
        attributes = [
            {"name": "BONE THICKNESS", "score": 10},
            {"name": "OTHER_ATTR", "score": 5}  # Weight 3 by default
        ]
        
        # Male Calculation:
        # BONE THICKNESS: weight 5, score 10 -> 50
        # OTHER_ATTR: weight 3, score 5 -> 15
        # Total weight: 5 + 3 = 8
        # Weighted Score: (50 + 15) / 8 = 65 / 8 = 8.125 -> round to 8.12
        score_male = calculate_weighted_score(attributes, "male")
        self.assertEqual(score_male, 8.12)
        
        # Female Calculation:
        # BONE THICKNESS: weight 1, score 10 -> 10
        # OTHER_ATTR: weight 3, score 5 -> 15
        # Total weight: 1 + 3 = 4
        # Weighted Score: (10 + 15) / 4 = 25 / 4 = 6.25
        score_female = calculate_weighted_score(attributes, "female")
        self.assertEqual(score_female, 6.25)
        
        # None/Unknown Calculation (should use default weight 3 for Bone Thickness)
        # BONE THICKNESS: weight 3, score 10 -> 30
        # OTHER_ATTR: weight 3, score 5 -> 15
        # Total weight: 3 + 3 = 6
        # Weighted Score: (30 + 15) / 6 = 45 / 6 = 7.5
        score_none = calculate_weighted_score(attributes, None)
        self.assertEqual(score_none, 7.5)

if __name__ == '__main__':
    unittest.main()
