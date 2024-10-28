"""
HTML viewer for the screen monitor log
"""

import io
import os
import json
import base64
from PIL import Image
from flask import Flask, redirect, render_template_string, request, url_for, jsonify

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

@app.route('/pick_folder')
def pick_folder():
    """Handle macOS folder picker dialog"""
    cmd = '''osascript -e 'choose folder with prompt "Select Folder"' '''
    result = os.popen(cmd).read().strip()
    if result:
        # Convert from AppleScript path format to Unix path
        path = result.replace('alias Macintosh HD:', '/').replace(':', '/')
        return jsonify({'path': path})
    return jsonify({'path': None})

@app.route('/')
def view_log():
    """
    Reads configuration and log files, processes log entries,
    and renders an HTML template with the log data.
    """
    app_dir = os.path.expanduser('~/Library/Application Support/ReThread')

    log_path = os.path.join(app_dir, 'data', 'logs', 'analysis_log.json')
    with open(log_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    # Add thumbnails to entries
    for entry in entries:
        entry['thumbnail'] = get_thumbnail_base64(entry['filepath'])

    # Sort by timestamp and limit to most recent 20 entries
    entries.sort(key=lambda x: x['timestamp'], reverse=True)
    entries = entries[:20]  # Only show most recent 20 entries initially

    # Read the template file
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'viewer.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    return render_template_string(template_content, entries=entries)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Handle settings page and form submission"""
    app_dir = os.path.expanduser('~/Library/Application Support/ReThread')
    config_path = os.path.join(app_dir, 'config', 'config.json')

    if request.method == 'POST':
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            if 'interval' in request.form:
                new_interval = int(request.form['interval'])
                if new_interval > 0:
                    config['interval'] = new_interval

            if 'screenshot_dir' in request.form:
                new_dir = request.form['screenshot_dir']
                if new_dir:
                    config['screenshot_dir'] = new_dir
                    os.makedirs(new_dir, exist_ok=True)

            if 'notes_dir' in request.form:
                new_dir = request.form['notes_dir']
                if new_dir:
                    config['notes_dir'] = new_dir
                    os.makedirs(new_dir, exist_ok=True)

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f)
            return redirect(url_for('settings'))
        except (ValueError, KeyError):
            pass

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'settings.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    return render_template_string(template_content, interval=config['interval'], config=config)

def shutdown_viewer():
    """Shutdown the Flask server and cleanup resources"""
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

def start_viewer():
    """Start the Flask server"""
    app.run(port=5050, debug=False, use_reloader=False)

if __name__ == '__main__':
    app.run(port=5050)
