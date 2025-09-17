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
    
    def get_system_prompt(self, category: str) -> str:
        """Get the system prompt for a specific category."""
        prompt_data = self.load_prompt(category)
        system_prompt = prompt_data["system_prompt"]
        
        # Handle both old string format and new object format
        if isinstance(system_prompt, dict):
            return system_prompt.get("text", "")
        return system_prompt
    
    def get_available_categories(self) -> List[str]:
        """Get list of available beauty categories."""
        categories = []
        if os.path.exists(self.prompts_dir):
            for filename in os.listdir(self.prompts_dir):
                if filename.endswith('_beauty.json'):
                    category = filename.replace('_beauty.json', '')
                    categories.append(category)
        return categories