# Selfveillance Screen Monitor
A macOS menubar app that periodically captures and analyzes your screen activity using Claude API.

## Project Mission
- Provide self-surveillance tools for personal productivity tracking
- Generate human-readable descriptions of screen activity
- Maintain privacy by keeping all data local
- Enable easy review of past computer usage

## Core Design Principles
- State Management
  - Monitor state transitions carefully
  - Reset monitoring state when settings change
  - Only start/stop monitoring through explicit user actions
- Event-driven monitoring over fixed intervals
  - Capture on window/app changes rather than time-based
  - Reset monitoring intervals when context changes
- Clean UI
  - Keep menubar icon simple
  - Put detailed status in menu

## Core Dependencies
- rumps 0.4.0 - macOS menubar app framework
- pillow 11.0.0 - Image processing
- anthropic 0.37.1 - Claude API client
- pyobjc-framework-Quartz - Native macOS window management
- asyncio 3.4.3 - Async/await support
- Flask 3.0.3 - Web viewer server
- ptyprocess 0.7.0 - Terminal interaction

Note: When updating dependencies, check for async/await usage in the codebase as these require explicit asyncio support

## Architecture
- Separate concerns into distinct modules
- Keep modules focused and independent
- Use native macOS APIs for window management
- Keep frontend assets in static files

## Data Structure

Application data is stored in platform-specific user data directories:
- macOS: ~/Library/Application Support/Selfveillance/
  - config/
    - config.json - User preferences
  - data/
    - screenshots/ - Screenshot images
    - logs/ - Analysis logs
  - cache/
    - thumbnails/ - Web viewer thumbnail cache

Files:
- Screenshots saved with timestamps
- Window information stored as app_name and window_title 
- Analysis logs stored as JSON

## Claude Integration
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

## System Requirements
- macOS only
- Screen recording permissions
- Anthropic API key in environment

## Best Practices
- Keep screenshot filepath consistent
- Handle API timeouts gracefully
- Show loading states during async operations
- Take first screenshot when monitoring starts
- Format datetime objects before JSON serialization

## TypeScript to Python Translation
- Replace Promise constructor with async/await pattern
- Use Python's asyncio instead of JS Promise chains
- Convert arrow functions to standard Python functions
- Replace process.env with os.environ
- Replace node-pty with ptyprocess
- Handle string interpolation with f-strings
- Use Python type hints instead of TypeScript types

## Code Porting Guidelines
- Maintain exact feature parity when porting between languages
- Port all function parameters and return types
- Preserve error handling behavior
- Keep test functions for verification
- Match original terminal interaction behavior
