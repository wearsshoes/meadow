"""Module for analyzing screenshots using Claude API"""

import base64
import io
import re
import json
from PIL import Image
from anthropic import Anthropic, AnthropicError

def analyze_image(screenshot, filename, timestamp, window_info, log_path):
    """Analyze screenshot using Claude API and log the results"""
    try:
        max_size = (1344, 896)
        screenshot.thumbnail(max_size, Image.Resampling.LANCZOS)

        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        client = Anthropic()

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
                        <relevance>true or false, whether content relates to {window_info.get('research_topic', 'civic government')}</relevance>
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
            is_relevant = (extract_tag('relevance', response) or 'false').lower() == 'true'
            summary = extract_tag('summary', response) if is_relevant else None
        except (AttributeError, ValueError):
            action = "Error parsing response"
            summary = None
        log_analysis(filename, action, timestamp, window_info, log_path, summary)

    except (AnthropicError, IOError, ValueError) as e:
        print(f"Error in analyze_image: {str(e)}")

def log_analysis(filename, description, timestamp, window_info, log_path, summary=None):
    """Log analysis results to JSON file"""
    entry = {
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'filepath': filename,
        'app': window_info['app'],
        'window': window_info['title'],
        'description': description,
        'research_summary': summary,
    }

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append(entry)

    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)
