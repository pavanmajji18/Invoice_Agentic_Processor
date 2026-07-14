"""
OCR utilities using EasyOCR
"""
import easyocr
from typing import Optional
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")


class OCRReader:
    """EasyOCR wrapper for invoice text extraction"""
    
    def __init__(self, languages: list = ["en"], gpu: bool = False):
        """Initialize OCR reader"""
        self.reader = None
        self.languages = languages
        self.gpu = gpu
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of OCR reader"""
        if not self._initialized:
            self.reader = easyocr.Reader(self.languages, gpu=self.gpu)
            self._initialized = True
    
    def read_text(self, image_path: str) -> str:
        """Extract text from an image file"""
        self._ensure_initialized()
        
        try:
            results = self.reader.readtext(image_path, detail=0)
            text = "\n".join(results)
            return text
        except Exception as e:
            raise Exception(f"OCR failed: {str(e)}")
    
    def read_text_detailed(self, image_path: str) -> list:
        """Extract text with bounding boxes and confidence scores"""
        self._ensure_initialized()
        
        try:
            results = self.reader.readtext(image_path, detail=1)
            return results
        except Exception as e:
            raise Exception(f"OCR failed: {str(e)}")
