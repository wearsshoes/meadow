"""Module for analyzing screenshots using Claude API"""

import base64
import re
import json
import os
import queue
import threading

import Vision
import easyocr
from anthropic import Anthropic, AnthropicError

class OCRProcessor:
    """Handles OCR processing with fallback options"""
    def __init__(self):
        self._ocr_reader = None
        self._ocr_queue = queue.Queue()
        self._ocr_lock = threading.Lock()

    def _get_easyocr_reader(self):
        """Get or initialize the OCR reader singleton"""
        with self._ocr_lock:
            if self._ocr_reader is None:
                self._ocr_reader = easyocr.Reader(['en'])
        return self._ocr_reader

    def get_text_from_image(self, cg_image, image_path):
        """Extract text from image, trying Vision first then EasyOCR

        Args:
            cg_image: CGImage object for Vision OCR
            image_path: Path to saved PNG for EasyOCR fallback
        """
        try:
            raise Exception("Test")
            print("[DEBUG] Using Vision OCR")
            return self._get_vision_text(cg_image)
        except Exception as e:
            print(f"[DEBUG] Vision OCR failed, falling back to EasyOCR: {e}")
            print("[DEBUG] Using EasyOCR")
            return self._get_easyocr_text(image_path)

    def _get_vision_text(self, cg_image):
        """Extract text using macOS Vision framework"""
        # pylint: disable=no-member
        request = Vision.VNRecognizeTextRequest.alloc().init()
        handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
        handler.performRequests_error_([request], None)

        text = []
        results = request.results() or []
        print(f"[DEBUG] Vision results count: {len(results)}")
        for observation in results:
            text.append(observation.text())

        if not text:
            print("[DEBUG] No text found in Vision results")
            raise ValueError("No text extracted from Vision framework")
        return ' '.join(text)

    def _get_easyocr_text(self, image_path):
        """Extract text using EasyOCR as fallback"""
        reader = self._get_easyocr_reader()
        self._ocr_queue.put(True)
        try:
            result = reader.readtext(image_path)
            text_results = [text for _, text, _ in result]
            return ' '.join(text_results)
        finally:
            self._ocr_queue.get()

# Create singleton OCR processor
ocr_processor = OCRProcessor()

def analyze_and_log_screenshot(screenshot, image_path, timestamp, window_info, log_path):
    """Analyze screenshot using OCR and Claude API, then log the results"""
    try:
        ocr_text = ocr_processor.get_text_from_image(screenshot, image_path)

        # Read the saved PNG for Claude API
        with open(image_path, 'rb') as f:
            img_str = base64.b64encode(f.read()).decode()

        # Use config API key if available, otherwise fall back to environment variable
        api_key = None
        config_path = os.path.join(os.path.expanduser('~/Library/Application Support/Meadow'), 'config', 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get('anthropic_api_key')
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        client = Anthropic(api_key=api_key) if api_key else Anthropic()

        # Get previous action for context
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
                prev_app = logs[-1]['app'] if logs else "N/A"
                prev_window = logs[-1]['window'] if logs else "N/A"
                prev_description = logs[-1]['description'] if logs else "N/A"
        except (FileNotFoundError, json.JSONDecodeError, IndexError):
            prev_app = "N/A"
            prev_window = "N/A"
            prev_description = "N/A"

        # Get research topics from config
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                research_topics = config.get('research_topics', ['civic government'])
        except (FileNotFoundError, json.JSONDecodeError):
            research_topics = ['civic government']

        prompt = f"""
Name of active window: {window_info['app']} - {window_info['title']}
Previous action: {prev_description} in "{prev_app} - {prev_window}"
Active research topics: {', '.join(research_topics)}
Analyze the screenshot and return your response in XML format with the following tags:
<action>Brief description of main user action, starting with an active verb</action>
<topic>Which research topic this relates to, or "none" if not relevant.</topic>
<summary>If relevant, one paragraph summary of the relevant content. If not relevant, leave empty.</summary>
<continuation>true/false: The current action is essentially the same as the previous action.</continuation>
"""

        # Include previous action in prompt
        print("[DEBUG] Sending to Claude")

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_str
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )

        response = message.content[0].text if message.content else "<action>No description available</action><topic>none</topic><summary></summary>"
        print("[DEBUG] Received Claude response")
        try:
            def extract_tag(tag, text):
                """Extract and unescape content from XML tag"""
                match = re.search(f'<{tag}>(.*?)</{tag}>', text, re.DOTALL)
                if not match:
                    return None
                return match.group(1).replace('<', '<').replace('>', '>').replace('&amp;', '&').strip()

            action = extract_tag('action', response) or "Error parsing response"
            topic = extract_tag('topic', response)
            summary = extract_tag('summary', response) if topic != "none" else None
            continuation = bool(extract_tag('continuation', response))
        except (AttributeError, ValueError):
            action = "Error parsing response"
            summary = None

        entry = {
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'image_path': image_path,
            'app': window_info['app'],
            'window': window_info['title'],
            'description': action,
            'research_topic': topic,
            'research_summary': summary,
            'ocr_text': ocr_text,
            'continuation': continuation,
            'processed': False
        }

        # Skip if no research content
        if summary is None:
            print("Took a screenshot, but it was irrelevant to research.")
            try:
                os.remove(image_path)  # Clean up irrelevant screenshot
            except OSError:
                pass  # Ignore cleanup errors
            return None

        # Move relevant screenshot to permanent storage
        screenshot_dir = os.path.dirname(os.path.dirname(image_path))
        perm_path = os.path.join(screenshot_dir, 'screenshots', f"screenshot_{timestamp.strftime('%Y%m%d_%H%M%S')}.png")
        os.makedirs(os.path.dirname(perm_path), exist_ok=True)
        os.rename(image_path, perm_path)
        entry['image_path'] = perm_path  # Update path in log entry

        # Use dated log file
        log_dir = os.path.dirname(log_path)
        dated_log = os.path.join(log_dir, f"log_{timestamp.strftime('%Y%m%d')}.json")

        try:
            with open(dated_log, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []

        logs.append(entry)

        with open(dated_log, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2)

        return entry

    except (AnthropicError, IOError, ValueError) as e:
        print(f"Error in analyze_image: {str(e)}")
        return None
