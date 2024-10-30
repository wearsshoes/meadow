import easyocr

def test_ocr():
    """Test EasyOCR functionality with a simple image"""
    print("Initializing EasyOCR...")
    reader = easyocr.Reader(['en'])
    print("EasyOCR initialized successfully")

    # Create a simple test image with text
    from PIL import Image, ImageDraw
    import numpy as np

    img = Image.new('RGB', (200, 50), color='white')
    d = ImageDraw.Draw(img)
    d.text((10,10), "Hello World", fill='black')

    # Convert to numpy array as required by EasyOCR
    img_array = np.array(img)

    print("\nTesting text extraction...")
    result = reader.readtext(img_array, detail=0)
    print("Extracted text:", result)

if __name__ == "__main__":
    test_ocr()
