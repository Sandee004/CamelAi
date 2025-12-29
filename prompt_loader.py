import json
import os
from typing import Dict, List, Any

class PromptLoader:
    """Utility class for loading and managing beauty category prompts."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir
        self._prompts_cache = {}
    
    def load_prompt(self, category: str) -> Dict[str, Any]:
        """Load prompt configuration for a specific beauty category."""
        if category in self._prompts_cache:
            return self._prompts_cache[category]
        
        prompt_file = os.path.join(self.prompts_dir, f"{category}_beauty.json")
        
        if not os.path.exists(prompt_file):
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_data = json.load(f)
        
        self._prompts_cache[category] = prompt_data
        return prompt_data
    
    def build_messages(self, category: str, user_image_url: str, user_text: str = None) -> List[Dict[str, Any]]:
        """
        Build the full message list including dynamic Golden Examples (Few-Shot Learning).
        """
        # 1. Fetch "Golden Examples" (Approved corrections)
        try:
            from core.models import RatingFeedback
            # Get up to 3 most recent approved feedback items for this category
            golden_examples = RatingFeedback.query.filter_by(
                category=category, 
                status='approved'
            ).order_by(RatingFeedback.created_at.desc()).limit(3).all()
        except Exception as e:
            # Fallback if DB is not ready or context is missing
            # print(f"Error fetching golden examples: {e}")
            golden_examples = []

        prompt_data = self.load_prompt(category)
        messages = []

        # 2. Add Predefined/Static Messages (Reference Images)
        # Strategy: usage static examples as baseline, but if we have golden examples, we might mix them
        # For now, let's KEEP static examples but append golden ones as "User Corrections"
        # OR: specific override strategy.
        # Let's use: Static Examples -> Golden Examples -> Target Image
        
        static_messages = prompt_data.get("predefined_messages", [])
        messages.extend(static_messages)
        
        # 3. Inject Golden Examples
        if golden_examples:
            messages.append({
                "role": "user",
                "content": [{
                    "type": "text", 
                    "text": "IMPORTANT: The following are EXPERT-VALIDATED examples from your training database. These corrections take precedence over general rules. Study them carefully:"
                }]
            })
            
            for example in golden_examples:
                # We need to format the corrected score into a clear example
                import json
                corrected_json_str = json.dumps(example.corrected_score, indent=2)
                reasoning = example.reasoning if example.reasoning else "Expert correction."
                
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": example.image_url}},
                        {"type": "text", "text": "Rate this camel."}
                    ]
                })
                messages.append({
                    "role": "assistant",
                    "content": f"Based on expert feedback, here is the correct rating:\n{corrected_json_str}\n\nKey Reasoning: {reasoning}"
                })

        # 4. Add the User's Target Image
        user_content = []
        if user_text:
            user_content.append({"type": "text", "text": user_text})
        
        user_content.extend([
            {
                "type": "text",
                "text": f"Now please analyze this {category} and provide a detailed beauty rating from 1-10:"
            },
            {
                "type": "image_url",
                "image_url": {"url": user_image_url}
            }
        ])
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        return messages
    
    def get_system_prompt(self, category: str, gender: str = None) -> str:
        """Get the system prompt for a specific category, optionally enhanced with gender context."""
        prompt_data = self.load_prompt(category)
        system_prompt = prompt_data["system_prompt"]
        
        # Handle both old string format and new object format
        if isinstance(system_prompt, dict):
            prompt_text = system_prompt.get("text", "")
        else:
            prompt_text = system_prompt
        
        # Inject gender context if provided
        if gender and gender.lower() in ["male", "female"]:
            gender_context = f"\n\n# Gender Context (Provided)\nThe camel's gender has been identified as **{gender.upper()}**. Please apply the {gender.upper()}-specific rules strictly when evaluating attributes. If the visual characteristics do not match the provided gender, note this in your analysis but still apply the gender-specific scoring guidelines.\n"
            # Insert gender context after the Instructions section (before Workflow Checklist)
            if "# Workflow Checklist" in prompt_text:
                # Insert right before Workflow Checklist
                workflow_pos = prompt_text.find("# Workflow Checklist")
                prompt_text = prompt_text[:workflow_pos] + gender_context + prompt_text[workflow_pos:]
            elif "# Instructions" in prompt_text:
                # Find the end of Instructions section and insert before next major section
                instructions_end = prompt_text.find("# Instructions")
                if instructions_end != -1:
                    # Find the next major section
                    next_section = prompt_text.find("\n\n#", instructions_end + 15)
                    if next_section != -1:
                        prompt_text = prompt_text[:next_section] + gender_context + prompt_text[next_section:]
                    else:
                        # If no next section found, append after Instructions
                        instructions_line_end = prompt_text.find("\n\n", instructions_end)
                        if instructions_line_end != -1:
                            prompt_text = prompt_text[:instructions_line_end] + gender_context + prompt_text[instructions_line_end:]
            else:
                # If structure is different, insert after first major section
                first_section_end = prompt_text.find("\n\n#", 0)
                if first_section_end != -1:
                    # Find end of first section
                    second_section = prompt_text.find("\n\n#", first_section_end + 3)
                    if second_section != -1:
                        prompt_text = prompt_text[:second_section] + gender_context + prompt_text[second_section:]
                    else:
                        prompt_text = gender_context + prompt_text
                else:
                    prompt_text = gender_context + prompt_text
        
        return prompt_text
    
    def get_available_categories(self) -> List[str]:
        """Get list of available beauty categories."""
        categories = []
        if os.path.exists(self.prompts_dir):
            for filename in os.listdir(self.prompts_dir):
                if filename.endswith('_beauty.json'):
                    category = filename.replace('_beauty.json', '')
                    categories.append(category)
        return categories