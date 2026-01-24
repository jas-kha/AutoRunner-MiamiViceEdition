"""
File service for project operations
"""
import os
import json
import subprocess


class FileService:
    """Handle file and directory operations for projects"""
    
    @staticmethod
    def has_package_json(project_path):
        """
        Check if package.json exists
        
        Args:
            project_path: Path to project directory
            
        Returns:
            bool: True if package.json exists
        """
        package_json = os.path.join(project_path, "package.json")
        return os.path.exists(package_json)
    
    @staticmethod
    def has_node_modules(project_path):
        """
        Check if node_modules directory exists
        
        Args:
            project_path: Path to project directory
            
        Returns:
            bool: True if node_modules exists
        """
        node_modules = os.path.join(project_path, "node_modules")
        return os.path.exists(node_modules)
    
    @staticmethod
    def load_scripts(project_path):
        """
        Load scripts from package.json
        
        Args:
            project_path: Path to project directory
            
        Returns:
            dict: Scripts from package.json
        """
        package_json = os.path.join(project_path, "package.json")
        
        try:
            with open(package_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("scripts", {})
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    @staticmethod
    def remove_node_modules(project_path):
        """
        Remove node_modules directory
        
        Args:
            project_path: Path to project directory
        """
        node_modules = os.path.join(project_path, "node_modules")
        
        if os.path.exists(node_modules):
            try:
                subprocess.call(f'rmdir /S /Q "{node_modules}"', shell=True)
            except Exception as e:
                print(f"Error removing node_modules: {e}")
    
    @staticmethod
    def load_package_info(project_path):
        """
        Load package.json metadata
        
        Args:
            project_path: Path to project directory
            
        Returns:
            dict: Package metadata or empty dict
        """
        package_json = os.path.join(project_path, "package.json")
        
        try:
            with open(package_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}