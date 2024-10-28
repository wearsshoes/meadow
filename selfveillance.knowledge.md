# ReThread
A macOS menubar app that acts as an AI research assistant by analyzing your screen activity using Claude API.
- Build a research companion that understands your work context
- Generate research outlines based on your reading and writing patterns
- Enable easy review of research progress and insights
-
## Project Mission
- Assist researchers by tracking and organizing their research activities
- Generate structured outlines from screen activity and content
- Maintain research context across multiple sources and sessions
- Compile coherent research summaries automatically
- Keep all data private and local

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

## Data Structure

Application data is stored in platform-specific user data directories:
- macOS: ~/Library/Application Support/ReThread/
- Keep frontend assets in static files
- macOS: ~/Library/Application Support/ReThread/
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
            "text": "In one sentence, describe the main research activity the user is performing, starting with an active verb (e.g. 'Reading'). Consider the full image context and previous actions to maintain research continuity. Active window: [window_name]. Previous action: [prev_description]"
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