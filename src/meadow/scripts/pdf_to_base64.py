"""Script to convert PDF pages to base64-encoded images"""

import os
import base64
import io
from pdf2image import convert_from_path
from PIL import Image

def pdf_to_base64_images(pdf_path, max_size=(1024, 1024)):
    """
    Convert each page of a PDF to a base64-encoded image, resizing if needed.
    Returns a list of base64 strings, one per page.
    """
    # Convert PDF pages to images
    images = convert_from_path(pdf_path)
    
    base64_images = []
    for img in images:
        # Resize if needed while maintaining aspect ratio
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        base64_images.append(img_str)
    
    return base64_images

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python pdf_to_base64.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
        
    images = pdf_to_base64_images(pdf_path)
    for i, img_str in enumerate(images):
        print(f"\n=== Page {i+1} ===")
        print(img_str)
