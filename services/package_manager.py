"""
Package manager service for npm, yarn, pnpm, and bun
"""
import os


class PackageManagerService:
    """Handle package manager detection and command generation"""
    
    MANAGERS = {
        "npm": {
            "install": "npm install",
            "run": "npm run {script}"
        },
        "yarn": {
            "install": "yarn",
            "run": "yarn {script}"
        },
        "pnpm": {
            "install": "pnpm install",
            "run": "pnpm run {script}"
        },
        "bun": {
            "install": "bun install",
            "run": "bun run {script}"
        }
    }
    
    LOCK_FILES = {
        "yarn.lock": "yarn",
        "pnpm-lock.yaml": "pnpm",
        "bun.lock": "bun",
        "bun.lockb": "bun"
    }
    
    def __init__(self):
        self.package_manager = "npm"  # Default
    
    def detect_package_manager(self, project_path):
        """
        Detect package manager by lock file
        
        Args:
            project_path: Path to project directory
            
        Returns:
            str: Package manager name (npm, yarn, pnpm, bun)
        """
        for lock_file, manager in self.LOCK_FILES.items():
            if os.path.exists(os.path.join(project_path, lock_file)):
                self.package_manager = manager
                return manager
        
        self.package_manager = "npm"
        return "npm"
    
    def get_install_command(self):
        """
        Get install command for current package manager
        
        Returns:
            str: Install command
        """
        return self.MANAGERS[self.package_manager]["install"]
    
    def get_run_command(self, script_name):
        """
        Get run command for a script
        
        Args:
            script_name: Name of the script to run
            
        Returns:
            str: Run command
        """
        template = self.MANAGERS[self.package_manager]["run"]
        return template.format(script=script_name)
    
    def set_package_manager(self, manager_name):
        """
        Manually set package manager
        
        Args:
            manager_name: Package manager name
            
        Raises:
            ValueError: If manager not supported
        """
        if manager_name not in self.MANAGERS:
            raise ValueError(f"Unsupported package manager: {manager_name}")
        
        self.package_manager = manager_name