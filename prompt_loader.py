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
        """Build complete message list including predefined messages and user message."""
        prompt_data = self.load_prompt(category)
        
        # Start with predefined messages
        messages = prompt_data["predefined_messages"].copy()
        
        # Build user message with the actual image to analyze
        user_content = []
        
        if user_text:
            user_content.append({
                "type": "text",
                "text": user_text
            })
        
        user_content.extend([
            {
                "type": "text",
                "text": f"Now please analyze this {category} and provide a detailed beauty rating from 1-10:"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": user_image_url
                }
            }
        ])
        
        # Add the user message
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