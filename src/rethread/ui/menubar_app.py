
"""Menubar app for screen monitoring using rumps and Quartz"""

import os
import threading
import subprocess
import json
import webbrowser
import rumps
from core.monitor import monitoring_loop, take_screenshot
from core.analyzer import analyze_image

# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-locals
class MenubarApp(rumps.App):
    """
    A macOS menu bar application that periodically
    captures screenshots and analyzes the user's activity.
    """

    def __init__(self):
        self.timer_menu_item = None  # Initialize before super().__init__
        self.config = None  # Initialize config attribute
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
            "Open Screenshots Folder",
            "Open Notes Folder",
            "Open Web Viewer",
            "Settings",
            None,
        ]

    def save_config(self):
        """Save current configuration to file"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f)

    def check_config_changes(self, _):
        """Check for config changes and reload if needed"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                new_config = json.load(f)
                if new_config != self.config:
                    self.config = new_config
                    if self.is_monitoring:
                        self.stop_monitoring(None)
                        self.start_monitoring(None)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

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

    def monitoring_loop(self):
        """Main monitoring loop"""
        monitoring_loop(self.config, self.timer_menu_item, self.is_monitoring, self.data_dir)

    @rumps.clicked("Analyze Current Screen")
    def take_screenshot_and_analyze(self, _):
        """Take and analyze a screenshot of the current screen."""
        self.title = "📸 Analyzing..."
        screenshot, filename, timestamp, window_info = take_screenshot(self.config['screenshot_dir'])
        log_path = os.path.join(self.data_dir, 'logs', 'analysis_log.json')

        def analyze_and_restore():
            analyze_image(screenshot, filename, timestamp, window_info, log_path)
            self.title = "📸"

        threading.Thread(target=analyze_and_restore).start()

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

    def show_settings(self):
        """Open settings in web viewer"""
        webbrowser.open('http://localhost:5050/settings')

    @rumps.clicked("Settings")
    def set_interval(self, _):
        """Display settings window for interval configuration."""
        # Run settings window in separate thread to avoid blocking menubar
        threading.Thread(target=self.show_settings).start()

    @rumps.clicked("Open Screenshots Folder")
    def open_screenshots(self, _):
        """Open the screenshots directory in Finder."""
        subprocess.run(['open', self.config['screenshot_dir']], check=True)

    @rumps.clicked("Open Notes Folder")
    def open_notes(self, _):
        """Open the notes directory in Finder."""
        subprocess.run(['open', self.config['notes_dir']], check=True)

    @rumps.clicked("Open Web Viewer")
    def open_web_viewer(self, _):
        """Open the web viewer in default browser."""
        webbrowser.open('http://localhost:5050')