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
        
        # Multi-language support configuration
        self.supported_languages = {
            'eng': 'English',
            'spa': 'Spanish', 
            'fra': 'French',
            'deu': 'German',
            'ita': 'Italian',
            'por': 'Portuguese',
            'rus': 'Russian',
            'chi_sim': 'Chinese (Simplified)',
            'jpn': 'Japanese',
            'kor': 'Korean'
        }
        
        # Default language combination for better accuracy
        self.default_lang_config = 'eng+spa+fra'  # English, Spanish, French
    
    def detect_language(self, image_path: str) -> str:
        """
        Detect the primary language in an image using OCR
        Returns: language code (e.g., 'eng', 'spa', 'fra')
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return 'eng'  # Default to English
            
            processed_image = self._preprocess_image(image)
            pil_image = Image.fromarray(processed_image)
            
            # Try to detect language using Tesseract's built-in language detection
            try:
                # Get orientation and script detection info
                osd = pytesseract.image_to_osd(pil_image)
                # For now, we'll use a simple heuristic based on character patterns
                # In a production system, you might use langdetect or similar libraries
                
                # Quick text extraction for language detection
                sample_text = pytesseract.image_to_string(pil_image, lang='eng+spa+fra')
                
                # Simple language detection based on common words/patterns
                text_lower = sample_text.lower()
                
                # Spanish indicators
                spanish_words = ['de', 'la', 'el', 'en', 'con', 'por', 'para', 'total', 'fecha', 'tienda']
                spanish_score = sum(1 for word in spanish_words if word in text_lower)
                
                # French indicators  
                french_words = ['de', 'la', 'le', 'en', 'avec', 'pour', 'total', 'date', 'magasin']
                french_score = sum(1 for word in french_words if word in text_lower)
                
                # English indicators
                english_words = ['the', 'and', 'for', 'with', 'total', 'date', 'store', 'receipt']
                english_score = sum(1 for word in english_words if word in text_lower)
                
                # Determine primary language
                scores = {'spa': spanish_score, 'fra': french_score, 'eng': english_score}
                detected_lang = max(scores, key=scores.get)
                
                logger.info(f"Language detection scores: {scores}, detected: {detected_lang}")
                return detected_lang
                
            except Exception:
                # Fallback to English if detection fails
                return 'eng'
                
        except Exception as e:
            logger.warning(f"Language detection failed for {image_path}: {str(e)}")
            return 'eng'
    
    def extract_text_from_image(self, image_path: str) -> Tuple[str, float]:
        """
        Extract text from image files (.jpg, .png) using OCR with multi-language support
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
            
            # Detect primary language
            detected_lang = self.detect_language(image_path)
            
            # Create language configuration based on detection
            if detected_lang == 'spa':
                lang_config = 'spa+eng'  # Spanish + English fallback
            elif detected_lang == 'fra':
                lang_config = 'fra+eng'  # French + English fallback
            else:
                lang_config = self.default_lang_config  # Multi-language default
            
            # Extract text with detected language configuration
            try:
                data = pytesseract.image_to_data(pil_image, lang=lang_config, output_type=pytesseract.Output.DICT)
                text = pytesseract.image_to_string(pil_image, lang=lang_config)
            except Exception as lang_error:
                logger.warning(f"Multi-language OCR failed, falling back to English: {str(lang_error)}")
                # Fallback to English only
                data = pytesseract.image_to_data(pil_image, lang='eng', output_type=pytesseract.Output.DICT)
                text = pytesseract.image_to_string(pil_image, lang='eng')
            
            # Calculate average confidence score
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            confidence_score = avg_confidence / 100.0  # Convert to 0-1 range
            
            logger.info(f"OCR completed for {image_path}, language: {detected_lang}, confidence: {confidence_score:.2f}")
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
