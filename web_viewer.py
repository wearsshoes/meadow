"""
HTML viewer for the screen monitor log
"""

import io
import os
import json
import base64
from PIL import Image
from flask import Flask, render_template_string

app = Flask(__name__)

# Cache for thumbnails
thumbnail_cache = {}

def get_thumbnail_base64(image_path):
    """Create base64 thumbnail from image path"""
    if image_path in thumbnail_cache:
        return thumbnail_cache[image_path]

    try:
        with Image.open(image_path) as img:
            # Create thumbnail
            img.thumbnail((400, 300))
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            b64_str = base64.b64encode(buffer.getvalue()).decode()
            thumbnail_cache[image_path] = b64_str
            return b64_str
    except (FileNotFoundError, IOError, OSError) as e:
        print(f"Error creating thumbnail for {image_path}: {e}")
        return ""

@app.route('/')
def view_log():
    """
    Reads configuration and log files, processes log entries,
    and renders an HTML template with the log data.
    """
    app_dir = os.path.expanduser('~/Library/Application Support/Selfveillance')
    config_path = os.path.join(app_dir, 'config', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    log_path = os.path.join(app_dir, 'data', 'logs', 'analysis_log.json')
    with open(log_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    # Add thumbnails to entries
    for entry in entries:
        entry['thumbnail'] = get_thumbnail_base64(entry['filepath'])

    # Sort by timestamp, most recent first
    entries.sort(key=lambda x: x['timestamp'], reverse=True)

    # Read the template file
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'viewer.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    return render_template_string(template_content, entries=entries)

def start_viewer():
    """Start the Flask server"""
    app.run(port=5050)

if __name__ == '__main__':
    app.run(port=5050)