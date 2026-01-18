import os
from PyQt6.QtCore import QThread, pyqtSignal


class FileWatcherThread(QThread):
    file_changed = pyqtSignal(str)

    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self.running = True
        self.last_modified = {}

    def stop(self):
        self.running = False

    def run(self):
        while self.running:
            try:
                if not self.path or not os.path.exists(self.path):
                    break

                for root, dirs, files in os.walk(self.path):
                    dirs[:] = [
                        d for d in dirs
                        if d not in ['node_modules', '.git', 'dist', 'build']
                    ]

                    for file in files:
                        if file.endswith(('.js', '.ts', '.jsx', '.tsx', '.json')):
                            filepath = os.path.join(root, file)
                            try:
                                mtime = os.path.getmtime(filepath)
                                if filepath in self.last_modified:
                                    if mtime > self.last_modified[filepath]:
                                        self.file_changed.emit(file)
                                self.last_modified[filepath] = mtime
                            except:
                                pass
            except:
                pass

            self.msleep(2000)
