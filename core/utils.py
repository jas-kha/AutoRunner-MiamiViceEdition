import re
import os
import sys

# ==============================================
# ANSI Escape Code Stripping Utility
# ==============================================
_ANSI_ESCAPE = re.compile(
    r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])'
)

def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from text"""
    return _ANSI_ESCAPE.sub('', text)

def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)