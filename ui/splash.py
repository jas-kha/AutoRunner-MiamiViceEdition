# ============================================================
# ENHANCED SPLASH SCREEN
# ============================================================

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QProgressBar
from PyQt6.QtGui import QFont, QPainter, QLinearGradient, QColor, QPen
from core.fonts import AppFonts

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()

        self.setFixedSize(600, 400)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.progress = 0

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        self.title = QLabel("🌆 Auto Runner")
        self.title.setFont(AppFonts.bold(32))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # title_font = QFont("Arial", 32, QFont.Weight.Bold)
        # self.title.setFont(title_font)
        self.title.setStyleSheet("""
            color: white;
            background: transparent;
        """)

        # Subtitle
        self.subtitle = QLabel("Miami Vice Edition")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont("Arial", 16)
        self.subtitle.setFont(AppFonts.bold(16))
        self.subtitle.setStyleSheet("""
            color: #ffddff;
            background: transparent;
        """)

        # Version label
        self.version = QLabel("v0.2.2.1 • Enhanced Edition")
        self.version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_font = QFont("Arial", 10)
        self.version.setFont(version_font)
        self.version.setStyleSheet("""
            color: #b3e6ff;
            background: transparent;
        """)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff00cc,
                    stop:0.5 #ff66dd,
                    stop:1 #ff00cc
                );
                border-radius: 4px;
            }
        """)

        # Status label
        self.status = QLabel("Initializing...")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont("Arial", 11)
        self.status.setFont(status_font)
        self.status.setStyleSheet("""
            color: #99ffcc;
            background: transparent;
        """)

        # Feature labels
        self.feature1 = QLabel("✨ Dual Terminal Support")
        self.feature1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feature1.setStyleSheet("color: #ffcc99; background: transparent; font-size: 10px;")
        
        self.feature2 = QLabel("🎨 Multiple Themes")
        self.feature2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feature2.setStyleSheet("color: #ccff99; background: transparent; font-size: 10px;")
        
        self.feature3 = QLabel("⚡ Smart File Watching")
        self.feature3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feature3.setStyleSheet("color: #99ccff; background: transparent; font-size: 10px;")

        # Add widgets to layout
        layout.addStretch()
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addWidget(self.version)
        layout.addSpacing(20)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status)
        layout.addSpacing(20)
        layout.addWidget(self.feature1)
        layout.addWidget(self.feature2)
        layout.addWidget(self.feature3)
        layout.addStretch()

        self.show()
        QApplication.processEvents()

        # Animate progress
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(30)  # Update every 30ms

        # Fade in animation
        self.setWindowOpacity(0)
        self.fade_in()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create gradient background
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(255, 0, 204, 230))  # #ff00cc
        gradient.setColorAt(0.5, QColor(138, 43, 226, 230))  # Purple
        gradient.setColorAt(1, QColor(51, 51, 153, 230))  # #333399

        # Draw background with rounded corners
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 25, 25)

        # Draw border glow
        pen = QPen(QColor(255, 255, 255, 100))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 25, 25)

    def fade_in(self):
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.fade_animation.start()

    def fade_out(self):
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()

    def update_progress(self):
        self.progress += 2
        self.progress_bar.setValue(self.progress)

        # Update status text
        if self.progress < 30:
            self.status.setText("Loading modules...")
        elif self.progress < 60:
            self.status.setText("Initializing UI...")
        elif self.progress < 90:
            self.status.setText("Setting up environment...")
        else:
            self.status.setText("Ready! 🚀")

        # Stop at 100% and fade out
        if self.progress >= 100:
            self.timer.stop()
            QTimer.singleShot(500, self.fade_out)

    def close(self):
        super().close()