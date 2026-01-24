"""
Main application window
"""
import os
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QComboBox, QTabWidget, QFileDialog, QMessageBox
)

from ui.widgets.terminal_tab import TerminalTab
from ui.widgets.recent_widget import RecentWidget
from ui.widgets.favorites_widget import FavoritesWidget
from ui.themes import THEMES as themes
from core.theme_manager import ThemeManager
from services.settings_service import SettingsService


class AutoRunnerApp(QWidget):
    """Main application window"""
    
    def __init__(self, project_path=None):
        super().__init__()
        
        self.project_path = project_path
        self.settings_service = SettingsService()
        self.settings = self.settings_service.load()
        
        self._init_ui()
        self._setup_connections()
        self._load_initial_data()
        
        # Apply theme after UI is ready
        QTimer.singleShot(0, lambda: self.change_theme(
            self.settings.get("theme", "Miami Vice")
        ))
        
        # Load project if provided
        if project_path:
            self.get_current_terminal().load_project(project_path)
    
    def _init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("🌆 AutoRunner – Miami Vice Edition")
        self.setWindowIcon(QIcon("icon.ico"))
        self.setMinimumSize(1200, 750)
        self.setAcceptDrops(True)
        
        # Main layout
        root = QHBoxLayout()
        self.setLayout(root)
        
        # Left panel
        left_panel = self._create_left_panel()
        
        # Right panel
        right_panel = self._create_right_panel()
        
        root.addLayout(left_panel, 1)
        root.addLayout(right_panel, 3)
    
    def _create_left_panel(self):
        """Create left sidebar panel"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🌴 AutoRunner")
        title.setObjectName("title")
        
        subtitle = QLabel("Miami Vice Edition")
        subtitle.setObjectName("subtitle_main")
        subtitle.setStyleSheet("color: #ff8ce6; font-size: 14px;")
        
        # Theme selector
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Theme:"))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(themes.keys())
        if "theme" in self.settings:
            self.theme_combo.setCurrentText(self.settings["theme"])
        theme_row.addWidget(self.theme_combo)
        
        # Open project button
        open_btn = QPushButton("📁 Open New Project")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(self.open_folder)
        
        # Project tabs (Recent & Favorites)
        self.project_tabs = QTabWidget()
        
        self.recent_widget = RecentWidget(self)
        self.favorites_widget = FavoritesWidget(self)
        
        self.project_tabs.addTab(self.recent_widget, "📚 Recent")
        self.project_tabs.addTab(self.favorites_widget, "⭐ Favorites")
        
        # Add widgets to layout
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(theme_row)
        layout.addWidget(open_btn)
        layout.addWidget(self.project_tabs)
        
        return layout
    
    def _create_right_panel(self):
        """Create right terminal panel"""
        layout = QVBoxLayout()
        
        # Terminal tabs
        self.terminal_tabs = QTabWidget()
        self.terminal_tabs.setTabsClosable(True)
        self.terminal_tabs.tabCloseRequested.connect(self.close_terminal_tab)
        
        # Add first terminal
        self.add_terminal_tab()
        
        # Add terminal button
        add_terminal_btn = QPushButton("➕ New Terminal")
        add_terminal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_terminal_btn.clicked.connect(self.add_terminal_tab)
        
        layout.addWidget(self.terminal_tabs)
        layout.addWidget(add_terminal_btn)
        
        return layout
    
    def _setup_connections(self):
        """Setup signal-slot connections"""
        self.theme_combo.currentTextChanged.connect(self.change_theme)
    
    def _load_initial_data(self):
        """Load initial data"""
        self.recent_widget.load_recent()
        self.favorites_widget.load_favorites()
    
    def change_theme(self, theme_name):
        """Change application theme"""
        self.settings["theme"] = theme_name
        self.settings_service.save(self.settings)
        ThemeManager.apply_theme(theme_name)
    
    def add_terminal_tab(self):
        """Add new terminal tab"""
        terminal = TerminalTab(self)
        tab_name = f"Terminal {self.terminal_tabs.count() + 1}"
        self.terminal_tabs.addTab(terminal, tab_name)
        self.terminal_tabs.setCurrentWidget(terminal)
    
    def close_terminal_tab(self, index):
        """Close terminal tab"""
        if self.terminal_tabs.count() > 1:
            self.terminal_tabs.removeTab(index)
        else:
            QMessageBox.warning(self, "Warning", "Cannot close the last terminal!")
    
    def get_current_terminal(self):
        """Get currently active terminal"""
        return self.terminal_tabs.currentWidget()
    
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.accept()
    
    def dropEvent(self, event):
        """Handle drop event"""
        path = event.mimeData().urls()[0].toLocalFile()
        if os.path.isdir(path):
            self.get_current_terminal().load_project(os.path.normpath(path))
    
    def open_folder(self):
        """Open folder dialog"""
        folder = QFileDialog.getExistingDirectory(self, "Choose Project Folder")
        if folder:
            self.get_current_terminal().load_project(os.path.normpath(folder))