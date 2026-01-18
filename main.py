import sys
import json
import os
import subprocess
from datetime import datetime
from PyQt6.QtGui import QIcon, QTextCursor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QTextEdit, QFileDialog, QMessageBox, QHBoxLayout,
    QTabWidget, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, QTimer

# Load ui elements
from ui.splash import SplashScreen

# Load constants
from core.constants import RECENT_FILE, FAVORITES_FILE, SETTINGS_FILE
from core.watcher import FileWatcherThread
from core.runner import RunnerThread


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
        
        self.open_folder_btn = QPushButton("📁 Open")
        self.open_folder_btn.clicked.connect(self.open_folder)
        self.open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        quick_row.addWidget(self.open_folder_btn)
        
        self.open_vscode_btn = QPushButton("🔷 VS Code")
        self.open_vscode_btn.clicked.connect(self.open_in_vscode)
        self.open_vscode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_vscode_btn.setEnabled(False)
        quick_row.addWidget(self.open_vscode_btn)
        
        self.open_explorer_btn = QPushButton("📂 Explorer")
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
        
        self.install_btn = QPushButton("⬇️ Install")
        self.install_btn.clicked.connect(self.install_dependencies)
        self.install_btn.setEnabled(False)
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dep_row.addWidget(self.install_btn)
        
        self.reinstall_btn = QPushButton("🔄 Reinstall")
        self.reinstall_btn.clicked.connect(self.reinstall_dependencies)
        self.reinstall_btn.setEnabled(False)
        self.reinstall_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dep_row.addWidget(self.reinstall_btn)
        
        layout.addLayout(dep_row)
        
        # Run/Stop buttons
        btn_row = QHBoxLayout()
        
        self.run_btn = QPushButton("▶️ Run Script")
        self.run_btn.clicked.connect(self.run_script)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.stop_script)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.clicked.connect(self.clear_console)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.clear_btn)
        
        layout.addLayout(btn_row)
        
        # Console
        self.console = QTextEdit()
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
        self.project_path = os.path.normpath(project_path)
        self.package_manager = self.detect_package_manager(self.project_path)
        
        self.info.setText(f"📦 {os.path.basename(self.project_path)} | {self.package_manager}")
        
        if self.parent_app:
            self.parent_app.save_recent(self.project_path)
        
        pkg = os.path.join(self.project_path, "package.json")
        if not os.path.exists(pkg):
            QMessageBox.critical(self, "Error", "package.json not found!")
            return
        
        data = json.load(open(pkg, encoding="utf-8"))
        
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
        self.theme_combo.addItems(["Miami Vice", "Dark Purple", "Ocean Blue", "Sunset Orange"])
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
        
        # STYLE BUG FIX: Temani hamma widgetlar tayyor bo'lgandan keyin uramiz
        QTimer.singleShot(0, lambda: self.change_theme(self.settings.get("theme", "Miami Vice")))
        
        if project_path:
            self.get_current_terminal().load_project(project_path)
    
    def change_theme(self, theme_name):
        self.settings["theme"] = theme_name
        self.save_settings()
        
        themes = {
            "Miami Vice": """
                QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #26004d, stop:1 #004c99); color: white; font-size: 14px; }
                QLabel#title { font-size: 24px; font-weight: bold; color: #ff8ce6; background: transparent; }
                QListWidget { background: rgba(255,255,255,0.12); border-radius: 10px; padding: 5px; }
                QPushButton { background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3); border-radius: 10px; padding: 10px; }
                QPushButton:hover { background: rgba(255,255,255,0.25); }
                #console { background: rgba(0,0,0,0.35); border-radius: 10px; padding: 10px; font-family: Consolas; }
                QLineEdit, QComboBox { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.3); border-radius: 5px; padding: 5px; color: white; }
                QTabWidget::pane { border: 1px solid rgba(255,255,255,0.2); border-radius: 5px; }
                QTabBar::tab { background: rgba(255,255,255,0.1); padding: 8px 15px; border-radius: 5px; margin: 2px; }
                QTabBar::tab:selected { background: rgba(255,255,255,0.25); }
            """,

            "Dark Purple": """
                QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a0033, stop:1 #330066); color: white; font-size: 14px; }
                QLabel#title { font-size: 24px; font-weight: bold; color: #cc99ff; background: transparent; }
                QListWidget { background: rgba(255,255,255,0.12); border-radius: 10px; padding: 5px; }
                QPushButton { background: rgba(204,153,255,0.2); border: 1px solid rgba(255,255,255,0.3); border-radius: 10px; padding: 10px; }
                QPushButton:hover { background: rgba(204,153,255,0.35); }
                #console { background: rgba(0,0,0,0.4); border-radius: 10px; padding: 10px; font-family: Consolas; }
                QLineEdit, QComboBox { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.3); border-radius: 5px; padding: 5px; color: white; }
                QTabWidget::pane { border: 1px solid rgba(255,255,255,0.2); border-radius: 5px; }
                QTabBar::tab { background: rgba(255,255,255,0.1); padding: 8px 15px; border-radius: 5px; margin: 2px; }
                QTabBar::tab:selected { background: rgba(204,153,255,0.3); }
            """,

            "Ocean Blue": """
                QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #001a33, stop:1 #004080); color: white; font-size: 14px; }
                QLabel#title { font-size: 24px; font-weight: bold; color: #66ccff; background: transparent; }
                QListWidget { background: rgba(255,255,255,0.12); border-radius: 10px; padding: 5px; }
                QPushButton { background: rgba(102,204,255,0.2); border: 1px solid rgba(255,255,255,0.3); border-radius: 10px; padding: 10px; }
                QPushButton:hover { background: rgba(102,204,255,0.35); }
                #console { background: rgba(0,0,0,0.35); border-radius: 10px; padding: 10px; font-family: Consolas; }
                QLineEdit, QComboBox { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.3); border-radius: 5px; padding: 5px; color: white; }
                QTabWidget::pane { border: 1px solid rgba(255,255,255,0.2); border-radius: 5px; }
                QTabBar::tab { background: rgba(255,255,255,0.1); padding: 8px 15px; border-radius: 5px; margin: 2px; }
                QTabBar::tab:selected { background: rgba(102,204,255,0.3); }
            """,

            "Sunset Orange": """
                QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4d1a00, stop:1 #cc5200); color: white; font-size: 14px; }
                QLabel#title { font-size: 24px; font-weight: bold; color: #ffcc99; background: transparent; }
                QListWidget { background: rgba(255,255,255,0.12); border-radius: 10px; padding: 5px; }
                QPushButton { background: rgba(255,153,51,0.25); border: 1px solid rgba(255,255,255,0.3); border-radius: 10px; padding: 10px; }
                QPushButton:hover { background: rgba(255,153,51,0.4); }
                #console { background: rgba(0,0,0,0.35); border-radius: 10px; padding: 10px; font-family: Consolas; }
                QLineEdit, QComboBox { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.3); border-radius: 5px; padding: 5px; color: white; }
                QTabWidget::pane { border: 1px solid rgba(255,255,255,0.2); border-radius: 5px; }
                QTabBar::tab { background: rgba(255,255,255,0.1); padding: 8px 15px; border-radius: 5px; margin: 2px; }
                QTabBar::tab:selected { background: rgba(255,153,51,0.35); }
            """
        }
        
        style = themes.get(theme_name, themes["Miami Vice"])
        QApplication.instance().setStyleSheet(style) # Apply to whole app

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
    splash = SplashScreen()
    while splash.isVisible():
        app.processEvents()
    
    project_path = sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else None
    window = AutoRunnerApp(project_path)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
