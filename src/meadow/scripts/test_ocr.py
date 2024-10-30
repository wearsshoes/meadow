import easyocr
import os
import time
import Vision
import Quartz
from PIL import Image, ImageDraw
import numpy as np

def get_vision_text(image):
    """Extract text using macOS Vision framework"""
    # Convert PIL image to CGImage
    # Convert to RGB if not already
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Get raw bytes with known format
    img_data = image.tobytes()
    img_size = image.size
    bytes_per_row = img_size[0] * 3  # 3 bytes per pixel for RGB
    
    img_provider = Quartz.CGDataProviderCreateWithData(None, img_data, len(img_data), None)
    cg_image = Quartz.CGImageCreate(
        img_size[0], img_size[1],
        8, 24, bytes_per_row,  # 8 bits per component, 24 bits per pixel
        Quartz.CGColorSpaceCreateDeviceRGB(),
        Quartz.kCGBitmapByteOrderDefault,  # No alpha channel needed
        img_provider, None, False, Quartz.kCGRenderingIntentDefault
    )
    
    request = Vision.VNRecognizeTextRequest.alloc().init()
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
    success, error = handler.performRequests_error_([request], None)
    if not success:
        raise Exception(f"Vision framework error: {error}")
    
    text = []
    results = request.results() or []  # Handle case where results() is None
    for observation in results:
        text.append(observation.text())
    return ' '.join(text)

def test_ocr():
    """Compare EasyOCR and Vision framework performance"""
    # Create test images with different complexities
    # Test with generated images
    test_cases = [
        ("Simple text", Image.new('RGB', (200, 50), color='white')),
        ("Multi-line text", Image.new('RGB', (200, 100), color='white')),
    ]
    
    # Add real screenshot test if available
    screenshot_path = "/Users/rachelshu/screen_monitor_logs/screenshots/screenshot_20241029_195652.png"
    if os.path.exists(screenshot_path):
        test_cases.append(("Real screenshot", Image.open(screenshot_path)))
    
    # Add text to test images
    for name, img in test_cases:
        d = ImageDraw.Draw(img)
        if name == "Simple text":
            d.text((10,10), "Hello World", fill='black')
        else:
            d.text((10,10), "Hello\nWorld\nTest", fill='black')
    
    print("\nInitializing EasyOCR...")
    start_time = time.time()
    reader = easyocr.Reader(['en'])
    print(f"EasyOCR initialization: {time.time() - start_time:.2f}s")
    
    # Test both methods
    for name, img in test_cases:
        print(f"\n=== Test Case: {name} ===")
        
        # Test Vision framework
        print("\nVision framework:")
        start_time = time.time()
        vision_result = get_vision_text(img)
        vision_time = time.time() - start_time
        print(f"Time: {vision_time:.2f}s")
        print(f"Result: {vision_result}")
        
        # Test EasyOCR
        print(f"\nEasyOCR:")
        img_array = np.array(img)
        start_time = time.time()
        easyocr_result = reader.readtext(img_array, detail=0)
        easyocr_time = time.time() - start_time
        print(f"Time: {easyocr_time:.2f}s")
        print(f"Result: {' '.join(easyocr_result)}")

if __name__ == "__main__":
    test_ocr()
