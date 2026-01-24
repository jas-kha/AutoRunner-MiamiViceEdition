"""
AutoRunner - Miami Vice Edition
Main entry point
"""
import sys
import os
from PyQt6.QtWidgets import QApplication

from app.application import AutoRunnerApp
from ui.splash import SplashScreen
from core.fonts import AppFonts


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    
    # Load custom fonts
    AppFonts.load()
    
    # Show splash screen
    splash = SplashScreen()
    while splash.isVisible():
        app.processEvents()
    
    # Get project path from command line args
    project_path = None
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        project_path = sys.argv[1]
    
    # Create and show main window
    window = AutoRunnerApp(project_path)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()