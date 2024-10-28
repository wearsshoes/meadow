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
- Architecture
  - Prefer simple solutions over complex ones
  - Use multiprocessing for clean process separation
  - Avoid complex coordination mechanisms (signals, events, etc)
- Clean UI
  - Keep menubar icon simple
  - Put detailed status in menu
  - Use native OS interfaces when available (e.g. file pickers over custom dialogs)
  - Follow platform UI conventions
  - Use native OS interfaces when available (e.g. file pickers over custom dialogs)
  - Follow platform UI conventions

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
- Process Separation
  - Run Flask server in separate process
  - Use process.terminate() for clean shutdown
  - Avoid signal handlers for inter-process communication
  - Keep UI responsive by offloading heavy tasks

- Module Organization
  - menubar_app.py: UI and coordination only
    - No direct file or API operations 
    - No business logic
    - Only coordinates between modules
  - monitor.py: Screen capture and monitoring
    - Window tracking
    - Screenshot management
    - Monitoring loop and timing
    - All window/screen related operations
  - analyzer.py: Analysis and logging
    - Claude API integration
    - Image analysis
    - Log management and persistence
    - All analysis related operations
  - web_viewer.py: Research visualization
    - Flask server
    - Log display
    - Settings interface
  - Python Package Structure
    - Use __init__.py files to mark directories as Python packages
    - Required for relative imports between modules
    - Enables `from rethread.core import monitor` style imports
    - Keep __init__.py files minimal unless exposing specific APIs

- Module Principles
  - Group related functionality in same module
  - Keep clear boundaries between modules
  - Avoid circular dependencies
  - Minimize cross-module knowledge

- Design Patterns
  - Single Responsibility: Each module handles one aspect
  - Clean Interfaces: Pass data, not dependencies
  - Minimal Redundancy: No duplicate code between modules
  - Process over Threads: Use multiprocessing for isolation

- Module Organization
  - menubar_app.py: UI and coordination only
    - No direct file or API operations 
    - No business logic
    - Only coordinates between modules
  - monitor.py: Screen capture and monitoring
    - Window tracking
    - Screenshot management
    - Monitoring loop and timing
    - All window/screen related operations
  - analyzer.py: Analysis and logging
    - Claude API integration
    - Image analysis
    - Log management and persistence
    - All analysis related operations
  - web_viewer.py: Research visualization
    - Flask server
    - Log display
    - Settings interface

- Module Principles
  - Group related functionality in same module
  - Keep clear boundaries between modules
  - Avoid circular dependencies
  - Minimize cross-module knowledge

- Design Patterns
  - Single Responsibility: Each module handles one aspect
  - Clean Interfaces: Pass data, not dependencies
  - Minimal Redundancy: No duplicate code between modules
  - Process over Threads: Use multiprocessing for isolation

## Data Structure

Application data is stored in platform-specific user data directories:
- macOS: ~/Library/Application Support/ReThread/
- Keep frontend assets in static files
- macOS: ~/Library/Application Support/ReThread/
  - config/
    - config.json - User preferences
      - screenshot_dir: Screenshot storage location
      - notes_dir: Research notes location (default: ~/Documents/ReThread Notes)
      - interval: Screenshot interval in seconds
  - data/
    - screenshots/ - Screenshot images
    - logs/ - Analysis logs
  - cache/
    - thumbnails/ - Web viewer thumbnail cache

User content is stored in configurable locations:
- Research notes default to ~/Documents/ReThread Notes
- All paths configurable through config.json

Files:
- Screenshots saved with timestamps
- Window information stored as app_name and window_title
- Analysis logs stored as JSON

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
- Config file handling
  - Validate loaded config has all required keys
  - Use default_config as template for required keys
  - Create missing directories from config paths
  - Save config after any changes