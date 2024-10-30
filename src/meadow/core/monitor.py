# pylint: disable=no-name-in-module
"""Module for screen monitoring and screenshot capture"""

import os
import threading
import time
import asyncio
from datetime import datetime
from PIL import ImageGrab
import subprocess

from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID,
    kCGWindowIsOnscreen,
    kCGWindowLayer,
    kCGWindowOwnerName,
    kCGWindowName,
    CGWindowListCreateImage,
    CGRectNull,
    NSURL,
    kCGWindowListOptionIncludingWindow,
    CGImageDestinationCreateWithURL,
    CGImageDestinationFinalize,
    CGImageDestinationAddImage,
)

from meadow.core.screenshot_analyzer import analyze_and_log_screenshot
from meadow.core.topic_similarity import initialize_model

def get_browser_url(app_name):
    """Get URL from browser using AppleScript"""
    browsers = {
        'Google Chrome': '''
            tell application "Google Chrome"
                get URL of active tab of front window
            end tell
        ''',
        'Safari': '''
            tell application "Safari"
                get URL of current tab of front window
            end tell
        ''',
        'Firefox': '''
            tell application "Firefox"
                get URL of active tab of front window
            end tell
        '''
    }

    if app_name in browsers:
        try:
            result = subprocess.run(['osascript', '-e', browsers[app_name]],
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.SubprocessError:
            return None
    return None

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
            url = None

            # Try to get URL if it's a browser
            # TODO: other browsers exist
            if app in ['Google Chrome', 'Safari', 'Firefox']:
                url = get_browser_url(app)

            return {'app': app, 'title': title, 'url': url}
    return {'app': 'Unknown App', 'title': 'No Title', 'url': None}

def take_screenshot(data_dir):
    """Capture and save a screenshot, returns (screenshot, image_path, timestamp, window_info)"""
    # Get the active window info
    window_info = get_active_window_info()
    screenshot = None
    # Find the window ID for the active window
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    window_id = None
    for window in window_list:
        if (window.get(kCGWindowOwnerName) == window_info['app'] and
            window.get(kCGWindowName) == window_info['title']):
            window_id = window.get('kCGWindowNumber')
            break

    if window_id:
        # Capture just this window using native API
        cg_image = CGWindowListCreateImage(
            CGRectNull,  # Null rect means capture the whole window
            kCGWindowListOptionIncludingWindow,  # Only capture the specified window
            window_id,  # The window to capture
            0  # No image options
        )
        if cg_image:
            screenshot = cg_image
    if screenshot is None:  # Fallback to full screen if window capture fails
        print("[DEBUG] Failed to capture active window. Capturing entire screen.")
        screenshot = ImageGrab.grab(all_screens=False)
    timestamp = datetime.now()
    window_info = get_active_window_info()
    screenshot_dir = os.path.join(data_dir, 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    # Save to temp location first
    temp_dir = os.path.join(data_dir, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"temp_{timestamp.strftime('%Y%m%d_%H%M%S')}.png")
    # Save CGImage directly to PNG
    destination = CGImageDestinationCreateWithURL(
            NSURL.fileURLWithPath_(temp_path),
        "public.png",  # Use the UTI string directly
        1,
        None
    )
    CGImageDestinationAddImage(destination, screenshot, None)
    CGImageDestinationFinalize(destination)
    return screenshot, temp_path, timestamp, window_info

def monitoring_loop(get_config, timer_menu_item, is_monitoring_ref, data_dir, set_title):
    """Main monitoring loop"""
    # Initialize model at start of monitoring
    asyncio.run(initialize_model())

    config = get_config()
    print(f"[DEBUG] Starting monitoring loop with interval: {config['interval']}")
    next_screenshot = time.time() + config['interval']
    last_window_info = get_active_window_info()

    while is_monitoring_ref():
        current_window = get_active_window_info()
        remaining = max(0, round(next_screenshot - time.time()))
        set_title(f"👁️ {remaining}s" if is_monitoring_ref() else "📸")
        # Take screenshot on window change or interval
        if (current_window != last_window_info) or (time.time() >= next_screenshot):
            print(f"[DEBUG] Window change detected or interval reached at {datetime.now().strftime('%H:%M:%S')}")
            # Skip if current window is Meadow
            if 'Meadow' in current_window['title']:
                time.sleep(1)
                continue
            print(f"[DEBUG] Taking screenshot at {datetime.now().strftime('%H:%M:%S')}")
            config = get_config()  # Get fresh config for screenshot
            screenshot, image_path, timestamp, window_info = take_screenshot(config['screenshot_dir'])
            print(f"[DEBUG] Screenshot saved to {image_path}")
            today = datetime.now().strftime('%Y%m%d')
            log_path = os.path.join(data_dir, 'logs', f'log_{today}.json')
            threading.Thread(target=analyze_and_log_screenshot, args=(screenshot, image_path, timestamp, window_info, log_path)).start()
            next_screenshot = time.time() + config['interval']
            last_window_info = current_window

        time.sleep(1)

    if timer_menu_item:
        timer_menu_item.title = "Next capture: --"
