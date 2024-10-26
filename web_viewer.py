from flask import Flask, render_template_string
import json
import os
import base64
from PIL import Image
import io

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Screenshot Analysis Viewer</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f5f5f5;
        }
        .thumbnail {
            max-width: 200px;
            max-height: 150px;
        }
    </style>
</head>
<body>
    <h1>Screenshot Analysis Log</h1>
    <table>
        <thead>
            <tr>
                <th>Screenshot</th>
                <th>Time</th>
                <th>App</th>
                <th>Window Title</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>
            {% for entry in entries %}
            <tr>
                <td><img class="thumbnail" src="data:image/png;base64,{{ entry.thumbnail }}" /></td>
                <td>{{ entry.timestamp }}</td>
                <td>{{ entry.app }}</td>
                <td>{{ entry.window }}</td>
                <td>{{ entry.description }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
'''

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

    return render_template_string(HTML_TEMPLATE, entries=entries)

def start_viewer():
    """Start the Flask server"""
    app.run(port=5050)

if __name__ == '__main__':
    app.run(port=5050)