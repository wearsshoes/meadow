"""Menubar app for screen monitoring using rumps and Quartz"""

import os
import threading
import subprocess
import json
import webbrowser
import asyncio
from datetime import datetime
import rumps
from meadow.core.screenshot_analyzer import analyze_and_log_screenshot
from meadow.core.monitor import monitoring_loop, take_screenshot
from meadow.core.markdown_bridge import process_analysis_result, process_saved_logs
from meadow.core.config import Config
from meadow.core.manicode_wrapper import execute_manicode
from meadow.core.topic_similarity import initialize_model

# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-locals
class MenubarApp(rumps.App):
    """
    A macOS menu bar application that periodically
    captures screenshots and analyzes the user's activity.
    """

    def __init__(self):
        print("[DEBUG] Initializing MenubarApp...")
        try:
            self.timer_menu_item = None  # Initialize before super().__init__
            self.config = None  # Initialize config attribute
            super().__init__("📸")  # Default icon when not monitoring
            print("[DEBUG] MenubarApp initialized successfully")
        except Exception as e:
            print(f"[ERROR] Failed to initialize MenubarApp: {e}")
            raise
        self.setup_config()
        self.setup_menu()
        self.is_monitoring = False
        self.next_screenshot = None
        self.last_window_info = None
        # Check config changes every 1 second
        rumps.Timer(self.check_config_changes, 1).start()

    def create_notes_structure(self, notes_dir):
        """Create the standard notes directory structure"""
        os.makedirs(notes_dir, exist_ok=True)
        os.makedirs(os.path.join(notes_dir, '_machine'), exist_ok=True)
        os.makedirs(os.path.join(notes_dir, 'research'), exist_ok=True)

    def setup_config(self):
        """Initialize configuration settings"""
        print("[DEBUG] Setting up configuration...")
        config = Config()
        self.config = config.get_all()  # Get copy of full config
        self.app_dir = config.app_dir
        self.data_dir = os.path.join(self.app_dir, 'data')
        self.cache_dir = os.path.join(self.app_dir, 'cache')
        self.log_dir = os.path.join(self.data_dir, 'logs')

    def get_current_log_path(self):
        """Get the path to the current day's log file"""
        today = datetime.now().strftime('%Y%m%d')
        log_path = os.path.join(self.log_dir, f'log_{today}.json')

        # Initialize log file if it doesn't exist
        if not os.path.exists(log_path):
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

        return log_path

    def setup_menu(self):
        """Setup menu items"""
        self.menu = [
            "Start Monitoring",
            "Stop Monitoring",
            None,
            "Analyze Current Window",
            None,
            "Open Web Viewer",
            "Open Screenshots Folder",
            "Open Notes Folder",
            "Process Missing Logs",
            "Generate Source Notes",
            "Settings",
            None,
        ]

    def save_config(self):
        """Save current configuration to file"""
        Config().update(self.config)

    def check_config_changes(self, _):
        """Check for config changes and reload if needed"""
        try:
            config = Config()
            new_config = config.get_all()
            if new_config != self.config:
                old_config = self.config
                self.config = new_config
                if self.is_monitoring:
                    # Only restart monitoring if interval changed
                    if old_config.get('interval') != new_config.get('interval'):
                        self.stop_monitoring(None)
                        self.start_monitoring(None)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def monitoring_loop(self):
        """Main monitoring loop"""
        # Pass function to get fresh config
        monitoring_loop(lambda: Config().get_all(), self.timer_menu_item, lambda: self.is_monitoring, self.data_dir,
                       lambda title: setattr(self, 'title', title))

    def process_screenshot_analysis(self, analysis_result):
        """Process screenshot analysis result immediately"""
        if analysis_result and analysis_result.get('research_summary'):
            asyncio.run(process_analysis_result(analysis_result, self.config['notes_dir']))

    async def generate_source_notes_with_manicode(self):
        """Generate source notes from temp notes in the notes dir"""
        instructions = """
        1. Read the new markdown files in _machine/_staging/ and subfolders
        2. Update or create topic-specific notes in _machine/ based on the content
        3. Link related concepts using [[wiki-style]] links
        4. Update the knowledge files in _machine/ to reflect new information
        5. Clean up and organize notes in _machine/ as needed
        """

        # Execute manicode with the workspace
        await execute_manicode(instructions, {
            "cwd": self.config['notes_dir'],
            "notes_dir": self.config['notes_dir']
        }, allow_notes=True)

    @rumps.clicked("Analyze Current Window")
    def take_screenshot_and_analyze(self, _):
        """Take and analyze a screenshot of the current window."""
        # Initialize model before analysis
        self.title = "📸 Analyzing..."
        screenshot, image_path, timestamp, window_info = take_screenshot(self.data_dir)
        log_path = self.get_current_log_path()

        def analyze_and_restore():
            # Initialize model asynchronously
            asyncio.run(initialize_model())
            analysis_result = analyze_and_log_screenshot(screenshot, image_path, timestamp, window_info, log_path)
            if analysis_result:
                self.process_screenshot_analysis(analysis_result)
            self.title = "📸"

        threading.Thread(target=analyze_and_restore).start()

    @rumps.clicked("Generate Source Notes")
    def handle_generate_source_notes(self, _):
        """Generate source notes from the temp notes."""
        self.title = "📝 Generating..."

        async def generate():
            try:
                await self.generate_source_notes_with_manicode()
                subprocess.run(['open', self.config['notes_dir']], check=True)
            finally:
                self.title = "📸"

        threading.Thread(target=lambda: asyncio.run(generate())).start()

    @rumps.clicked("Start Monitoring")
    def start_monitoring(self, _):
        """Start periodic screenshot monitoring."""
        if not self.is_monitoring:
            # Get fresh config before starting
            self.config = Config().get_all()
            self.is_monitoring = True
            self.title = "👁️"  # Active monitoring icon
            threading.Thread(target=self.monitoring_loop).start()

    @rumps.clicked("Stop Monitoring")
    def stop_monitoring(self, _):
        """Stop periodic screenshot monitoring."""

        self.is_monitoring = False
        self.title = "📸"  # Default icon when not monitoring

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
        subprocess.run(['open', os.path.join(self.data_dir, 'screenshots')], check=True)

    @rumps.clicked("Open Notes Folder")
    def open_notes(self, _):
        """Open the notes directory in Finder."""
        subprocess.run(['open', self.config['notes_dir']], check=True)

    @rumps.clicked("Open Web Viewer")
    def open_web_viewer(self, _):
        """Open the web viewer in default browser."""
        webbrowser.open('http://localhost:5050')

    @rumps.clicked("Process Missing Logs")
    def handle_process_missing_logs(self, _):
        """Process any saved unprocessed logs."""
        async def process():
            await process_saved_logs(self.config['notes_dir'])
            subprocess.run(['open', self.config['notes_dir']], check=True)

        threading.Thread(target=lambda: asyncio.run(process())).start()
