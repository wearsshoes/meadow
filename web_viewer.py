from flask import Flask, render_template_string
import os
import json
import base64
from PIL import Image
import io

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
    except Exception as e:
        print(f"Error creating thumbnail for {image_path}: {e}")
        return ""

@app.route('/')
def view_log():
    config_path = os.path.expanduser('~/.screen_monitor_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    log_path = os.path.join(config['screenshot_dir'], 'analysis_log.json')
    with open(log_path, 'r') as f:
        entries = json.load(f)

    # Add thumbnails to entries
    for entry in entries:
        entry['thumbnail'] = get_thumbnail_base64(entry['filepath'])

    # Sort by timestamp, most recent first
    entries.sort(key=lambda x: x['timestamp'], reverse=True)

    # Read the template file
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'viewer.html')
    with open(template_path, 'r') as f:
        template_content = f.read()
    return render_template_string(template_content, entries=entries)

def start_viewer():
    """Start the Flask server"""
    app.run(port=5050)

if __name__ == '__main__':
    app.run(port=5050)