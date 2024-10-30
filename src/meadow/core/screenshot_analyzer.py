"""Module for analyzing screenshots using Claude API"""

import base64
import io
import re
import json
import os
import queue
import threading
import numpy as np
from PIL import Image
import easyocr
from anthropic import Anthropic, AnthropicError
import Vision
import Quartz
import platform

# Initialize OCR reader once as a module-level singleton
_ocr_reader = None
_ocr_queue = queue.Queue()
_ocr_lock = threading.Lock()

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
    
    # Create Vision request
    request = Vision.VNRecognizeTextRequest.alloc().init()
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
    
    # Perform request
    handler.performRequests_error_([request], None)
    
    # Extract text from observations
    text = []
    results = request.results() or []  # Handle case where results() is None
    print(f"[DEBUG] Vision results count: {len(results)}")
    for observation in results:
        text.append(observation.text())
    
    if not text:
        print("[DEBUG] No text found in Vision results")
        raise ValueError("No text extracted from Vision framework")
    return ' '.join(text)

def get_ocr_reader():
    """Get or initialize the OCR reader singleton"""
    # pylint: disable=global-statement
    global _ocr_reader
    with _ocr_lock:
        if _ocr_reader is None:
            _ocr_reader = easyocr.Reader(['en'])
    return _ocr_reader

def analyze_and_log_screenshot(screenshot, image_path, timestamp, window_info, log_path):
    """Analyze screenshot using OCR and Claude API, then log the results"""
    # Get the singleton OCR reader
    reader = get_ocr_reader()

    # Try Vision framework first, fall back to EasyOCR
    try:
        if platform.mac_ver()[0] >= '11.0':  # Vision text recognition requires macOS 11+
            print(f"[DEBUG] Starting Vision OCR at {timestamp}")
            ocr_text = get_vision_text(screenshot)
            print(f"[DEBUG] Completed Vision OCR at {timestamp}")
        else:
            raise ImportError("Vision framework not available")
    except Exception as e:
        print(f"[DEBUG] Vision OCR failed, falling back to EasyOCR: {e}")
        # Extract text from image using queue
        img_array = np.array(screenshot)
        print(f"[DEBUG] Waiting for OCR queue at {timestamp}")
        _ocr_queue.put(True)  # Add request to queue
        try:
            print(f"[DEBUG] Starting OCR at {timestamp}")
            ocr_text = reader.readtext(img_array, detail=0)
            ocr_text = ' '.join(ocr_text)
            print(f"[DEBUG] Completed OCR at {timestamp}")
        finally:
            _ocr_queue.get()  # Remove request from queue
    try:
        # Resize to max dimension of 1024 while preserving aspect ratio
        max_size = 1024
        ratio = max_size / max(screenshot.size)
        if ratio < 1:
            new_size = tuple(int(dim * ratio) for dim in screenshot.size)
            screenshot = screenshot.resize(new_size, Image.Resampling.LANCZOS)

        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

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
        print(f"[DEBUG] Sending to Claude at {timestamp}")
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
        print(f"[DEBUG] Received Claude response at {timestamp}")
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
            return None

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
