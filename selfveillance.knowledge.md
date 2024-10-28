# ReThread
A macOS menubar app that acts as an AI research assistant by analyzing your screen activity using Claude API.
- Build a research companion that understands your work context
- Generate research outlines based on your reading and writing patterns
- Enable easy review of research progress and insights
-
## Project Mission
- Assist researchers by tracking and analyzing topic-relevant content
- Filter and analyze content based on configured research topics
- Generate detailed summaries of relevant research material
- Maintain research context across multiple sources and sessions
- Compile coherent research summaries automatically
- Keep all data private and local

## Core Design Principles
- Threading Constraints
- Self-monitoring Prevention
  - Skip automatic screenshots of ReThread's own interface
  - Allow manual screenshots via menubar
  - Check active window before taking screenshot, not during window detection
  - Prevents recursive monitoring of research logs and settings
- Self-monitoring Prevention
  - Skip automatic screenshots of ReThread's own interface
  - Allow manual screenshots via menubar
  - Check active window before taking screenshot, not during window detection
  - Prevents recursive monitoring of research logs and settings
- Self-Monitoring Constraints
  - Exclude ReThread's own UI from automatic monitoring
  - Only capture ReThread windows when explicitly requested via menubar
  - Prevent recursive/redundant analysis of monitoring interface
- AI Response Format
  - Use XML tags for structured responses
  - Parse XML into JSON for storage
  - Required tags:
    ```xml
    <action>Brief description of main user action</action>
    <relevance>true/false for research topic relevance</relevance>
    <summary>Research-relevant content summary</summary>
    ```
  - XML Parsing Safety:
    - Escape special characters in content
    - Use html.escape for user-facing output
    - Handle CDATA sections if needed
    - Validate tag presence before access
    - Sanitize before regex matching
  - Parse tags individually with regex
  - Store all fields directly in log entries
  - No tuple/list wrapping of parsed data
  - Include error handling for malformed responses
  - Empty summary tag indicates non-relevant content
- Architecture
  - Prefer simple solutions over complex ones
  - Use multiprocessing for clean process separation
  - Avoid complex coordination mechanisms (signals, events, etc)  - Clean UI
  - Keep menubar icon simple but informative
    - Use 📸 when idle
    - Use 👁️ when monitoring
    - Show status info in icon title (e.g. countdown) not menu
  - Put detailed status in menu
  - Settings UI Patterns
    - Auto-save changes immediately
    - Show feedback through status messages
    - Avoid explicit save buttons
    - Provide immediate visual feedback for changes
    - Apply consistent save behavior across all input types (text fields, pickers, etc)
  - Native OS Integration
    - Prefer browser-native UI components over OS-native when in web context
    - Browser dialogs maintain tab/window context
    - OS dialogs can lead to state inconsistency if user navigates away
    - Convert paths to Unix format after selection
    - Create chosen directories if they don't exist
    - Folder Picker UX Constraints
      - Disable picker button while dialog is open
      - Center dialog relative to parent window
      - Handle dialog dismissal gracefully
      - Prevent multiple concurrent dialogs
    - Apply consistent save behavior across all input types (text fields, pickers, etc)
    - Apply consistent save behavior across all input types (text fields, pickers, etc)
  - Native OS Integration
    - Prefer browser-native UI components over OS-native when in web context
    - Browser dialogs maintain tab/window context
    - OS dialogs can lead to state inconsistency if user navigates away
    - Convert paths to Unix format after selection
    - Create chosen directories if they don't exist
    - Folder Picker UX Constraints
      - Disable picker button while dialog is open
      - Center dialog relative to parent window
      - Handle dialog dismissal gracefully
      - Prevent multiple concurrent dialogs
  - Status Display Patterns
    - Menu items can't update while menu is open (rumps limitation)
    - Use icon title for real-time updates
    - Keep dropdown menu for static information
  - Use native OS interfaces when available (e.g. file pickers over custom dialogs)
  - Follow platform UI conventions
  - Provide clear visual feedback for system state
  - Maintain consistent navigation
    - Show menubar in both native app and web interface
    - Keep core actions accessible across all views
    - Use same terminology and icons in both interfaces
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

- State Management
  - Monitor state transitions carefully
  - Reset monitoring state when settings change
  - Only start/stop monitoring through explicit user actions
  - Settings changes take effect immediately:
    - Config updates trigger behavior changes without restart
    - Analysis parameters (e.g. research topic) update on next capture
    - UI reflects current settings state
  - Threading Constraints
    - Signal handlers must run in main thread
    - Keep Flask cleanup in main process
    - Use event flags for thread communication
    - Avoid signals for inter-thread coordination
  - Resource Management
    - Clean up resources on shutdown
    - Handle multiprocessing semaphores explicitly
    - Use context managers for resource lifecycle
    - Check for resource leaks during development
  - Monitoring State
    - Use boolean flag for monitoring state
    - Check flag before starting new monitoring
    - Reset timer and window info on stop
    - Clear menu status on stop
    - Ensure monitoring thread exits cleanly

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
      - research_topic: Active research topic (default: 'civic government')
      - topic_threshold: Minimum relevance score for content analysis
  - data/
    - screenshots/ - Screenshot images
    - logs/ - Analysis logs
  - cache/
    - thumbnails/ - Web viewer thumbnail cache
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

## Data Structure
- Screenshots saved with timestamps
- Window information stored as app_name and window_title
- Analysis logs stored as JSON
- Thumbnails cached in memory during web viewer session
  - Max size: 400x300px
  - Format: PNG
  - Base64 encoded for web display
  - Stored in ~/Library/Application Support/ReThread/cache/thumbnails/

## Best Practices
- Keep screenshot filepath consistent
- Handle API timeouts gracefully
- Show loading states during async operations
- Content Analysis
  - Check topic relevance before detailed analysis
  - Provide specific, research-focused summaries
  - Include key quotes and citations when available
  - Note connections to previous research content
- Take first screenshot when monitoring starts
- Format datetime objects before JSON serialization
- Config file handling
  - Validate loaded config has all required keys
  - Use default_config as template for required keys
  - Create missing directories from config paths
  - Save config after any changes
  - Required Settings UI Fields
    - Screenshot directory (with folder picker)
    - Notes directory (with folder picker)
    - Screenshot interval
    - Research topic