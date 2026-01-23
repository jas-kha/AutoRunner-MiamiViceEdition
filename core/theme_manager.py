from PyQt6.QtWidgets import QApplication
from ui.themes import THEMES

class ThemeManager:
    DEFAULT_THEME = "Miami Vice"

    @staticmethod
    def apply_theme(theme_name: str):
        style = THEMES.get(theme_name, THEMES[ThemeManager.DEFAULT_THEME])
        QApplication.instance().setStyleSheet(style)
