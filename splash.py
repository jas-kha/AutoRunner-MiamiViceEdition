# ============================================================
# SPLASH SCREEN
# ============================================================

import time
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()

        self.setFixedSize(500, 300)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setStyleSheet("""
        QWidget {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #ff00cc,
                stop:1 #333399
            );
            border-radius: 20px;
        }
        QLabel {
            color: white;
            font-size: 28px;
            font-weight: bold;
        }
        """)

        layout = QVBoxLayout()
        self.setLayout(layout)

        l1 = QLabel("AutoRunner")
        l2 = QLabel("Miami Vice Edition")
        l2.setStyleSheet("font-size:18px; color:#ffddff;")

        layout.addStretch()
        layout.addWidget(l1, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(l2, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        self.show()
        QApplication.processEvents()
        time.sleep(1.4)