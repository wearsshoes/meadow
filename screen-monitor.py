import io
import rumps
import os
import threading
import time
import json
import base64
from datetime import datetime
import webbrowser
from web_viewer import start_viewer
from PIL import ImageGrab, Image
import pygetwindow as gw
from anthropic import Anthropic

class ScreenMonitorApp(rumps.App):
    def __init__(self):
        super().__init__("📸")
        self.setup_config()
        self.setup_menu()
        self.is_monitoring = False
        self.next_screenshot = None

    def setup_config(self):
        """Initialize configuration settings"""
        self.config_path = os.path.expanduser('~/.screen_monitor_config.json')
        default_config = {
            'screenshot_dir': os.path.expanduser('~/screen_monitor_screenshots'),
            'interval': 60
        }

        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = default_config
            self.save_config()

        os.makedirs(self.config['screenshot_dir'], exist_ok=True)

    def setup_menu(self):
        """Setup menu items"""
        self.menu = [
            "Start Monitoring",
            "Stop Monitoring",
            None,
            "Analyze Current Screen",
            None,
            "Set Interval",
            "Open Screenshots Folder",
            "Open Web Viewer",
        ]

    def save_config(self):
        """Save current configuration to file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f)

    def take_screenshot(self):
        """Capture and save a screenshot, returns (screenshot, filename, timestamp)"""
        screenshot = ImageGrab.grab()
        timestamp = datetime.now()
        filename = os.path.join(self.config['screenshot_dir'], f"screenshot_{timestamp.strftime('%Y%m%d_%H%M%S')}.png")
        screenshot.save(filename)
        return screenshot, filename, timestamp

    def analyze_image(self, screenshot, filename, timestamp):
        """Analyze screenshot using Claude API"""
        try:
            MAX_SIZE = (1344, 896)
            screenshot.thumbnail(MAX_SIZE, Image.LANCZOS)

            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            client = Anthropic()
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
                            "text": f"In one sentence, describe the main action the user is taking starting with an active verb (e.g. 'Reading'). Active window: {gw.getActiveWindow().title() if gw.getActiveWindow() else 'Unknown Window'}"
                        }
                    ]
                }]
            )

            description = message.content[0].text if message.content else "No description available"
            self.log_analysis(filename, description, timestamp)

        except Exception as e:
            print(f"Error in analyze_image: {str(e)}")

    def log_analysis(self, filename, description, timestamp):
        """Log analysis results to JSON file"""
        log_path = os.path.join(self.config['screenshot_dir'], 'analysis_log.json')
        entry = {
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'filepath': filename,
            'window': gw.getActiveWindow().title() if gw.getActiveWindow() else "Unknown Window",
            'description': description
        }

        try:
            with open(log_path, 'r') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []

        logs.append(entry)

        with open(log_path, 'w') as f:
            json.dump(logs, f, indent=2)

    def analyze_and_restore(self, screenshot, filename, timestamp):
        """Analyze screenshot and restore app icon"""
        self.analyze_image(screenshot, filename, timestamp)
        self.title = "📸"

    def monitoring_loop(self):
        """Main monitoring loop"""
        screenshot, _, _ = self.take_screenshot()
        self.next_screenshot = time.time() + self.config['interval']

        while self.is_monitoring:
            remaining = max(0, round(self.next_screenshot - time.time()))
            self.title = f"📸 {remaining}s"

            if time.time() >= self.next_screenshot:
                screenshot, filename, timestamp = self.take_screenshot()
                threading.Thread(target=self.analyze_image, args=(screenshot, filename, timestamp)).start()
                self.next_screenshot += self.config['interval']

            time.sleep(0.1)

    @rumps.clicked("Analyze Current Screen")
    def take_screenshot_and_analyze(self, _):
        self.title = "📸 Analyzing..."
        screenshot, filename, timestamp = self.take_screenshot()
        threading.Thread(target=self.analyze_and_restore, args=(screenshot, filename, timestamp)).start()

    @rumps.clicked("Start Monitoring")
    def start_monitoring(self, _):
        if not self.is_monitoring:
            self.is_monitoring = True
            threading.Thread(target=self.monitoring_loop).start()

    @rumps.clicked("Stop Monitoring")
    def stop_monitoring(self, _):
        self.is_monitoring = False
        self.title = "📸"

    @rumps.clicked("Set Interval")
    def set_interval(self, _):
        cmd = f'''osascript -e 'Tell application "System Events" to display dialog "Enter interval in seconds:" \
                default answer "{self.config["interval"]}" with title "Set Screenshot Interval"' '''
        result = os.popen(cmd).read()

        if "button returned:OK" in result:
            try:
                new_interval = int(result.split("text returned:")[1].strip())
                if new_interval > 0:
                    self.config['interval'] = new_interval
                    self.save_config()
                    if self.is_monitoring:
                        self.stop_monitoring(None)
                        self.start_monitoring(None)
            except ValueError:
                pass

    @rumps.clicked("Open Screenshots Folder")
    def open_screenshots(self, _):
        os.system(f"open {self.config['screenshot_dir']}")

    @rumps.clicked("Open Web Viewer")
    def open_web_viewer(self, _):
        webbrowser.open('http://localhost:5050')

if __name__ == "__main__":
    # Start web viewer in a separate thread
    import threading
    viewer_thread = threading.Thread(target=start_viewer, daemon=True)
    viewer_thread.start()
    
    ScreenMonitorApp().run()