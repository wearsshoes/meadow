# Selfveillance Screen Monitor

A macOS menubar app that periodically captures and analyzes your screen activity using Claude API, helping you track and understand your computer usage patterns.

## Project Mission
- Provide self-surveillance tools for personal productivity tracking
- Generate human-readable descriptions of screen activity
- Maintain privacy by keeping all data local
- Enable easy review of past computer usage

## Architecture
- Separate concerns into distinct modules:
  - main.py - Entry point and app initialization
  - screenshot.py - Screenshot capture and management
  - analyzer.py - Claude integration and analysis
  - web_viewer.py - Flask-based log viewer
  - config.py - Configuration management
- Keep modules focused and independent
- Avoid circular dependencies

## Core Design Principles
- Web viewer organization
  - Separate HTML, CSS, and JS into distinct sections/files
  - Keep template logic separate from Python code
  - Avoid embedding large chunks of frontend code in string literals
  - Use static files for frontend assets when possible
- Event-driven monitoring over fixed intervals
  - Capture on window/app changes rather than time-based
  - Use polling to detect context switches
  - Reset monitoring intervals when context changes
- Clean UI
  - Keep menubar icon simple
  - Put detailed status in menu
  - Avoid cluttering system UI

## Core Dependencies
- rumps 0.4.0 - macOS menubar app framework
  - Menu items must be initialized in __init__ before setup_menu is called
  - Dynamic menu items (like timers) should be class attributes
  - Example:
    ```python
    def __init__(self):
        self.timer_item = rumps.MenuItem("Timer: --")
        super().__init__("Title", menu=[self.timer_item])
    ```
- rumps 0.4.0 - macOS menubar app framework
- pillow 11.0.0 - Image processing
- anthropic 0.37.1 - Claude API client
- pyobjc-framework-Quartz - Native macOS window management

## Architecture Decisions
- Use native macOS APIs (via pyobjc) over cross-platform alternatives
  - More reliable window/app information
  - Better integration with OS

## Window Management
- Use Quartz/CoreGraphics APIs for window info:
  - More accurate window information 
  - Proper separation of app name and window title
  - Native macOS integration
  - Access to window layer and other macOS-specific properties
- Window.title() returns combined app name and window title
- No built-in way to get app name separately
- Format: "[App Name] [Window Title]" (e.g. "Chrome Stack Overflow - Google Chrome")

## Features
- Menubar interface with screenshot controls
- Context-aware screenshot capture
  - Captures on window/app changes
  - Configurable time-based intervals
  - Interval resets on context changes
- Automatic screenshot capture and Claude analysis
  - Analysis performed on both manual and context-based captures
  - Each screenshot analyzed immediately after capture
  - Analysis includes previous action context
- Analysis logs stored as JSON
- Screenshots saved with timestamps


## Configuration
- Config stored in ~/.screen_monitor_config.json
- Screenshots saved to ~/screen_monitor_screenshots
- Analysis logs saved as analysis_log.json in screenshots directory

## Data Structure
### Window Information
- Window titles stored separately as:
  - app_name: Application name (e.g. "Google Chrome")
  - window_title: Active window title (e.g. "Stack Overflow - Question")
- Separation enables:
  - Better analysis by application
  - Cleaner display in web viewer
  - More accurate activity tracking

## Claude Integration
- Analyzes screenshots with active window context for better understanding
- Prompts for active-verb descriptions (e.g. "Reading", "Coding")
```python
# Image analysis request format
messages=[{
    "role": "user",
    "content": [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": base64_string
            }
        },
        {
            "type": "text",
            "text": "Describe what the user is doing starting with an active verb, taking into account the full image context. Active window: [window_name]"
        }
    ]
}]
```

### Historical Context
- Include previous action in Claude's prompt, not in logs
- Helps Claude provide more contextually aware descriptions
- Previous action should be read from last analysis result when making new request

## System Requirements
- macOS only (rumps dependency)
- Screen recording permissions
- Anthropic API key in environment

## TODOs
- Improve web viewer performance and updates
  - Current limitations:
    - Loads all screenshots into memory at once
    - No auto-refresh mechanism
    - Base64 encoding entire images is inefficient
  - Consider:
    - Pagination or infinite scroll
    - WebSocket for real-time updates
    - Serve images directly instead of base64
    - Cache thumbnails
- Consider alternative scheduling approaches for more precise timing
  - Current schedule library may introduce slight delays
  - Options: asyncio, custom timing with drift correction

## Known Issues
- Additional permissions may be required for menubar/screen access
- Rumps menu items must be initialized in specific order:
  1. Declare as None in __init__
  2. Create MenuItem instance in setup_menu
  3. Add to menu list
  - Common error: NoneType if not properly initialized
  - Reason: Rumps menu item lifecycle tied to app initialization
- pygetwindow provides limited window information on macOS
  - Does not properly separate app name from window title
  - Consider using Quartz/CoreGraphics APIs instead:
    ```python
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID
    )
    ```
  - Provides richer window metadata including proper app bundle IDs

## Best Practices
- Keep screenshot filepath consistent between capture and logging
- Handle API timeouts and errors gracefully
- Show loading states during async operations
- Take first screenshot immediately when monitoring starts

## Installation
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set ANTHROPIC_API_KEY environment variable
4. Grant screen recording permissions to Terminal/IDE
5. Run `python main.py`

## Development Setup
1. Create Python virtual environment
2. Install dev dependencies: `pip install -r requirements.txt`
3. Follow installation steps above
4. Main components:
   - main.py: Entry point
   - screen_monitor_app.py: Core app logic
   - web_viewer.py: Screenshot analysis viewer

## Contributing Guidelines
- Use consistent code style with existing codebase
- Add docstrings for new functions/classes
- Test changes on macOS before submitting
- Include screenshot examples for UI changes
- Update documentation for new features

## License
MIT License - See LICENSE file
- Capture all metadata (window title, app name) at time of screenshot
  - Prevents race conditions where window changes before analysis
  - Ensures accurate data association
- Format datetime objects before JSON serialization (datetime objects are not JSON serializable)
- Use existing variables instead of parsing data from filenames/strings when possible
- Use data at its source - avoid reconstructing data that was already available (e.g. use capture timestamp directly rather than parsing from filename)
