# Attribute-specific weights for camel beauty scoring
# Based on user specifications: High=5, Medium=3, Low=1

ATTRIBUTE_WEIGHTS = {
    # HIGH PRIORITY ATTRIBUTES (Weight = 5)
    "HEAD SIZE": 5,  # User specified "High = weight is 5"
    "NECK LENGTH": 5,  # User specified "Neck length = 5"
    "LOWER JAW LENGTH": 5,  # User specified "Jaw length = 5"
    "CHEEK WIDTH": 5,  # User specified "Jaw prominence = 5" (closest match to jaw/cheek features)
    "WITHERS LENGTH": 5,  # User specified "Width length = 5" (interpreting as withers length)
    
    # MEDIUM PRIORITY ATTRIBUTES (Weight = 3)
    "LIP LENGTH": 3,  # User specified "Lips = 3"
    "SNOUT CURVE SCORE": 3,  # User specified "Nose curves = 3"
    
    # LOW PRIORITY ATTRIBUTES (Weight = 1)
    "WITHERS LEVELNESS": 1,  # User specified "Wither alignment = 1"
    "LEG JOINT ANGLE": 1,  # User specified "Hock joint = 1"
    "HUMP POSITION": 1,  # User specified "Back structure/hump position = 1"
    "NECK MASS": 1,  # User specified "Neck thickness = 1"
    
    # DEFAULT WEIGHTS FOR UNSPECIFIED ATTRIBUTES (Weight = 3 - Medium)
    # Head attributes
    "EAR SIZE": 3,
    "EAR DIRECTION": 3,
    "HEAD UPWARD ANGLE": 3,
    
    # Body attributes
    "HUMP VERTICAL ANGLE": 3,
    "HUMP TO RUMP DISTANCE": 3,
    "BODY HEIGHT": 3,
    
    # Neck attributes
    "NECK STRAIGHTNESS SCORE": 3,
    "NECK ANGLE TOP": 3,
    "NECK ANGLE BOTTOM": 3,
    
    # Leg attributes
    "BONE THICKNESS": 3,
    "LEG STRAIGHTNESS": 3,
    "MUSCLE DEFINITION": 3
}


GENDER_SPECIFIC_WEIGHTS = {
    "BONE THICKNESS": {"male": 5, "female": 1}
}

def get_attribute_weight(attribute_name: str, gender: str = None) -> int:
    """
    Get the weight for a specific attribute, considering gender if applicable.
    
    Args:
        attribute_name: Name of the attribute
        gender: Gender of the camel ("male", "female", or None)
        
    Returns:
        Weight value (1, 3, or 5)
    """
    # Check for gender-specific weight first
    if gender and gender.lower() in ["male", "female"]:
        gender_weights = GENDER_SPECIFIC_WEIGHTS.get(attribute_name)
        if gender_weights:
            return gender_weights.get(gender.lower(), 3)
            
    return ATTRIBUTE_WEIGHTS.get(attribute_name, 3)  # Default to medium weight


def get_all_weights() -> dict:
    """
    Get all default attribute weights.
    
    Returns:
        Dictionary of attribute names and their weights
    """
    return ATTRIBUTE_WEIGHTS.copy()


def calculate_weighted_score(attributes: list, gender: str = None) -> float:
    """
    Calculate weighted average score for a list of attributes.
    
    Args:
        attributes: List of attribute dictionaries with 'name' and 'score' keys
        gender: Gender of the camel ("male", "female", or None)
        
    Returns:
        Weighted average score
    """
    total_weighted_score = 0
    total_weight = 0
    
    for attr in attributes:
        if isinstance(attr.get('score'), (int, float)) and attr['score'] is not None:
            weight = get_attribute_weight(attr['name'], gender)
            total_weighted_score += attr['score'] * weight
            total_weight += weight
    
    return round(total_weighted_score / total_weight, 2) if total_weight > 0 else 0