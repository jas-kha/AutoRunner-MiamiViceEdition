"""
Settings service for application configuration
"""
import json
from core.constants import SETTINGS_FILE


class SettingsService:
    """Handle application settings persistence"""
    
    DEFAULT_SETTINGS = {
        "theme": "Miami Vice"
    }
    
    def load(self):
        """
        Load settings from file
        
        Returns:
            dict: Settings dictionary
        """
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self.DEFAULT_SETTINGS.copy()
    
    def save(self, settings):
        """
        Save settings to file
        
        Args:
            settings: Settings dictionary to save
        """
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self, key, default=None):
        """
        Get a setting value
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        settings = self.load()
        return settings.get(key, default)
    
    def set(self, key, value):
        """
        Set a setting value
        
        Args:
            key: Setting key
            value: Setting value
        """
        settings = self.load()
        settings[key] = value
        self.save(settings)
    
    def reset(self):
        """Reset settings to defaults"""
        self.save(self.DEFAULT_SETTINGS.copy())