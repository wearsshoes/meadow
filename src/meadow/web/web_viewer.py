"""
HTML viewer for the screen monitor log and PDF analysis
"""

import io
import os
import random
import json
import string
from datetime import datetime
import base64
import hashlib
import keyring
from PIL import Image
from flask import Flask, render_template_string, request, jsonify, redirect, render_template
from meadow.ui.menubar_app import MenubarApp
from meadow.core.pdf_analyzer import PDFAnalyzer

app = Flask(__name__,
           template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
           static_folder=os.path.join(os.path.dirname(__file__), 'static'))
pdf_analyzer = PDFAnalyzer()

# Cache for thumbnails
thumbnail_cache = {}

def get_thumbnail_base64(image_path):
    """Create base64 thumbnail from image path"""
    if image_path in thumbnail_cache:
        return thumbnail_cache[image_path]

    # Check disk cache
    cache_dir = os.path.expanduser('~/Library/Application Support/Meadow/cache/thumbnails')
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, os.path.basename(image_path))

    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                b64_str = base64.b64encode(f.read()).decode()
                thumbnail_cache[image_path] = b64_str
                return b64_str
        except IOError:
            pass

    try:
        with Image.open(image_path) as img:
            # Create thumbnail
            img.thumbnail((400, 300))
            # Save to cache
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            b64_str = base64.b64encode(buffer.getvalue()).decode()
            thumbnail_cache[image_path] = b64_str
            # Save to disk cache
            img.save(cache_path, 'PNG')
            return b64_str
    except (FileNotFoundError, IOError, OSError) as e:
        print(f"Error creating thumbnail for {image_path}: {e}")
        return ""

def get_pdf_cache_dir():
    """Get and ensure PDF pages cache directory exists"""
    cache_dir = os.path.expanduser('~/Library/Application Support/Meadow/cache/pdf_pages')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

@app.route('/open_in_finder')
def open_in_finder():
    """Open the log file location in Finder"""
    app_dir = os.path.expanduser('~/Library/Application Support/Meadow')
    log_path = os.path.join(app_dir, 'data', 'logs')
    os.system(f'open "{log_path}"')
    return '', 204

@app.route('/')
def index():
    """Redirect to logs view"""
    return redirect('/logs')

@app.route('/pdf')
def pdf_upload():
    """Render the PDF upload interface"""
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'pdf_upload.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    return render_template_string(template_content)

@app.route('/analyze_pdf', methods=['POST'])
def analyze_pdf():
    """Handle PDF analysis"""
    app_dir = os.path.expanduser('~/Library/Application Support/Meadow')
    config_path = os.path.join(app_dir, 'config', 'config.json')

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            notes_dir = config['notes_dir']
            temp_dir = os.path.join(notes_dir, '_machine', '_temp')

        data = request.json
        pdf_data = data.get('pdf_data')
        if not pdf_data:
            return jsonify({'error': 'No PDF data provided'}), 400

        # Generate PDF hash for caching
        pdf_hash = hashlib.sha256(base64.b64decode(pdf_data)).hexdigest()[:12]

        # Get analysis results and page images
        markdown_results, page_images = pdf_analyzer.analyze_pdf(pdf_data)

        # Save page images to cache
        cache_dir = get_pdf_cache_dir()
        for page_num, img_data in enumerate(page_images, 1):
            cache_filename = f"{pdf_hash}_page_{page_num}.png"
            cache_path = os.path.join(cache_dir, cache_filename)
            with open(cache_path, 'wb') as f:
                f.write(img_data)
            print(f"[DEBUG] Saved page {page_num} to cache: {cache_filename}")

        # Create _machine/_temp/notes directory if it doesn't exist
        os.makedirs(temp_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save markdown content to file with image links
        for i, result in enumerate(markdown_results):
            page_num = i + 1
            cache_filename = f"{pdf_hash}_page_{page_num}.png"
            cache_path = os.path.join(cache_dir, cache_filename)

            # Add image link at the end of the analysis
            result_with_image = f"{result}\n\n![Page {page_num}]({cache_path})\n"

            suffix = ''.join(random.choices(string.ascii_letters, k=4))
            filename = f"pdf_analysis_{timestamp}{suffix}.md"
            filepath = os.path.join(temp_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(result_with_image)

            print(f"[DEBUG] Saved analysis to {filepath}")

        # Join results with image links for the response
        markdown_with_images = ''.join(markdown_results)
        return jsonify({'result': {'markdown': markdown_with_images}})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logs')
def view_logs():
    """
    Reads configuration and log files, processes log entries,
    and renders an HTML template with the log data.
    """
    app_dir = os.path.expanduser('~/Library/Application Support/Meadow')
    log_dir = os.path.join(app_dir, 'data', 'logs')

    # Get selected date from query params, default to most recent date
    dates = []
    for filename in os.listdir(log_dir):
        if filename.startswith('log_') and filename.endswith('.json'):
            date = filename[4:12]  # Extract YYYYMMDD from filename
            dates.append(date)
    dates.sort(reverse=True)
    selected_date = request.args.get('date', dates[0] if dates else datetime.now().strftime('%Y%m%d'))

    # Get list of available dates
    dates = []
    for filename in os.listdir(log_dir):
        if filename.startswith('log_') and filename.endswith('.json'):
            date = filename[4:12]  # Extract YYYYMMDD from filename
            dates.append(date)
    dates.sort(reverse=True)

    # Read selected log file
    log_path = os.path.join(log_dir, f'log_{selected_date}.json')
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
            print(f"[DEBUG] Loaded {len(entries)} entries from {log_path}")
    except FileNotFoundError:
        print(f"[DEBUG] Log file not found: {log_path}")
        entries = []
    except json.JSONDecodeError as e:
        print(f"[DEBUG] Error decoding log file {log_path}: {e}")
        entries = []

    # Add thumbnails to entries
    for entry in entries:
        entry['thumbnail'] = get_thumbnail_base64(entry['image_path'])

    # Sort by timestamp and limit to most recent 20 entries
    entries.sort(key=lambda x: x['timestamp'], reverse=True)
    entries = entries[:20]  # Only show most recent 20 entries initially

    return render_template('viewer.html',
                           entries=entries,
                           dates=dates,
                           selected_date=selected_date)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Handle settings page and form submission"""
    app_dir = os.path.expanduser('~/Library/Application Support/Meadow')
    config_path = os.path.join(app_dir, 'config', 'config.json')

    if request.method == 'POST':
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            if 'interval' in request.form:
                new_interval = int(request.form['interval'])
                if new_interval > 0:
                    config['interval'] = new_interval

            if 'research_topics' in request.form:
                topics = [t.strip() for t in request.form['research_topics'].split('\n') if t.strip()]
                config['research_topics'] = topics

            if 'screenshot_dir' in request.form:
                new_dir = request.form['screenshot_dir']
                if new_dir:
                    config['screenshot_dir'] = new_dir
                    os.makedirs(new_dir, exist_ok=True)

            if 'notes_dir' in request.form:
                new_dir = request.form['notes_dir']
                if new_dir:
                    config['notes_dir'] = new_dir
                    # Create full notes structure when directory changes
                    menubarapp = MenubarApp()
                    menubarapp.create_notes_structure(new_dir)

            if 'anthropic_api_key' in request.form:
                api_key = request.form['anthropic_api_key']
                if api_key:
                    keyring.set_password("meadow", "anthropic_api_key", api_key)
                    # Don't store API key in config file
                    config.pop('anthropic_api_key', None)

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f)
            return '', 204
        except (ValueError, KeyError):
            pass

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Get stored API key
    stored_api_key = keyring.get_password("meadow", "anthropic_api_key") or os.environ.get('ANTHROPIC_API_KEY', '')

    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'settings.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    return render_template_string(template_content, interval=config['interval'], config=config, stored_api_key=bool(stored_api_key))

def shutdown_viewer():
    """Shutdown the Flask server and cleanup resources"""
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

def initialize_config():
    """Initialize application configuration"""
    app_dir = os.path.expanduser('~/Library/Application Support/Meadow')
    config_dir = os.path.join(app_dir, 'config')
    os.makedirs(config_dir, exist_ok=True)

    config_path = os.path.join(config_dir, 'config.json')
    default_config = {
        'notes_dir': os.path.join(os.path.expanduser('~/Documents'), 'Meadow Notes'),
        'interval': 60,
        'research_topics': ['civic government']
    }

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Ensure all default keys exist
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
    except (FileNotFoundError, json.JSONDecodeError):
        config = default_config

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f)

    # Create notes directory structure
    notes_dir = config['notes_dir']
    os.makedirs(notes_dir, exist_ok=True)
    os.makedirs(os.path.join(notes_dir, '_machine'), exist_ok=True)
    os.makedirs(os.path.join(notes_dir, 'research'), exist_ok=True)

def start_viewer():
    """Start the Flask server"""
    print("[DEBUG] Starting web viewer...")
    initialize_config()
    app.run(port=5050, debug=False, use_reloader=False)

if __name__ == '__main__':
    app.run(port=5050)
