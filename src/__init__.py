"""OCR自动化工具包"""

__version__ = "1.0.0"
__author__ = "Jian"

from .ocr_engine import OCREgnine
from .window_manager import Windows
from .image_processor import ImageProcessor

__all__ = ["OCREngine", "Windows", "ImageProcessor"]
