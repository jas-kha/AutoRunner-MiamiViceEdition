import sys
import json
import os
import subprocess

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QTextEdit, QFileDialog, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from scripts import APP_NAME, APP_PUBLISHER
from splash import SplashScreen


RECENT_FILE = "recent.json"

RECENT_FILE = os.path.join(
    os.getenv("APPDATA"),
    APP_PUBLISHER,
    APP_NAME,
    "recent.json"
)

os.makedirs(os.path.dirname(RECENT_FILE), exist_ok=True)


# ============================================================
# RUNNER THREAD
# ============================================================
class RunnerThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, cmd, cwd):
        super().__init__()
        self.cmd = cmd
        self.cwd = cwd
        self.process = None
        self.running = True

    def stop(self):
        self.running = False
        if self.process and self.process.poll() is None:
            try:
                subprocess.call(f"taskkill /F /T /PID {self.process.pid}", shell=True)
            except:
                pass

    def run(self):
        self.process = subprocess.Popen(
            self.cmd,
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )

        for line in self.process.stdout:
            if not self.running:
                break
            self.log_signal.emit(line)

        if self.process and self.process.poll() is None:
            self.process.terminate()


# ============================================================
# MAIN APP
# ============================================================
class AutoRunnerApp(QWidget):
    def __init__(self, project_path=None):
        super().__init__()

        self.project_path = project_path
        self.runner = None
        self.scripts = {}
        self.package_manager = "npm"

        self.setWindowTitle("AutoRunner – Miami Vice Edition")
        self.setWindowIcon(QIcon("icon.ico"))
        self.setMinimumSize(1000, 680)
        self.setAcceptDrops(True)

        self.setStyleSheet(self.miami_style())

        root = QHBoxLayout()
        self.setLayout(root)

        # Left panel ---------------------
        left = QVBoxLayout()

        title = QLabel("Recent Projects")
        title.setObjectName("title")

        open_btn = QPushButton("Open Folder")
        open_btn.clicked.connect(self.open_folder)
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.recent_list = QListWidget()
        self.recent_list.itemClicked.connect(self.load_recent_selected)

        left.addWidget(title)
        left.addWidget(open_btn)
        left.addWidget(self.recent_list)

        # Right panel ---------------------
        right = QVBoxLayout()

        self.info = QLabel("No project loaded")
        self.info.setObjectName("subtitle")
        right.addWidget(self.info)

        self.script_list = QListWidget()
        right.addWidget(self.script_list)

        # DEPENDENCY BUTTONS
        dep_row = QHBoxLayout()

        self.install_btn = QPushButton("Install Dependencies")
        self.install_btn.clicked.connect(self.install_dependencies)
        self.install_btn.setEnabled(False)
        dep_row.addWidget(self.install_btn)
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.reinstall_btn = QPushButton("Re-Install Dependencies")
        self.reinstall_btn.clicked.connect(self.reinstall_dependencies)
        self.reinstall_btn.setEnabled(False)
        self.reinstall_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dep_row.addWidget(self.reinstall_btn)

        right.addLayout(dep_row)

        # Run/Stop buttons
        btn_row = QHBoxLayout()

        self.run_btn = QPushButton("Run Script")
        self.run_btn.clicked.connect(self.run_script)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.run_btn)

        self.stop_btn = QPushButton("Exit Script")
        self.stop_btn.clicked.connect(self.stop_script)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.stop_btn)

        right.addLayout(btn_row)

        # console
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setObjectName("console")
        right.addWidget(self.console)

        root.addLayout(left, 1)
        root.addLayout(right, 2)

        self.load_recent()
        if project_path:
            self.load_project(project_path)

    # ============================================================
    # Drag & Drop
    # ============================================================
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()

    def dropEvent(self, event):
        p = event.mimeData().urls()[0].toLocalFile()
        if os.path.isdir(p):
            self.load_project(p)

    # ============================================================
    # Detect Package Manager
    # ============================================================
    def detect_package_manager(self, path):
        if os.path.exists(os.path.join(path, "yarn.lock")):
            return "yarn"
        if os.path.exists(os.path.join(path, "pnpm-lock.yaml")):
            return "pnpm"
        if os.path.exists(os.path.join(path, "bun.lock")):
            return "bun"
        if os.path.exists(os.path.join(path, "bun.lockb")):
            return "bun"
        return "npm"

    def get_install_cmd(self):
        pm = self.package_manager
        if pm == "npm":
            return "npm install"
        if pm == "yarn":
            return "yarn"
        if pm == "pnpm":
            return "pnpm install"
        if pm == "bun":
            return "bun install"

    def get_run_command(self, script):
        pm = self.package_manager
        if pm == "npm":
            return f"npm run {script}"
        if pm == "yarn":
            return f"yarn {script}"
        if pm == "pnpm":
            return f"pnpm run {script}"
        if pm == "bun":
            return f"bun run {script}"

    # ============================================================
    # Check node_modules
    # ============================================================
    def check_node_modules(self):
        nm = os.path.join(self.project_path, "node_modules")

        if not os.path.exists(nm):
            self.console.append("<span style='color:#ffcc00;'>node_modules not found. Install needed.</span><br>")
            self.install_btn.setEnabled(True)
            self.reinstall_btn.setEnabled(False)
        else:
            self.console.append("<span style='color:#99ffcc;'>node_modules detected.</span><br>")
            self.install_btn.setEnabled(False)
            self.reinstall_btn.setEnabled(True)

    # ============================================================
    # Install / Reinstall
    # ============================================================
    def install_dependencies(self):
        cmd = self.get_install_cmd()
        self.console.append(f"<b>Installing:</b> {cmd}<br>")

        self.runner = RunnerThread(cmd, self.project_path)
        self.runner.log_signal.connect(self.output_log)
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
            self.console.append("<span style='color:#ffaa00;'>Reinstall canceled by user.</span><br>")
            return

        nm = os.path.join(self.project_path, "node_modules")
        self.console.append("<span style='color:#ff6666;'>Removing node_modules...</span><br>")

        try:
            subprocess.call(f'rmdir /S /Q "{nm}"', shell=True)
        except:
            pass

        self.console.append("<span style='color:#ffaa00;'>Reinstalling dependencies...</span><br>")
        self.install_dependencies()

    # ============================================================
    # Style
    # ============================================================
    def miami_style(self):
        return """
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #26004d, stop:1 #004c99 );
            color: white;
            font-size: 14px;
        }
        #title {
            font-size: 20px;
            font-weight: bold;
            color: #ff8ce6;
        }
        #subtitle {
            font-size: 17px;
            color: #b3e6ff;
        }
        QListWidget {
            background: rgba(255,255,255,0.12);
            border-radius: 10px;
            padding: 5px;
        }
        QPushButton {
            background: rgba(255,255,255,0.15);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 10px;
            padding: 10px;
        }
        #console {
            background: rgba(0,0,0,0.35);
            border-radius: 10px;
            padding: 10px;
            font-family: Consolas;
        }
        """
    
    # ============================================================
    # OPEN FOLDER
    # ============================================================
    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Project Folder")
        if folder and os.path.isdir(folder):
            self.load_project(folder)

    # ============================================================
    # Recent List
    # ============================================================
    def load_recent(self):
        paths = self.read_recent()

        paths = [p for p in paths if os.path.isdir(p)]
        self.write_recent(paths)

        self.recent_list.clear()
        for p in paths:
            self.recent_list.addItem(p)


    def save_recent(self, path):
        paths = self.read_recent()

        if path not in paths:
            paths.insert(0, path)

        self.write_recent(paths[:10])
        self.load_recent()


    def load_recent_selected(self):
        item = self.recent_list.currentItem()
        if not item:
            return
        self.load_project(item.text())

    def read_recent(self):
        os.makedirs(os.path.dirname(RECENT_FILE), exist_ok=True)

        try:
            with open(RECENT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []

    def write_recent(self, paths):
        with open(RECENT_FILE, "w", encoding="utf-8") as f:
            json.dump(paths, f, indent=2)


    # ============================================================
    # Load Project
    # ============================================================
    def load_project(self, project_path):
        self.project_path = project_path
        self.package_manager = self.detect_package_manager(project_path)

        self.info.setText(f"Project: {project_path}  |  PM: {self.package_manager}")
        self.save_recent(project_path)

        pkg = os.path.join(project_path, "package.json")
        if not os.path.exists(pkg):
            QMessageBox.critical(self, "Error", "package.json not found!")
            return

        data = json.load(open(pkg, encoding="utf-8"))

        self.scripts = data.get("scripts", {})
        self.script_list.clear()
        for s in self.scripts:
            self.script_list.addItem(s)

        self.check_node_modules()

    # ============================================================
    # Run / Stop Script
    # ============================================================
    def run_script(self):
        if self.runner and self.runner.isRunning():
            QMessageBox.warning(self, "Warning", "Script already running!")
            return

        item = self.script_list.currentItem()
        if not item:
            return

        cmd = self.get_run_command(item.text())
        self.console.append(f"<b>Running:</b> {cmd}<br>")

        self.runner = RunnerThread(cmd, self.project_path)
        self.runner.log_signal.connect(self.output_log)
        self.runner.start()

    def stop_script(self):
        if self.runner and self.runner.isRunning():
            self.console.append("<span style='color:#ff3333;'>Process stopped.</span><br>")
            self.runner.stop()

    def output_log(self, text):
        self.console.append(text)


# ============================================================
# MAIN
# ============================================================
def main():
    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.close()

    project_path = None
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        project_path = sys.argv[1]

    window = AutoRunnerApp(project_path)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
