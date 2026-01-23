import os
from PyQt6.QtGui import QFontDatabase, QFont
from core.utils import resource_path


FONT_DIR = resource_path(os.path.join("assets", "fonts"))


class AppFonts:
    _loaded = False
    family = {}

    @classmethod
    def load(cls):
        if cls._loaded:
            return

        if not os.path.exists(FONT_DIR):
            print(f"⚠️ Font directory not found: {FONT_DIR}")
            cls._loaded = True
            return

        for file in os.listdir(FONT_DIR):
            if file.endswith((".ttf", ".otf")):
                path = os.path.join(FONT_DIR, file)
                font_id = QFontDatabase.addApplicationFont(path)

                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families:
                        cls.family[file] = families[0]

        # Debug: List loaded fonts
        # print("✅ Loaded fonts:", cls.family)
        cls._loaded = True

    # ===== SAFE FONT GETTERS =====
    @classmethod
    def regular(cls, size=12):
        # Priority: Rage-Italic → any loaded → fallback system
        if "Rage-Italic.ttf" in cls.family:
            return QFont(cls.family["Rage-Italic.ttf"], size)

        if cls.family:
            return QFont(next(iter(cls.family.values())), size)

        return QFont("Arial", size)

    @classmethod
    def bold(cls, size=12):
        font = cls.regular(size)
        font.setBold(True)
        return font
