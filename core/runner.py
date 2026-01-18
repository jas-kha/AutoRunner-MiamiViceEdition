import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

from core.utils import strip_ansi_codes


# ============================================================
# RUNNER THREAD
# ============================================================
class RunnerThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, cmd: str, cwd: str):
        super().__init__()
        self.cmd = cmd
        self.cwd = cwd
        self.process = None
        self.running = True

    def stop(self):
        self.running = False
        if self.process and self.process.poll() is None:
            try:
                subprocess.call(
                    f"taskkill /F /T /PID {self.process.pid}",
                    shell=True
                )
            except:
                pass

    def run(self):
        try:
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
                self.log_signal.emit(strip_ansi_codes(line))

            if self.process and self.process.poll() is None:
                self.process.terminate()

        finally:
            self.finished_signal.emit()
