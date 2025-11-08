"""OCR自动化工具包"""

__version__ = "1.0.0"
__author__ = "Jian"

from .ocr_engine import OCREngine
from .providers.win_provider import WinProvider

__all__ = ["OCREngine", "WinProvider"]
