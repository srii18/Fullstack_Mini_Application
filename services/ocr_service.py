import pytesseract
import cv2
import numpy as np
from PIL import Image
import PyPDF2
import pdfplumber
from typing import Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRService:
    """Service for extracting text from various file formats"""
    
    def __init__(self):
        # Configure Tesseract path (adjust based on installation)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    def extract_text_from_image(self, image_path: str) -> Tuple[str, float]:
        """
        Extract text from image files (.jpg, .png) using OCR
        Returns: (extracted_text, confidence_score)
        """
        try:
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Preprocess image for better OCR accuracy
            processed_image = self._preprocess_image(image)
            
            # Convert to PIL Image for Tesseract
            pil_image = Image.fromarray(processed_image)
            
            # Extract text with confidence scores
            data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
            text = pytesseract.image_to_string(pil_image)
            
            # Calculate average confidence score
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            confidence_score = avg_confidence / 100.0  # Convert to 0-1 range
            
            logger.info(f"OCR completed for {image_path}, confidence: {confidence_score:.2f}")
            return text.strip(), confidence_score
            
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {str(e)}")
            return "", 0.0
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image to improve OCR accuracy
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to clean up the image
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, float]:
        """
        Extract text from PDF files
        Returns: (extracted_text, confidence_score)
        """
        try:
            text = ""
            
            # Try pdfplumber first (better for structured PDFs)
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                
                if text.strip():
                    logger.info(f"PDF text extracted using pdfplumber: {pdf_path}")
                    return text.strip(), 1.0  # High confidence for direct text extraction
                    
            except Exception as e:
                logger.warning(f"pdfplumber failed for {pdf_path}: {str(e)}")
            
            # Fallback to PyPDF2
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                
                if text.strip():
                    logger.info(f"PDF text extracted using PyPDF2: {pdf_path}")
                    return text.strip(), 0.9  # Slightly lower confidence
                    
            except Exception as e:
                logger.warning(f"PyPDF2 failed for {pdf_path}: {str(e)}")
            
            # If no text extracted, return empty
            logger.warning(f"No text could be extracted from PDF: {pdf_path}")
            return "", 0.0
            
        except Exception as e:
            logger.error(f"PDF processing failed for {pdf_path}: {str(e)}")
            return "", 0.0
    
    def extract_text_from_txt(self, txt_path: str) -> Tuple[str, float]:
        """
        Extract text from plain text files
        Returns: (extracted_text, confidence_score)
        """
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            logger.info(f"Text file processed: {txt_path}")
            return text.strip(), 1.0  # Perfect confidence for plain text
            
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(txt_path, 'r', encoding=encoding) as file:
                        text = file.read()
                    logger.info(f"Text file processed with {encoding} encoding: {txt_path}")
                    return text.strip(), 1.0
                except UnicodeDecodeError:
                    continue
            
            logger.error(f"Could not decode text file: {txt_path}")
            return "", 0.0
            
        except Exception as e:
            logger.error(f"Text file processing failed for {txt_path}: {str(e)}")
            return "", 0.0
    
    def extract_text(self, file_path: str, file_type: str) -> Tuple[str, float]:
        """
        Main method to extract text based on file type
        Returns: (extracted_text, confidence_score)
        """
        file_type = file_type.lower()
        
        if file_type in ['jpg', 'jpeg', 'png']:
            return self.extract_text_from_image(file_path)
        elif file_type == 'pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_type == 'txt':
            return self.extract_text_from_txt(file_path)
        else:
            logger.error(f"Unsupported file type: {file_type}")
            return "", 0.0
