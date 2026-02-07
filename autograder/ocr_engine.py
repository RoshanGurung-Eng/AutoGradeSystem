# import easyocr
# import re
# def preprocess_image(image_path):
#     # (your gentle preprocessing)
#     #return enhanced_path
#     pass

# def run_ocr(image_path, use_preprocessing=False):
#     if use_preprocessing:
#         image_path = preprocess_image(image_path)
#     reader = easyocr.Reader(['en'], gpu=False, verbose=False)
#     return reader.readtext(image_path, detail=0, paragraph=True)



# def tokenize_lines(raw_results):
#     """Split raw OCR lines into tokens using robust splitting."""
#     all_tokens = []
#     corrected_lines = []
#     for line in raw_results:
#         tokens = re.split(r'[_\s~@#$%^&*+=]+', line)
#         cleaned_tokens = []
#         for token in tokens:
#             if len(token) == 0:
#                 continue
#             if not any(c.isalpha() for c in token):
#                 continue
#             if len(token) == 1 and token.lower() not in ['a', 'i']:
#                 continue
#             all_tokens.append(token)
#             cleaned_tokens.append(token)
#         if cleaned_tokens:
#             corrected_lines.append(" ".join(cleaned_tokens))
#     return all_tokens, corrected_lines
# autograder/ocr_engine.py - UPDATE THIS FILE

import easyocr
import cv2
import numpy as np

def preprocess_image(image_path):
    """Preprocess image for better OCR"""
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Increase contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
    
    # Binarization (thresholding)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Save processed image
    processed_path = image_path.replace('.jpg', '_processed.jpg').replace('.png', '_processed.png')
    cv2.imwrite(processed_path, binary)
    
    return processed_path

def run_ocr(image_path, use_preprocessing=True):
    """Run OCR with optional preprocessing"""
    if use_preprocessing:
        image_path = preprocess_image(image_path)
    
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    results = reader.readtext(image_path, detail=0, paragraph=True)
    
    return results