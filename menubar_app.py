# pylint: disable=no-name-in-module
"""Menubar app for screen monitoring using rumps and Quartz"""

import io
import os
import threading
import subprocess
import time
import json
import base64
from datetime import datetime
import webbrowser
from PIL import ImageGrab, Image
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID,
    kCGWindowIsOnscreen,
    kCGWindowLayer,
    kCGWindowOwnerName,
    kCGWindowName
)
from anthropic import Anthropic, AnthropicError
import rumps

# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-locals
class MenubarApp(rumps.App):
    """
    A macOS menu bar application that periodically
    captures screenshots and analyzes the user's activity.
    """

    def __init__(self):
        self.timer_menu_item = None  # Initialize before super().__init__
        super().__init__("📸")
        self.setup_config()
        self.setup_menu()
        self.is_monitoring = False
        self.next_screenshot = None
        self.last_window_info = None

    def setup_config(self):
        """Initialize configuration settings"""
        # Set up application directories
        self.app_dir = os.path.expanduser('~/Library/Application Support/ReThread')
        self.config_dir = os.path.join(self.app_dir, 'config')
        self.data_dir = os.path.join(self.app_dir, 'data')
        self.cache_dir = os.path.join(self.app_dir, 'cache')

        # Create directory structure
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, 'screenshots'), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, 'logs'), exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, 'thumbnails'), exist_ok=True)

        self.config_path = os.path.join(self.config_dir, 'config.json')
        default_config = {
            'screenshot_dir': os.path.join(self.data_dir, 'screenshots'),
            'notes_dir': os.path.join(os.path.expanduser('~/Documents'), 'ReThread Notes'),
            'interval': 60
        }

        # Load configuration from file
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                # Ensure all default keys exist
                for key, value in default_config.items():
                    if key not in self.config:
                        self.config[key] = value
                self.save_config()
        except FileNotFoundError:
            self.config = default_config
            self.save_config()

        os.makedirs(self.config['screenshot_dir'], exist_ok=True)
        os.makedirs(self.config['notes_dir'], exist_ok=True)

        # Ensure the analysis log file exists
        self.log_path = os.path.join(self.data_dir, 'logs', 'analysis_log.json')
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def setup_menu(self):
        """Setup menu items"""
        self.timer_menu_item = rumps.MenuItem("Next capture: --")
        self.menu = [
            "Start Monitoring",
            "Stop Monitoring",
            None,
            self.timer_menu_item,
            None,
            "Analyze Current Screen",
            None,
            "Set Interval",
            "Open Screenshots Folder",
            "Set Screenshots Folder",
            "Set Notes Folder",
            "Open Web Viewer",
        ]

    def get_active_window_info(self):
        """Get active window info using Quartz"""
        window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
        for window in window_list:
            if window.get(kCGWindowIsOnscreen) and window.get(kCGWindowLayer, 0) == 0:
                return {
                    'app': window.get(kCGWindowOwnerName, 'Unknown App'),
                    'title': window.get(kCGWindowName, 'No Title')
                }
        return {'app': 'Unknown App', 'title': 'No Title'}

    def save_config(self):
        """Save current configuration to file"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f)

    def take_screenshot(self):
        """Capture and save a screenshot, returns (screenshot, filename, timestamp, window_info)"""
        screenshot = ImageGrab.grab()
        timestamp = datetime.now()
        window_info = self.get_active_window_info()
        filename = os.path.join(self.config['screenshot_dir'], f"screenshot_{timestamp.strftime('%Y%m%d_%H%M%S')}.png")
        screenshot.save(filename)
        return screenshot, filename, timestamp, window_info

    def analyze_image(self, screenshot, filename, timestamp, window_info):
        """Analyze screenshot using Claude API"""
        try:
            max_size = (1344, 896)
            screenshot.thumbnail(max_size, Image.Resampling.LANCZOS)

            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            client = Anthropic()

            # Get previous action for context
            try:
                log_path = os.path.join(self.config['screenshot_dir'], 'analysis_log.json')
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
                            "text": f"In one sentence, describe the main action the user is taking starting with an active verb (e.g. 'Reading'). Active window: {window_info['title']}. Previous action: {prev_description}"
                        }
                    ]
                }]
            )

            description = message.content[0].text if message.content else "No description available"
            self.log_analysis(filename, description, timestamp, window_info)

        except (AnthropicError, IOError, ValueError) as e:
            print(f"Error in analyze_image: {str(e)}")

    def log_analysis(self, filename, description, timestamp, window_info):
        """Log analysis results to JSON file"""
        log_path = os.path.join(self.data_dir, 'logs', 'analysis_log.json')

        entry = {
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'filepath': filename,
            'app': window_info['app'],
            'window': window_info['title'],
            'description': description,
        }

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []

        logs.append(entry)

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2)

    def analyze_and_restore(self, screenshot, filename, timestamp, window_info):
        """Analyze screenshot and restore app icon"""
        self.analyze_image(screenshot, filename, timestamp, window_info)
        self.title = "📸"

    def monitoring_loop(self):
        """Main monitoring loop"""
        self.next_screenshot = time.time() + self.config['interval']
        self.last_window_info = self.get_active_window_info()

        while self.is_monitoring:
            current_window = self.get_active_window_info()
            remaining = max(0, round(self.next_screenshot - time.time()))
            self.timer_menu_item.title = f"Next capture: {remaining}s"

            # Take screenshot on window change or interval
            if (current_window != self.last_window_info) or (time.time() >= self.next_screenshot):
                screenshot, filename, timestamp, window_info = self.take_screenshot()
                threading.Thread(target=self.analyze_image, args=(screenshot, filename, timestamp, window_info)).start()
                self.next_screenshot = time.time() + self.config['interval']
                self.last_window_info = current_window

            time.sleep(1)

    @rumps.clicked("Analyze Current Screen")
    def take_screenshot_and_analyze(self, _):
        """Take and analyze a screenshot of the current screen."""
        self.title = "📸 Analyzing..."
        screenshot, filename, timestamp, window_info = self.take_screenshot()
        threading.Thread(target=self.analyze_and_restore, args=(screenshot, filename, timestamp, window_info)).start()

    @rumps.clicked("Start Monitoring")
    def start_monitoring(self, _):
        """Start periodic screenshot monitoring."""
        if not self.is_monitoring:
            self.is_monitoring = True
            threading.Thread(target=self.monitoring_loop).start()

    @rumps.clicked("Stop Monitoring")
    def stop_monitoring(self, _):
        """Stop periodic screenshot monitoring."""
        self.is_monitoring = False
        self.title = "📸"
        self.timer_menu_item.title = "Next capture: --"

    @rumps.clicked("Set Interval")
    def set_interval(self, _):
        """Display dialog to set screenshot interval in seconds."""
        cmd = f'''osascript -e 'Tell application "System Events" to display dialog "Enter interval in seconds:" \
                default answer "{self.config["interval"]}" with title "Set Screenshot Interval"' '''
        result = os.popen(cmd).read()

        if "button returned:OK" in result:
            try:
                new_interval = int(result.split("text returned:")[1].strip())
                if new_interval > 0:
                    self.config['interval'] = new_interval
                    self.save_config()
                    was_monitoring = self.is_monitoring
                    if was_monitoring:
                        self.stop_monitoring(None)
                        self.start_monitoring(None)
            except ValueError:
                pass

    @rumps.clicked("Open Screenshots Folder")
    def open_screenshots(self, _):
        """Open the screenshots directory in Finder."""
        subprocess.run(['open', self.config['screenshot_dir']], check=True)

    @rumps.clicked("Set Screenshots Folder")
    def set_screenshots_folder(self, _):
        """Display Finder dialog to set screenshots directory."""
        cmd = '''osascript -e 'choose folder with prompt "Select Screenshots Folder"' '''
        result = os.popen(cmd).read().strip()

        if result:
            # Remove 'alias ' prefix and ':' suffix that Apple script adds
            new_path = result.replace('alias ', '').rstrip(':')
            self.config['screenshot_dir'] = new_path
            os.makedirs(new_path, exist_ok=True)
            self.save_config()

    @rumps.clicked("Set Notes Folder")
    def set_notes_folder(self, _):
        """Display Finder dialog to set notes directory."""
        cmd = '''osascript -e 'choose folder with prompt "Select Notes Folder"' '''
        result = os.popen(cmd).read().strip()

        if result:
            # Remove 'alias ' prefix and ':' suffix that Apple script adds
            new_path = result.replace('alias ', '').rstrip(':')
            self.config['notes_dir'] = new_path
            os.makedirs(new_path, exist_ok=True)
            self.save_config()

    @rumps.clicked("Open Web Viewer")
    def open_web_viewer(self, _):
        """Open the web viewer in default browser."""
        webbrowser.open('http://localhost:5050')
