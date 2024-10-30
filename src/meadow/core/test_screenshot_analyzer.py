"""Unit tests for screenshot analyzer functionality"""

import os
import unittest
from unittest.mock import patch, MagicMock
import Vision
from PIL import Image, ImageDraw
import numpy as np

from meadow.core.screenshot_analyzer import OCRProcessor

class TestOCRProcessor(unittest.TestCase):
    """Test OCR processing with both Vision and EasyOCR"""

    def setUp(self):
        """Set up test images and OCR processor"""
        self.ocr = OCRProcessor()

        # Create test image with known text
        self.test_img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(self.test_img)
        # Draw larger text for better OCR detection
        draw.text((50, 40), "TEST", fill='black')

        # Save test image
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_path = os.path.join(self.test_dir, 'test_ocr.png')
        self.test_img.save(self.test_path)

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_path):
            os.remove(self.test_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    @patch('Vision.VNRecognizeTextRequest')
    @patch('Vision.VNImageRequestHandler')
    def test_vision_ocr(self, mock_handler, mock_request):
        """Test Vision framework OCR processing"""
        # Mock Vision framework response
        mock_observation = MagicMock()
        mock_observation.text.return_value = "Test OCR Text"
        mock_request_instance = MagicMock()
        mock_request_instance.results.return_value = [mock_observation]
        mock_request.alloc.return_value.init.return_value = mock_request_instance

        # Mock handler
        mock_handler_instance = MagicMock()
        mock_handler.alloc.return_value.initWithCGImage_options_.return_value = mock_handler_instance
        mock_handler_instance.performRequests_error_.return_value = (True, None)

        # Create mock CGImage
        mock_cg_image = MagicMock()

        result = self.ocr._get_vision_text(mock_cg_image)
        self.assertEqual(result, "Test OCR Text")

    def test_easyocr_fallback(self):
        """Test EasyOCR fallback when Vision fails"""
        # Force Vision to fail
        with patch.object(self.ocr, '_get_vision_text', side_effect=Exception("Vision failed")):
            result = self.ocr.get_text_from_image(None, self.test_path)
            self.assertTrue(len(result) > 0, "EasyOCR should detect some text")

    def test_ocr_queue(self):
        """Test OCR queue management"""
        # Force Vision to fail to test EasyOCR queue
        with patch.object(self.ocr, '_get_vision_text', side_effect=Exception("Vision failed")):
            # Queue should be empty initially
            self.assertTrue(self.ocr._ocr_queue.empty())

            # Process should add to queue
            result = self.ocr.get_text_from_image(None, self.test_path)

            # Queue should be empty after processing
            self.assertTrue(self.ocr._ocr_queue.empty())
            self.assertTrue(len(result) > 0, "EasyOCR should detect some text")

    def test_concurrent_ocr_requests(self):
        """Test queue handles multiple OCR requests properly"""
        with patch.object(self.ocr, '_get_vision_text', side_effect=Exception("Vision failed")):
            # Start multiple OCR requests
            results = []
            for _ in range(3):
                result = self.ocr.get_text_from_image(None, self.test_path)
                results.append(result)
            
            # All requests should complete and return text
            self.assertEqual(len(results), 3)
            for result in results:
                self.assertTrue(len(result) > 0)

    def test_image_format_handling(self):
        """Test handling of different image formats"""
        # Test with invalid image path
        with self.assertRaises(FileNotFoundError):
            self.ocr._get_easyocr_text("nonexistent.png")

    def test_error_recovery(self):
        """Test error handling and recovery"""
        # Test recovery from Vision error
        with patch.object(self.ocr, '_get_vision_text', side_effect=Exception("Vision failed")):
            result = self.ocr.get_text_from_image(None, self.test_path)
            self.assertTrue(len(result) > 0)

if __name__ == '__main__':
    unittest.main()
