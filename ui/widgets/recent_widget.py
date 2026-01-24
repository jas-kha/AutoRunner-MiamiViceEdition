"""
Recent projects widget
"""
import os
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget

from core.constants import RECENT_FILE


class RecentWidget(QWidget):
    """Widget for displaying recent projects"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        
        layout = QVBoxLayout(self)
        
        self.recent_list = QListWidget()
        self.recent_list.itemClicked.connect(self.load_recent_selected)
        layout.addWidget(self.recent_list)
    
    def load_recent(self):
        """Load and display recent projects"""
        paths = self.read_recent()
        self.recent_list.clear()
        
        for path in paths:
            if os.path.isdir(path):
                project_name = os.path.basename(path)
                self.recent_list.addItem(f"📁 {project_name}\n   {path}")
    
    def save_recent(self, path):
        """
        Save project to recent list
        
        Args:
            path: Project path to save
        """
        paths = self.read_recent()
        
        # Remove if already exists (to move to top)
        if path in paths:
            paths.remove(path)
        
        # Add to beginning
        paths.insert(0, path)
        
        # Keep only last 10
        paths = paths[:10]
        
        try:
            with open(RECENT_FILE, "w", encoding="utf-8") as f:
                json.dump(paths, f, indent=2)
        except Exception as e:
            print(f"Error saving recent: {e}")
        
        self.load_recent()
    
    def read_recent(self):
        """
        Read recent projects from file
        
        Returns:
            list: List of recent project paths
        """
        try:
            with open(RECENT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def load_recent_selected(self):
        """Load selected recent project"""
        item = self.recent_list.currentItem()
        if not item:
            return
        
        # Extract path from item text
        path = item.text().split('\n')[-1].strip()
        
        if self.parent_app:
            terminal = self.parent_app.get_current_terminal()
            terminal.load_project(path)