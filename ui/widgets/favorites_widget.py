"""
Favorites projects widget
"""
import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QPushButton
)

from core.constants import FAVORITES_FILE


class FavoritesWidget(QWidget):
    """Widget for displaying favorite projects"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        
        layout = QVBoxLayout(self)
        
        # Favorites list
        self.favorites_list = QListWidget()
        self.favorites_list.itemClicked.connect(self.load_favorite_selected)
        layout.addWidget(self.favorites_list)
        
        # Buttons
        btn_row = QHBoxLayout()
        
        add_btn = QPushButton("⭐ Add to Favorites")
        add_btn.clicked.connect(self.add_to_favorites)
        
        remove_btn = QPushButton("❌ Remove")
        remove_btn.clicked.connect(self.remove_from_favorites)
        
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        
        layout.addLayout(btn_row)
    
    def load_favorites(self):
        """Load and display favorite projects"""
        paths = self.read_favorites()
        self.favorites_list.clear()
        
        for path in paths:
            if os.path.isdir(path):
                project_name = os.path.basename(path)
                self.favorites_list.addItem(f"⭐ {project_name}\n   {path}")
    
    def add_to_favorites(self):
        """Add selected recent project to favorites"""
        if not self.parent_app:
            return
        
        recent_widget = self.parent_app.recent_widget
        item = recent_widget.recent_list.currentItem()
        
        if not item:
            return
        
        # Extract path
        path = item.text().split('\n')[-1].strip()
        
        # Add to favorites
        favs = self.read_favorites()
        if path not in favs:
            favs.append(path)
            self.write_favorites(favs)
            self.load_favorites()
    
    def remove_from_favorites(self):
        """Remove selected project from favorites"""
        item = self.favorites_list.currentItem()
        if not item:
            return
        
        # Extract path
        path = item.text().split('\n')[-1].strip()
        
        # Remove from favorites
        favs = self.read_favorites()
        if path in favs:
            favs.remove(path)
            self.write_favorites(favs)
            self.load_favorites()
    
    def load_favorite_selected(self):
        """Load selected favorite project"""
        item = self.favorites_list.currentItem()
        if not item:
            return
        
        # Extract path
        path = item.text().split('\n')[-1].strip()
        
        if self.parent_app:
            terminal = self.parent_app.get_current_terminal()
            terminal.load_project(path)
    
    def read_favorites(self):
        """
        Read favorites from file
        
        Returns:
            list: List of favorite project paths
        """
        try:
            with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def write_favorites(self, favorites):
        """
        Write favorites to file
        
        Args:
            favorites: List of favorite paths
        """
        try:
            with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
                json.dump(favorites, f, indent=2)
        except Exception as e:
            print(f"Error writing favorites: {e}")