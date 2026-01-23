import sys
import os
import json
import re
import subprocess
from datetime import datetime

# ============================================================
# Third-party imports
# ============================================================
import qtawesome as qta # pyright: ignore[reportMissingImports]

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon, QTextCursor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QFileDialog, QMessageBox, QHBoxLayout,
    QTabWidget, QLineEdit, QComboBox, QTextBrowser
)


# ============================================================
# Local imports
# ============================================================
# Load ui elements
from ui.splash import SplashScreen
from ui.themes import THEMES as themes

# Load constants and helper threads
from core.constants import RECENT_FILE, FAVORITES_FILE, SETTINGS_FILE
from core.utils import resource_path
from core.fonts import AppFonts
from core.theme_manager import ThemeManager
from core.watcher import FileWatcherThread
from core.runner import RunnerThread

app = QApplication(sys.argv)

# ============================================================
# TERMINAL TAB
# ============================================================
class TerminalTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_path = None
        self.runner = None
        self.scripts = {}
        self.package_manager = "npm"
        self.file_watcher = None
        self.parent_app = parent
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Project Info
        self.info = QLabel("No project loaded")
        self.info.setObjectName("subtitle")
        layout.addWidget(self.info)
        
        # Quick actions row
        quick_row = QHBoxLayout()
        
        self.open_folder_btn = QPushButton(" Open")
        self.open_folder_btn.setIcon(QIcon(resource_path("assets/icons/openFolder.png")))
        self.open_folder_btn.setIconSize(QSize(64, 64))
        self.open_folder_btn.clicked.connect(self.open_folder)
        self.open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        quick_row.addWidget(self.open_folder_btn)
        
        self.open_vscode_btn = QPushButton(" VS Code")
        self.open_vscode_btn.setIcon(QIcon(resource_path("assets/icons/vscode.png")))
        self.open_vscode_btn.setIconSize(QSize(64, 64))
        self.open_vscode_btn.clicked.connect(self.open_in_vscode)
        self.open_vscode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_vscode_btn.setEnabled(False)
        quick_row.addWidget(self.open_vscode_btn)
        
        self.open_explorer_btn = QPushButton(" Explorer")
        self.open_explorer_btn.setIcon(QIcon(resource_path("assets/icons/explorer.png")))
        self.open_explorer_btn.setIconSize(QSize(64, 64))
        self.open_explorer_btn.clicked.connect(self.open_in_explorer)
        self.open_explorer_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_explorer_btn.setEnabled(False)
        quick_row.addWidget(self.open_explorer_btn)
        
        layout.addLayout(quick_row)
        
        # Search box for scripts
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search scripts...")
        self.search_box.textChanged.connect(self.filter_scripts)
        layout.addWidget(self.search_box)
        
        # Script list
        self.script_list = QListWidget()
        self.script_list.itemDoubleClicked.connect(self.run_script)
        layout.addWidget(self.script_list)
        
        # Dependency buttons
        dep_row = QHBoxLayout()
        
        self.install_btn = QPushButton(" Install")
        self.install_btn.setIcon(qta.icon("fa5s.download"))
        self.install_btn.clicked.connect(self.install_dependencies)
        self.install_btn.setEnabled(False)
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dep_row.addWidget(self.install_btn)
        
        self.reinstall_btn = QPushButton(" Reinstall")
        self.reinstall_btn.setIcon(qta.icon("fa5s.sync"))
        self.reinstall_btn.clicked.connect(self.reinstall_dependencies)
        self.reinstall_btn.setEnabled(False)
        self.reinstall_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dep_row.addWidget(self.reinstall_btn)
        
        layout.addLayout(dep_row)
        
        # Run/Stop buttons
        btn_row = QHBoxLayout()
        
        self.run_btn = QPushButton(" Run Script")
        self.run_btn.setIcon(qta.icon("fa5s.play"))
        self.run_btn.clicked.connect(self.run_script)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton(" Stop")
        self.stop_btn.setIcon(qta.icon("fa5s.stop"))
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self.stop_script)
        btn_row.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton(" Clear")
        self.clear_btn.clicked.connect(self.clear_console)
        self.clear_btn.setIcon(qta.icon("fa5s.trash"))
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.clear_btn)
        
        layout.addLayout(btn_row)
        
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
        
    def filter_scripts(self, text):
        for i in range(self.script_list.count()):
            item = self.script_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Project Folder")
        if folder and os.path.isdir(folder):
            normalized_path = os.path.normpath(folder)
            self.load_project(normalized_path)
    
    def open_in_vscode(self):
        if self.project_path:
            subprocess.Popen(f'code "{self.project_path}"', shell=True)
    
    def open_in_explorer(self):
        if self.project_path:
            os.startfile(self.project_path)
    
    def clear_console(self):
        self.console.clear()
        self.log(f"<span style='color:#99ffcc;'>Console cleared at {datetime.now().strftime('%H:%M:%S')}</span>")
    
    def detect_package_manager(self, path):
        if os.path.exists(os.path.join(path, "yarn.lock")):
            return "yarn"
        if os.path.exists(os.path.join(path, "pnpm-lock.yaml")):
            return "pnpm"
        if os.path.exists(os.path.join(path, "bun.lock")) or os.path.exists(os.path.join(path, "bun.lockb")):
            return "bun"
        return "npm"
    
    def get_install_cmd(self):
        pm = self.package_manager
        return {
            "npm": "npm install",
            "yarn": "yarn",
            "pnpm": "pnpm install",
            "bun": "bun install"
        }.get(pm, "npm install")
    
    def get_run_command(self, script):
        pm = self.package_manager
        return {
            "npm": f"npm run {script}",
            "yarn": f"yarn {script}",
            "pnpm": f"pnpm run {script}",
            "bun": f"bun run {script}"
        }.get(pm, f"npm run {script}")
    
    def check_node_modules(self):
        nm = os.path.join(self.project_path, "node_modules")
        if not os.path.exists(nm):
            self.log("<span style='color:#ffcc00;'>⚠️ node_modules not found. Install needed.</span>")
            self.install_btn.setEnabled(True)
            self.reinstall_btn.setEnabled(False)
        else:
            self.log("<span style='color:#99ffcc;'>✅ node_modules detected.</span>")
            self.install_btn.setEnabled(False)
            self.reinstall_btn.setEnabled(True)
    
    def install_dependencies(self):
        cmd = self.get_install_cmd()
        self.log(f"<b>Installing:</b> {cmd}")
        self.status_label.setText("Installing dependencies...")
        
        self.runner = RunnerThread(cmd, self.project_path)
        self.runner.log_signal.connect(self.log)
        self.runner.finished_signal.connect(lambda: self.status_label.setText("Installation complete"))
        self.runner.start()
    
    def reinstall_dependencies(self):
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
        
        nm = os.path.join(self.project_path, "node_modules")
        self.log("<span style='color:#ff6666;'>🗑️ Removing node_modules...</span>")
        
        try:
            subprocess.call(f'rmdir /S /Q "{nm}"', shell=True)
        except:
            pass
        
        self.log("<span style='color:#ffaa00;'>Reinstalling dependencies...</span>")
        self.install_dependencies()
    
    def load_project(self, project_path):
        normalized_path = os.path.normpath(project_path)
        pkg = os.path.join(normalized_path, "package.json")

        # if package.json does not exist project cannot be loaded
        if not os.path.exists(pkg):
            QMessageBox.critical(self, "Error", "package.json not found!")
            return

        # Load project
        self.project_path = normalized_path
        self.package_manager = self.detect_package_manager(self.project_path)
        
        self.info.setText(f"📦 {os.path.basename(self.project_path)} | Used Package Manager {self.package_manager}")
        
        if self.parent_app:
            self.parent_app.save_recent(self.project_path)
        
        pkg = os.path.join(self.project_path, "package.json")
        if not os.path.exists(pkg):
            QMessageBox.critical(self, "Error", "package.json not found!")
            return
        
        # Load package.json
        with open(pkg, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.scripts = data.get("scripts", {})
        self.script_list.clear()

        for s in self.scripts:
            self.script_list.addItem(f"▶️ {s}")
        
        self.check_node_modules()
        self.open_vscode_btn.setEnabled(True)
        self.open_explorer_btn.setEnabled(True)
        
        # Start file watcher
        if self.file_watcher:
            self.file_watcher.stop()
        
        self.file_watcher = FileWatcherThread(self.project_path)
        self.file_watcher.file_changed.connect(self.on_file_changed)
        self.file_watcher.start()
    
    def on_file_changed(self, filename):
        self.log(f"<span style='color:#ffcc99;'>📝 File changed: {filename}</span>")
    
    def run_script(self):
        if self.runner and self.runner.isRunning():
            QMessageBox.warning(self, "Warning", "Script already running!")
            return
        
        item = self.script_list.currentItem()
        if not item:
            return
        
        script_name = item.text().replace("▶️ ", "")
        cmd = self.get_run_command(script_name)
        self.log(f"<b>Running:</b> {cmd}")
        self.status_label.setText(f"Running: {script_name}")
        
        self.runner = RunnerThread(cmd, self.project_path)
        self.runner.log_signal.connect(self.log)
        self.runner.finished_signal.connect(lambda: self.status_label.setText("Script finished"))
        self.runner.start()
    
    def stop_script(self):
        if self.runner and self.runner.isRunning():
            self.log("<span style='color:#ff3333;'>⏹️ Process stopped.</span>")
            self.status_label.setText("Stopped")
            self.runner.stop()
    
    def log(self, text):
        url_pattern = r"((http|https)://[^\s]+)"
        text = re.sub(url_pattern, r'<a href="\1" style="color:#66ccff;">\1</a>', text)

        self.console.append(text)
        # Auto-scroll to bottom
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.console.setTextCursor(cursor)
    
    def closeEvent(self, event):
        if self.runner:
            self.runner.stop()
        if self.file_watcher:
            self.file_watcher.stop()
        event.accept()


# ============================================================
# MAIN APP
# ============================================================
class AutoRunnerApp(QWidget):
    def __init__(self, project_path=None):
        super().__init__()

        self.project_path = project_path
        self.settings = self.load_settings()
        
        self.setWindowTitle("🌆 AutoRunner – Miami Vice Edition")
        self.setWindowIcon(QIcon("icon.ico"))
        self.setMinimumSize(1200, 750)
        self.setAcceptDrops(True)

        # UI yig'ish
        root = QHBoxLayout()
        self.setLayout(root)

        # Left panel
        left = QVBoxLayout()
        title = QLabel("🌴 AutoRunner")
        title.setObjectName("title")
        subtitle = QLabel("Miami Vice Edition")
        subtitle.setObjectName("subtitle_main")
        subtitle.setStyleSheet("color: #ff8ce6; font-size: 14px;")

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(themes.keys())
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        if "theme" in self.settings:
            self.theme_combo.setCurrentText(self.settings["theme"])
        theme_row.addWidget(self.theme_combo)
        
        open_btn = QPushButton("📁 Open New Project")
        open_btn.clicked.connect(self.open_folder)
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.project_tabs = QTabWidget()
        
        # Recent
        recent_widget = QWidget()
        recent_layout = QVBoxLayout(recent_widget)
        self.recent_list = QListWidget()
        self.recent_list.itemClicked.connect(self.load_recent_selected)
        recent_layout.addWidget(self.recent_list)
        
        # Favorites
        favorites_widget = QWidget()
        favorites_layout = QVBoxLayout(favorites_widget)
        self.favorites_list = QListWidget()
        self.favorites_list.itemClicked.connect(self.load_favorite_selected)
        favorites_layout.addWidget(self.favorites_list)
        
        fav_btn_row = QHBoxLayout()
        add_fav_btn = QPushButton("⭐ Add to Favorites")
        add_fav_btn.clicked.connect(self.add_to_favorites)
        remove_fav_btn = QPushButton("❌ Remove")
        remove_fav_btn.clicked.connect(self.remove_from_favorites)
        fav_btn_row.addWidget(add_fav_btn)
        fav_btn_row.addWidget(remove_fav_btn)
        favorites_layout.addLayout(fav_btn_row)
        
        self.project_tabs.addTab(recent_widget, "📚 Recent")
        self.project_tabs.addTab(favorites_widget, "⭐ Favorites")

        left.addWidget(title)
        left.addWidget(subtitle)
        left.addLayout(theme_row)
        left.addWidget(open_btn)
        left.addWidget(self.project_tabs)

        # Right panel
        self.terminal_tabs = QTabWidget()
        self.terminal_tabs.setTabsClosable(True)
        self.terminal_tabs.tabCloseRequested.connect(self.close_terminal_tab)
        
        self.add_terminal_tab()
        
        add_terminal_btn = QPushButton("➕ New Terminal")
        add_terminal_btn.clicked.connect(self.add_terminal_tab)
        add_terminal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        right = QVBoxLayout()
        right.addWidget(self.terminal_tabs)
        right.addWidget(add_terminal_btn)

        root.addLayout(left, 1)
        root.addLayout(right, 3)

        self.load_recent()
        self.load_favorites()
        
        # Style BUG FIX: Apply theme after all widgets are ready
        QTimer.singleShot(0, lambda: self.change_theme(self.settings.get("theme", "Miami Vice")))
        
        if project_path:
            self.get_current_terminal().load_project(project_path)
    
    def change_theme(self, theme_name):
        self.settings["theme"] = theme_name
        self.save_settings()
        ThemeManager.apply_theme(theme_name)

    def add_terminal_tab(self):
        terminal = TerminalTab(self)
        tab_name = f"Terminal {self.terminal_tabs.count() + 1}"
        self.terminal_tabs.addTab(terminal, tab_name)
        self.terminal_tabs.setCurrentWidget(terminal)

    def close_terminal_tab(self, index):
        if self.terminal_tabs.count() > 1:
            self.terminal_tabs.removeTab(index)
        else:
            QMessageBox.warning(self, "Warning", "Cannot close the last terminal!")

    def get_current_terminal(self):
        return self.terminal_tabs.currentWidget()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()

    def dropEvent(self, event):
        p = event.mimeData().urls()[0].toLocalFile()
        if os.path.isdir(p):
            self.get_current_terminal().load_project(os.path.normpath(p))

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Project Folder")
        if folder: self.get_current_terminal().load_project(os.path.normpath(folder))

    def load_recent(self):
        paths = self.read_recent()
        self.recent_list.clear()
        for p in paths:
            if os.path.isdir(p):
                self.recent_list.addItem(f"📁 {os.path.basename(p)}\n   {p}")

    def save_recent(self, path):
        paths = self.read_recent()
        if path in paths: paths.remove(path)
        paths.insert(0, path)
        with open(RECENT_FILE, "w", encoding="utf-8") as f:
            json.dump(paths[:10], f, indent=2)
        self.load_recent()

    def read_recent(self):
        try:
            with open(RECENT_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return []

    def load_recent_selected(self):
        item = self.recent_list.currentItem()
        if item:
            path = item.text().split('\n')[-1].strip()
            self.get_current_terminal().load_project(path)

    def load_favorites(self):
        favs = self.read_favorites()
        self.favorites_list.clear()
        for p in favs:
            if os.path.isdir(p):
                self.favorites_list.addItem(f"⭐ {os.path.basename(p)}\n   {p}")

    def add_to_favorites(self):
        item = self.recent_list.currentItem()
        if not item: return
        path = item.text().split('\n')[-1].strip()
        favs = self.read_favorites()
        if path not in favs:
            favs.append(path)
            with open(FAVORITES_FILE, "w", encoding="utf-8") as f: json.dump(favs, f, indent=2)
            self.load_favorites()

    def remove_from_favorites(self):
        item = self.favorites_list.currentItem()
        if not item: return
        path = item.text().split('\n')[-1].strip()
        favs = self.read_favorites()
        if path in favs:
            favs.remove(path)
            with open(FAVORITES_FILE, "w", encoding="utf-8") as f: json.dump(favs, f, indent=2)
            self.load_favorites()

    def load_favorite_selected(self):
        item = self.favorites_list.currentItem()
        if item:
            path = item.text().split('\n')[-1].strip()
            self.get_current_terminal().load_project(path)

    def read_favorites(self):
        try:
            with open(FAVORITES_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return []

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {"theme": "Miami Vice"}

    def save_settings(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f: json.dump(self.settings, f, indent=2)


def main():
    app = QApplication(sys.argv)
    AppFonts.load()
    splash = SplashScreen()
    while splash.isVisible():
        app.processEvents()
    
    project_path = sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else None
    window = AutoRunnerApp(project_path)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
