import re

# ==============================================
# ANSI Escape Code Stripping Utility
# ==============================================
_ANSI_ESCAPE = re.compile(
    r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])'
)

def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from text"""
    return _ANSI_ESCAPE.sub('', text)
