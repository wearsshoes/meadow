# pylint: disable=no-name-in-module
# pylint: disable=import-error
"""Module for screen monitoring and screenshot capture"""

import os
import threading
import time
from datetime import datetime
from PIL import ImageGrab
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID,
    kCGWindowIsOnscreen,
    kCGWindowLayer,
    kCGWindowOwnerName,
    kCGWindowName
)

from core.analyzer import analyze_and_log_screenshot

def get_active_window_info():
    """Get active window info using Quartz"""
    # Check screen recording permissions
    try:
        window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
        if window_list is None:
            raise PermissionError("Screen recording permission is required. Please enable it in System Preferences > Security & Privacy > Privacy > Screen Recording")
    except Exception as e:
        raise PermissionError("Unable to access screen content. Please check screen recording permissions.") from e
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    for window in window_list:
        # Skip system UI elements
        app = window.get(kCGWindowOwnerName, '')
        if app in ['Window Server', 'SystemUIServer']:
            continue

        if window.get(kCGWindowIsOnscreen) and window.get(kCGWindowLayer, 0) == 0:
            title = window.get(kCGWindowName, 'No Title')
            return {'app': app, 'title': title}
    return {'app': 'Unknown App', 'title': 'No Title'}

def take_screenshot(screenshot_dir):
    """Capture and save a screenshot, returns (screenshot, filename, timestamp, window_info)"""
    # Get the primary monitor's region for screenshot
    screenshot = ImageGrab.grab(all_screens=False)  # Only grab primary screen
    timestamp = datetime.now()
    window_info = get_active_window_info()
    filename = os.path.join(screenshot_dir, f"screenshot_{timestamp.strftime('%Y%m%d_%H%M%S')}.png")
    screenshot.save(filename)
    return screenshot, filename, timestamp, window_info

def monitoring_loop(config, timer_menu_item, is_monitoring_ref, data_dir, set_title):
    """Main monitoring loop"""
    next_screenshot = time.time() + config['interval']
    last_window_info = get_active_window_info()

    while is_monitoring_ref():
        current_window = get_active_window_info()
        remaining = max(0, round(next_screenshot - time.time()))
        set_title(f"👁️ {remaining}s" if is_monitoring_ref() else "📸")
        # Take screenshot on window change or interval
        if (current_window != last_window_info) or (time.time() >= next_screenshot):
            # Skip if current window is Meadow
            if 'Meadow' in current_window['title']:
                time.sleep(1)
                continue
            screenshot, filename, timestamp, window_info = take_screenshot(config['screenshot_dir'])
            log_path = os.path.join(data_dir, 'logs', 'analysis_log.json')
            threading.Thread(target=analyze_and_log_screenshot, args=(screenshot, filename, timestamp, window_info, log_path)).start()
            next_screenshot = time.time() + config['interval']
            last_window_info = current_window

        time.sleep(1)

    timer_menu_item.title = "Next capture: --"
