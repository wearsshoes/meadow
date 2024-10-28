# pylint: disable=relative-beyond-top-level
"""Module for analyzing screenshots using Claude API"""

import base64
import io
import re
import json
import os
import numpy as np
from PIL import Image
import easyocr
from anthropic import Anthropic, AnthropicError
from .manicode_wrapper import execute_manicode

def analyze_image(screenshot, filename, timestamp, window_info, log_path):
    """Analyze screenshot using OCR and Claude API, then log the results"""
    # Initialize OCR reader once
    reader = easyocr.Reader(['en'])

    # Extract text from image
    img_array = np.array(screenshot)
    ocr_text = reader.readtext(img_array, detail=0)
    ocr_text = ' '.join(ocr_text)
    print("OCR extracted text:", ocr_text)
    try:
        max_size = (1344, 896)
        screenshot.thumbnail(max_size, Image.Resampling.LANCZOS)

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
                prev_description = logs[-1]['description'] if logs else "N/A"
        except (FileNotFoundError, json.JSONDecodeError, IndexError):
            prev_description = "N/A"

        # Include previous action in prompt
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
                        "text": f"""Analyze this screenshot and return your response in XML format with the following tags:

                        <action>Brief description of main user action, starting with an active verb</action>
                        <topic>Which research topic this relates to, or "none" if not relevant: {', '.join(window_info.get('research_topics', ['civic government']))}</topic>
                        <relevance>true or false, whether content relates to any research topic</relevance>
                        <summary>If relevant, one paragraph summary of the relevant content. If not relevant, leave empty.</summary>

                        Active window: {window_info['title']}
                        Previous action: {prev_description}"""
                    }
                ]
            }]
        )

        response = message.content[0].text if message.content else "<action>No description available</action><relevance>false</relevance><summary></summary>"
        try:
            def extract_tag(tag, text):
                """Extract and unescape content from XML tag"""
                match = re.search(f'<{tag}>(.*?)</{tag}>', text, re.DOTALL)
                if not match:
                    return None
                return match.group(1).replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').strip()

            action = extract_tag('action', response) or "Error parsing response"
            topic = extract_tag('topic', response)
            is_relevant = (extract_tag('relevance', response) or 'false').lower() == 'true'
            summary = extract_tag('summary', response) if is_relevant else None
        except (AttributeError, ValueError):
            action = "Error parsing response"
            summary = None
        log_analysis(filename, action, topic, timestamp, window_info, log_path, summary, ocr_text)

    except (AnthropicError, IOError, ValueError) as e:
        print(f"Error in analyze_image: {str(e)}")

async def generate_research_notes(notes_dir: str, research_topics: list[str]):
    """Generate Obsidian-style research notes from analysis logs"""
    try:
        print("\n[DEBUG] Starting research note generation...")
        print(f"[DEBUG] Using notes directory: {notes_dir} and these research topics: {', '.join(research_topics)}")

        # Get log from Application Support
        log_path = os.path.join(os.path.expanduser('~/Library/Application Support/Meadow'), 'data', 'logs', 'analysis_log.json')

        with open(log_path, 'r', encoding='utf-8') as f:
            logs = json.load(f)

        print(f"[DEBUG] Found {len(logs)} log entries")

        instructions = f"""
        1. Review the most recent usage logs for content related to these research topics: {', '.join(research_topics)}
        2. Capture key concepts and findings from the research by creating new Obsidian-style markdown notes, or adding to existing ones.
        3. Include a human-readable date and time corresponding to the log to maintain context.
        4. Connect related notes with [[wiki-style]] links.
        5. Organize within subfolders by topic.
        6. Finish by updating the knowledge file to capture details about the file organization.
        """

        await execute_manicode(instructions, {
            "cwd": notes_dir
        }, allow_notes=True)

    except (IOError, json.JSONDecodeError) as e:
        print(f"Error generating notes: {e}")

def log_analysis(filename, action, topic, timestamp, window_info, log_path, summary=None, ocr_text=None):
    """Log analysis results to JSON file"""
    entry = {
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'filepath': filename,
        'app': window_info['app'],
        'window': window_info['title'],
        'description': action,
        'research_topic': topic,
        'research_summary': summary,
        'ocr_text': ocr_text,
    }

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append(entry)

    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)
