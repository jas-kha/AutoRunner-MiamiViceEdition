"""
Terminal tab widget for running scripts
"""
import os
import re
import subprocess
from datetime import datetime

import qtawesome as qta
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QTextCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QListWidget, QTextBrowser, QMessageBox
)

from core.utils import resource_path
from core.watcher import FileWatcherThread
from core.runner import RunnerThread
from services.package_manager import PackageManagerService
from services.file_service import FileService


class TerminalTab(QWidget):
    """Terminal tab for project management and script execution"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.project_path = None
        self.runner = None
        self.scripts = {}
        self.file_watcher = None
        self.parent_app = parent
        
        self.package_service = PackageManagerService()
        self.file_service = FileService()
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Project info
        self.info = QLabel("No project loaded")
        self.info.setObjectName("subtitle")
        layout.addWidget(self.info)
        
        # Quick actions
        layout.addLayout(self._create_quick_actions())
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search scripts...")
        self.search_box.textChanged.connect(self.filter_scripts)
        layout.addWidget(self.search_box)
        
        # Script list
        self.script_list = QListWidget()
        self.script_list.itemDoubleClicked.connect(self.run_script)
        layout.addWidget(self.script_list)
        
        # Dependency buttons
        layout.addLayout(self._create_dependency_buttons())
        
        # Run/Stop buttons
        layout.addLayout(self._create_control_buttons())
        
        # Console
        self.console = QTextBrowser()
        self.console.setOpenExternalLinks(True)
        self.console.setOpenLinks(True)
        self.console.setReadOnly(True)
        self.console.setObjectName("console")
        layout.addWidget(self.console)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #99ffcc; font-size: 12px;")
        layout.addWidget(self.status_label)
    
    def _create_quick_actions(self):
        """Create quick action buttons"""
        row = QHBoxLayout()
        
        self.open_folder_btn = QPushButton(" Open")
        self.open_folder_btn.setIcon(QIcon(resource_path("assets/icons/openFolder.png")))
        self.open_folder_btn.setIconSize(QSize(64, 64))
        self.open_folder_btn.clicked.connect(self.open_folder)
        self.open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.open_vscode_btn = QPushButton(" VS Code")
        self.open_vscode_btn.setIcon(QIcon(resource_path("assets/icons/vscode.png")))
        self.open_vscode_btn.setIconSize(QSize(64, 64))
        self.open_vscode_btn.clicked.connect(self.open_in_vscode)
        self.open_vscode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_vscode_btn.setEnabled(False)
        
        self.open_explorer_btn = QPushButton(" Explorer")
        self.open_explorer_btn.setIcon(QIcon(resource_path("assets/icons/explorer.png")))
        self.open_explorer_btn.setIconSize(QSize(64, 64))
        self.open_explorer_btn.clicked.connect(self.open_in_explorer)
        self.open_explorer_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_explorer_btn.setEnabled(False)
        
        row.addWidget(self.open_folder_btn)
        row.addWidget(self.open_vscode_btn)
        row.addWidget(self.open_explorer_btn)
        
        return row
    
    def _create_dependency_buttons(self):
        """Create dependency management buttons"""
        row = QHBoxLayout()
        
        self.install_btn = QPushButton(" Install")
        self.install_btn.setIcon(qta.icon("fa5s.download"))
        self.install_btn.clicked.connect(self.install_dependencies)
        self.install_btn.setEnabled(False)
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.reinstall_btn = QPushButton(" Reinstall")
        self.reinstall_btn.setIcon(qta.icon("fa5s.sync"))
        self.reinstall_btn.clicked.connect(self.reinstall_dependencies)
        self.reinstall_btn.setEnabled(False)
        self.reinstall_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        row.addWidget(self.install_btn)
        row.addWidget(self.reinstall_btn)
        
        return row
    
    def _create_control_buttons(self):
        """Create script control buttons"""
        row = QHBoxLayout()
        
        self.run_btn = QPushButton(" Run Script")
        self.run_btn.setIcon(qta.icon("fa5s.play"))
        self.run_btn.clicked.connect(self.run_script)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.stop_btn = QPushButton(" Stop")
        self.stop_btn.setIcon(qta.icon("fa5s.stop"))
        self.stop_btn.clicked.connect(self.stop_script)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.clear_btn = QPushButton(" Clear")
        self.clear_btn.setIcon(qta.icon("fa5s.trash"))
        self.clear_btn.clicked.connect(self.clear_console)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        row.addWidget(self.run_btn)
        row.addWidget(self.stop_btn)
        row.addWidget(self.clear_btn)
        
        return row
    
    def filter_scripts(self, text):
        """Filter script list by search text"""
        for i in range(self.script_list.count()):
            item = self.script_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def open_folder(self):
        """Open folder dialog"""
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Choose Project Folder")
        if folder and os.path.isdir(folder):
            self.load_project(os.path.normpath(folder))
    
    def open_in_vscode(self):
        """Open project in VS Code"""
        if self.project_path:
            subprocess.Popen(f'code "{self.project_path}"', shell=True)
    
    def open_in_explorer(self):
        """Open project in file explorer"""
        if self.project_path:
            os.startfile(self.project_path)
    
    def clear_console(self):
        """Clear console output"""
        self.console.clear()
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log(f"<span style='color:#99ffcc;'>Console cleared at {timestamp}</span>")
    
    def check_node_modules(self):
        """Check if node_modules exists"""
        has_modules = self.file_service.has_node_modules(self.project_path)
        
        if not has_modules:
            self.log("<span style='color:#ffcc00;'>⚠️ node_modules not found. Install needed.</span>")
            self.install_btn.setEnabled(True)
            self.reinstall_btn.setEnabled(False)
        else:
            self.log("<span style='color:#99ffcc;'>✅ node_modules detected.</span>")
            self.install_btn.setEnabled(False)
            self.reinstall_btn.setEnabled(True)
    
    def install_dependencies(self):
        """Install project dependencies"""
        cmd = self.package_service.get_install_command()
        self.log(f"<b>Installing:</b> {cmd}")
        self.status_label.setText("Installing dependencies...")
        
        self.runner = RunnerThread(cmd, self.project_path)
        self.runner.log_signal.connect(self.log)
        self.runner.finished_signal.connect(
            lambda: self.status_label.setText("Installation complete")
        )
        self.runner.start()
    
    def reinstall_dependencies(self):
        """Reinstall dependencies (remove and install)"""
        reply = QMessageBox.question(
            self,
            "Confirm Reinstall",
            "Are you sure you want to reinstall dependencies?\n"
            "This will completely remove the 'node_modules' folder.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            self.log("<span style='color:#ffaa00;'>Reinstall canceled.</span>")
            return
        
        self.log("<span style='color:#ff6666;'>🗑️ Removing node_modules...</span>")
        self.file_service.remove_node_modules(self.project_path)
        
        self.log("<span style='color:#ffaa00;'>Reinstalling dependencies...</span>")
        self.install_dependencies()
    
    def load_project(self, project_path):
        """Load a project"""
        normalized_path = os.path.normpath(project_path)
        
        # Validate package.json
        if not self.file_service.has_package_json(normalized_path):
            QMessageBox.critical(self, "Error", "package.json not found!")
            return
        
        # Set project
        self.project_path = normalized_path
        
        # Detect package manager
        self.package_service.detect_package_manager(self.project_path)
        
        # Update UI
        project_name = os.path.basename(self.project_path)
        pm_name = self.package_service.package_manager
        self.info.setText(f"📦 {project_name} | Package Manager: {pm_name}")
        
        # Save to recent
        if self.parent_app:
            self.parent_app.recent_widget.save_recent(self.project_path)
        
        # Load scripts
        scripts = self.file_service.load_scripts(self.project_path)
        self.scripts = scripts
        
        self.script_list.clear()
        for script_name in scripts:
            self.script_list.addItem(f"▶️ {script_name}")
        
        # Check dependencies
        self.check_node_modules()
        
        # Enable buttons
        self.open_vscode_btn.setEnabled(True)
        self.open_explorer_btn.setEnabled(True)
        
        # Start file watcher
        if self.file_watcher:
            self.file_watcher.stop()
        
        self.file_watcher = FileWatcherThread(self.project_path)
        self.file_watcher.file_changed.connect(self.on_file_changed)
        self.file_watcher.start()
    
    def on_file_changed(self, filename):
        """Handle file change event"""
        self.log(f"<span style='color:#ffcc99;'>📝 File changed: {filename}</span>")
    
    def run_script(self):
        """Run selected script"""
        if self.runner and self.runner.isRunning():
            QMessageBox.warning(self, "Warning", "Script already running!")
            return
        
        item = self.script_list.currentItem()
        if not item:
            return
        
        script_name = item.text().replace("▶️ ", "")
        cmd = self.package_service.get_run_command(script_name)
        
        self.log(f"<b>Running:</b> {cmd}")
        self.status_label.setText(f"Running: {script_name}")
        
        self.runner = RunnerThread(cmd, self.project_path)
        self.runner.log_signal.connect(self.log)
        self.runner.finished_signal.connect(
            lambda: self.status_label.setText("Script finished")
        )
        self.runner.start()
    
    def stop_script(self):
        """Stop running script"""
        if self.runner and self.runner.isRunning():
            self.log("<span style='color:#ff3333;'>⏹️ Process stopped.</span>")
            self.status_label.setText("Stopped")
            self.runner.stop()
    
    def log(self, text):
        """Log message to console"""
        # Convert URLs to clickable links
        url_pattern = r"((http|https)://[^\s]+)"
        text = re.sub(url_pattern, r'<a href="\1" style="color:#66ccff;">\1</a>', text)
        
        self.console.append(text)
        
        # Auto-scroll to bottom
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.console.setTextCursor(cursor)
    
    def closeEvent(self, event):
        """Handle close event"""
        if self.runner:
            self.runner.stop()
        if self.file_watcher:
            self.file_watcher.stop()
        event.accept()