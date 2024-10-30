# Meadow
A macOS menubar app that acts as an AI research assistant by analyzing your screen activity using Claude API.

## Project Mission
- Assist researchers by tracking and analyzing topic-relevant content
- Filter and analyze content based on configured research topics
- Generate detailed summaries of relevant research material
- Contribute new information to the user's existing markdown notes

## Architecture

### Core
- monitor.py
  - runs the monitoring loop and saves logs
- screenshot_analyzer.py
  - analyzes screenshots and extracts text
  - filters content by topic relevance before analysis
- topic_similarity.py
  - uses Apple NLEmbedding for topic matching
  - falls back to sentence-transformers if unavailable
  - filters irrelevant content before API calls
  - filters content by topic relevance before analysis
- topic_similarity.py
  - uses Apple NLEmbedding for topic matching
  - falls back to sentence-transformers if unavailable
  - filters irrelevant content before API calls
- pdf_analyzer.py
  - analyzes PDFs and extracts content
- manicode_wrapper.py
  - used to create notes from analysis

### UI
- menubar_app.py: UI and coordination
  - monitor continuously or analyze current screen
  - open web viewer
  - read-only access to configuration

### Web
- web_viewer.py: settings and configuration management
  - Handles all config file modifications
  - Provides config API for menubar app
  - / (main page)
    - View details from captured logs
    - Show thumbnails and analysis results
    - Collapsible details with OCR text and prompts
  - /settings
    - Configure intervals and directories
    - Set research topics
    - Store API keys securely
  - /open_log_file
    - Open log directory in Finder

## Data Storage
Application data in ~/Library/Application Support/Meadow/:
- config/config.json - User preferences
- data/screenshots/ - Screenshot images
- data/logs/ - Analysis logs (includes prompts and responses for debugging)
- cache/thumbnails/ - Web viewer thumbnail

Notes folder (Location set by user):
```
   notes/                                     # parent folder, may be named differently
      _machine/                               # App-managed source notes
      city_governance/                        # Organized by topic
         san_mateo_budget_pdf/                # Organized by source
            fiscal_summary.md                 # Subtopic
            public_works.md                   # Subtopic
         city_governance.knowledge.md         # Compares sources
      machine_notes.knowledge.md              # Tracks research topics
      research/                               # User knowledge space
      meadow_notes.knowledge.md               # Overall description of research folder
```

## Topic Filtering Architecture
- Pre-filter content using embeddings before Claude API
- Uses sentence-transformers (all-MiniLM-L6-v2) for embeddings
- Configurable similarity threshold
- Reduces API costs by filtering irrelevant content early
- Cleans up irrelevant screenshots automatically

## Topic Filtering Architecture
- Pre-filter content using embeddings before Claude API
- Primary: Apple's NLEmbedding framework
- Fallback: sentence-transformers (all-MiniLM-L6-v2)
- Configurable similarity threshold
- Reduces API costs by filtering irrelevant content early
- Cleans up irrelevant screenshots automatically

## Dependencies
- rumps - macOS menubar app framework
- pillow - Image processing and screenshots
- anthropic - Claude API client
- pyobjc-framework-Quartz - Native macOS window management
- Flask - Web viewer server
- EasyOCR - Text extraction from images
- py2app - macOS app bundling
- keyring - Secure API key storage
- manicode - Note generation (TODO: determine packaging strategy)

### Dependency Management
- Use setup.py as single source of truth for dependencies
- Generate requirements.txt only when needed: `pip install . && pip freeze > requirements.txt`

## Core Design Principles

### Architecture Patterns

- Screenshot lifecycle management:
  - Only save screenshots permanently if relevant to research
  - Clean up irrelevant screenshots at exit
  - Save to temp location until analysis complete
  - Move to permanent storage only after confirming research relevance
  - Testing considerations:
    - Verify window capture with fallback to full screen
    - Confirm temp file cleanup on irrelevant content
    - Check permanent storage path for relevant content
    - Test file permissions and directory creation
    - Validate file naming patterns and uniqueness
  - Testing considerations:
    - Verify window capture with fallback to full screen
    - Confirm temp file cleanup on irrelevant content
    - Check permanent storage path for relevant content
    - Test file permissions and directory creation
    - Validate file naming patterns and uniqueness

- Timestamp handling:
  - Record actual timestamps for API calls
  - Capture separate timestamps for request and response
  - Skip timestamps in OCR logging
  - Focus logging on method selection over timing
- Separate UI concerns from configuration management
  - Web interface handles all config modifications
  - Menubar app has read-only access to config
  - Prevents race conditions between interfaces
  - Makes config changes traceable through web UI

### Code Quality Standards

- Performance Standards:
  - Keep startup time under 1 second
  - Lazy load expensive resources
  - Initialize singletons only when first accessed
  - Defer file operations until needed
  - Profile startup path regularly

- Linting:
  - Run pylint before committing changes
  - Maintain 8.0+ pylint score
  - Use type hints for all function parameters
  - Follow Google Python Style Guide
  - Disable specific pylint warnings with inline comments only when necessary

- Error Handling:
  - Log all exceptions with context
  - Provide user-friendly error messages
  - Use custom exceptions for domain-specific errors
  - Handle all file operations with appropriate try/except
  - Never suppress KeyboardInterrupt or SystemExit

### Configuration Management Patterns

- Config Change Handling:
  - Web viewer owns all config modifications
  - Config changes affect next app start
  - Clear menu item references during cleanup
  - Handle quick start/stop cycles gracefully
  - Example: "Changes will take effect after restarting the app"

- Race condition prevention:
  - Web viewer validates before saving
  - Menubar app reloads on timer
  - Use atomic writes for config updates
  - Watch for external config changes

- Performance patterns:
  - Lazy initialize Config singleton on first access
  - Cache file paths but not content
  - Load config file only when values needed
  - Use atomic file operations for updates
  - Keep config operations off startup path

- Implementation patterns:
  - Never access protected members (e.g. Config._config) directly
  - Use public methods: get(), set(), get_all()
  - Create new public methods for complex operations
  - Avoid storing mutable config references
  - Reload config when needed instead of caching
  - Example: "Changes will take effect after restarting the app"

- Config Change Propagation:
  - Web viewer owns all config modifications
  - Config changes affect next app start
  - Clear menu item references during cleanup
  - Handle quick start/stop cycles gracefully
  - When comparing configs, use get_all() vs get_all()
  - In templates, use config.get_all() instead of passing Config instance
  - Templates expect dictionary interface, not Config object

- Race condition prevention:
  - Web viewer validates before saving
  - Menubar app reloads on timer
  - Use atomic writes for config updates
  - Watch for external config changes

- Performance patterns:
  - Lazy initialize Config singleton on first access
  - Cache file paths but not content
  - Load config file only when values needed
  - Use atomic file operations for updates
  - Keep config operations off startup path

- Implementation patterns:
  - Never access protected members (e.g. Config._config) directly
  - Use public methods: get(), set(), get_all()
  - Create new public methods for complex operations
  - Avoid storing mutable config references
  - Reload config when needed instead of caching
  - When comparing configs, use get_all() vs get_all()
  - In templates, use config.get_all() instead of passing Config instance
  - Templates expect dictionary interface, not Config object

- Race condition prevention:
  - Web viewer validates before saving
  - Menubar app reloads on timer
  - Use atomic writes for config updates
  - Watch for external config changes

- Performance patterns:
  - Lazy initialize Config singleton on first access
  - Cache file paths but not content
  - Load config file only when values needed
  - Use atomic file operations for updates
  - Keep config operations off startup path

- Implementation patterns:
  - Never access protected members (e.g. Config._config) directly
  - Use public methods: get(), set(), get_all()
  - Create new public methods for complex operations
  - Avoid storing mutable config references
  - Reload config when needed instead of caching
  - When comparing configs, use get_all() vs get_all()
  - In templates, use config.get_all() instead of passing Config instance
  - Templates expect dictionary interface, not Config object

- Menubar Lifecycle Management
  - Initialize all menu items in setup_menu() before use
  - Never assume menu items exist after stopping monitoring
  - Clear references to menu items during cleanup
  - Handle quick start/stop cycles gracefully
  - Check menu item existence before access
  - Example error case: timer_menu_item.title access after monitoring stops

### Debug Logging
- Log all state transitions:
  - Start/stop of key operations (monitoring, analysis)
  - Before/after values for config changes
  - Entry/exit of long-running operations
  - Failures and fallback behavior
  - Config changes with old/new values
  - Monitoring lifecycle events (start, stop, interval changes)
  - Settings changes with new values
- Avoid repetitive logging:
  - Log state changes once, not per iteration
  - Use counters for repeated operations
  - Summarize batch operations instead of logging each item
  - Only log meaningful state changes
  - Example: "Processed 5 items" vs "Processing item 1... Processing item 2..."
- Include timing information where relevant
- Use consistent format: "[DEBUG] Operation: detail"
- Log both old and new values for config changes
- Log complete lifecycle of features (start, stop, pause)
- Debug logging patterns:
  - Config changes: "[DEBUG] Config changed - old interval: X, new interval: Y"
  - Settings updates: "[DEBUG] Settings: changing interval to X"
  - Monitoring lifecycle: "[DEBUG] Starting monitoring loop with interval: X"
  - Monitoring state: "[DEBUG] Stopping monitoring"
  - When comparing configs, use get_all() vs get_all()
  - In templates, use config.get_all() instead of passing Config instance
  - Templates expect dictionary interface, not Config object

- Race condition prevention:
  - Web viewer validates before saving
  - Menubar app reloads on timer
  - Use atomic writes for config updates
  - Watch for external config changes

- Performance patterns:
  - Lazy initialize Config singleton on first access
  - Cache file paths but not content
  - Load config file only when values needed
  - Use atomic file operations for updates
  - Keep config operations off startup path

- Implementation patterns:
  - Never access protected members (e.g. Config._config) directly
  - Use public methods: get(), set(), get_all()
  - Create new public methods for complex operations
  - Avoid storing mutable config references
  - Reload config when needed instead of caching

- Performance patterns:
  - Lazy initialize Config singleton on first access
  - Cache file paths but not content
  - Load config file only when values needed
  - Use atomic file operations for updates
  - Keep config operations off startup path

- Implementation patterns:
  - Never access protected members (e.g. Config._config) directly
  - Use public methods: get(), set(), get_all()
  - Create new public methods for complex operations
  - Avoid storing mutable config references
  - Reload config when needed instead of caching
  - When comparing configs, use get_all() vs get_all()
  - In templates, use config.get_all() instead of passing Config instance
  - Templates expect dictionary interface, not Config object

- Singleton implementation:
  - Initialize all attributes in __init__, not __new__
  - Use hasattr check to prevent double initialization
  - Example:
    ```python
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.config_dir = '...'
            self.initialized = True
    ```
  - Never access instance attributes in __new__
  - Keep __new__ minimal, just instance creation
  - Do all setup work in __init__

- Template Integration:
  - Pass config.get_all() to templates, never Config instance
  - Example: render_template('view.html', config=config.get_all())
  - Access in template: {{ config.notes_dir }}
  - Maintain dictionary-like interface for template compatibility

- Config file location:
  - Store in ~/Library/Application Support/Meadow/config/config.json
  - Never cache path, always derive from app_dir
  - Use get_config_path() helper to ensure consistency

- Config access patterns:
  - Web viewer owns all config modifications
  - Menubar app only reads config
  - Both reload config file on each access
  - Use file watchers for live updates
  - Never modify config.json directly
  - Update UI elements when config changes:
    - Check timer_menu_item exists before updating
    - Update menubar display immediately on interval change
    - Restart monitoring if interval changes during active monitoring
    - Clear menu item references during cleanup

- Config validation:
  - Validate all fields when loading
  - Provide defaults for missing fields
  - Create parent directories on first write
  - Handle permission errors gracefully

- Config change propagation:
  - Web viewer owns all config modifications
  - Config changes must propagate immediately to UI
  - Check timer_menu_item exists before updating
  - Update menubar display immediately on interval change
  - Restart monitoring if interval changes during active monitoring
  - Clear menu item references during cleanup

- Menubar Lifecycle Management
  - Initialize all menu items in setup_menu() before use
  - Never assume menu items exist after stopping monitoring
  - Clear references to menu items during cleanup
  - Handle quick start/stop cycles gracefully
  - Check menu item existence before access
  - Example error case: timer_menu_item.title access after monitoring stops

- Race condition prevention:
  - Web viewer validates before saving
  - Menubar app reloads on timer
  - Use atomic writes for config updates
  - Watch for external config changes

- Race condition prevention:
  - Web viewer validates before saving
  - Menubar app reloads on timer
  - Use atomic writes for config updates
  - Watch for external config changes

- Error handling:
  - Always check config file exists
  - Initialize with defaults if missing
  - Log config load/save errors
  - Provide clear error messages

- Research topic handling:
  - Source research topics from user config, not window context
  - Use configured topics to guide Claude analysis
  - Allow users to update topics without code changes

- Screenshot handling:
  - Only capture primary monitor to avoid PIL assertion errors
  - Skip automatic screenshots of Meadow's own interface
  - Handle macOS window detection edge cases:
    - "Window Server StatusIndicator" often appears instead of real app name
    - "Cursor" appears when window focus is ambiguous
    - Testing considerations:
      - Mock window list must include kCGWindowLayer: 0
      - Window focus state affects app name detection
      - Full screen capture may be more reliable than window detection
    - Most common during manual captures

- Data processing:
  - Use EasyOCR for text extraction
    - Requires input as numpy array, not PIL Image
    - Convert using np.array(image) before passing to readtext()
    - Initialize reader once at module level, not per function
    - Reader loads ML model which is expensive
    - Share reader instance across screenshot analysis calls
  - Consider macOS Vision API alternative
    - Native system capability could be faster
    - Better platform integration
    - Would reduce ML model loading overhead
    - TODO: Evaluate Vision API performance vs EasyOCR
  - Future improvement: Consider switching to macOS Vision framework
    - Native to macOS and optimized for Apple Silicon
    - No external ML model loading required
    - Better system integration
    - Lower memory footprint
    - Would require pyobjc-framework-Vision

- Minimize API calls
  - Check for duplicate/similar content before sending
  - Skip redundant screenshots while monitoring


- Privacy and metadata handling (TODO):
  - Track epistemic status of notes
  - Enforce privacy levels in content
  - Maintain clear evidence chains
  - Handle content redaction

## How manicode.ai works
- Designed for code editing, also works well for other tasks
- NPM library which is an API to a backend server, which itself sends requests to LLMs
- Simple interface where the user can enter a prompt
- Can also accept a folderpath and a prompt as an argument when being called
- Reads *.knowledge.md files in working directory
- Reads relevant subset of other files from directory
- Uses LLM backend to determine what changes are needed to satisfy user request and generate those changes
- Can edit files directly and run shell commands

## How manicode_wrapper.py works with the Meadow note system
- json_to_markdown.py bridges the raw notes from the JSON into the markdown
- manicode_wrapper.py creates a PTY terminal to instantiate manicode at the notes/ folder
- calls manicode with instructions to process the raw notes into the research structure
- kills the process once the action is complete or if the API times out
- does not work well with long prompts due to PTY and API issues
- manicode is fairly expensive, but can do a lot in one go, so should be called less and asked to do more each time.

## Logging Patterns

### Debug Logging
- Log all state transitions:
  - Start/stop of key operations (monitoring, analysis)
  - Before/after values for config changes
  - Entry/exit of long-running operations
  - Failures and fallback behavior
  - Config changes with old/new values
  - Monitoring lifecycle events (start, stop, interval changes)
  - Settings changes with new values
- Include timing information where relevant
- Use consistent format: "[DEBUG] Operation: detail"
- Log both old and new values for config changes
- Log complete lifecycle of features (start, stop, pause)
- Debug logging patterns:
  - Config changes: "[DEBUG] Config changed - old interval: X, new interval: Y"
  - Settings updates: "[DEBUG] Settings: changing interval to X"
  - Monitoring lifecycle: "[DEBUG] Starting monitoring loop with interval: X"
  - Monitoring state: "[DEBUG] Stopping monitoring"

### Analysis Logging
- Store complete context with each log entry:
  - Raw inputs (screenshots, PDFs, window info)
  - Processing steps (OCR text, prompts) 
  - Analysis results (summaries, topics)
  - Continuation status
- Log files are split by date:
  - Format: log_YYYYMMDD.json in logs directory
  - Each day starts with empty JSON array ([])
  - Web viewer uses date picker for navigation
  - Old entries marked as processed=true
- No single analysis_log.json file - all logs are date-based
- Handle optional fields defensively:
  - research_topic may be missing/none for non-research content
  - summary may be empty for non-relevant content
  - continuation may be unknown for first entries
- Log file handling:
  - All logs stored in ~/Library/Application Support/Meadow/data/logs/
  - Naming format: log_YYYYMMDD.json (e.g. log_20241028.json)
  - Web viewer reads from log directory based on selected date
  - Both menubar app and web viewer must use get_current_log_path() pattern
  - Always initialize new log files with empty array ([])
  - When reading logs, check for both current and previous dates

## Initialization Patterns
- Create all required directories on startup before any operations
- Initialize empty log files with valid JSON ([])
- Validate file/directory existence before operations
- Handle first-run gracefully with default configurations
- Provide clear error messages for permission/access issues
- Create parent directories when creating files (os.makedirs with exist_ok=True)

## UI Patterns
- Auto-save changes immediately with visual feedback
- Use browser-native UI components in web context
- Keep menubar icon simple but informative (📸 idle, 👁️ monitoring)
- Show status in icon title, not menu

### Menubar Lifecycle Management
- Initialize all menu items in setup_menu() before use
- Never assume menu items exist after stopping monitoring
- Clear references to menu items during cleanup
- Handle quick start/stop cycles gracefully
- Check menu item existence before access
- Example error case: timer_menu_item.title access after monitoring stops

### Web Viewer
- Full-width entries with consistent layout:
  - Left-aligned thumbnails
  - Collapsible details
  - Clear visual hierarchy
- Date-based log navigation:
  - Default to most recent log file date, not current date
  - Dropdown shows all available log dates
  - URL parameter ?date=YYYYMMDD controls displayed logs
  - Handle missing dates gracefully with empty state

### Log Viewer Management
- Store all logs in Application Support directory
- Research note generation reads from Application Support logs
- Initialize empty log files with valid JSON ([])

## TODO

### Development Priorities

1. Phase 1 (Current)
- Basic machine note generation
- LLM contribution system
- Privacy/redaction implementation
- Knowledge state tracking

2. Phase 2
- Enhanced metadata and linking
- Improved contradiction handling
- Better evidence quality tracking
- Expanded Obsidian integration

3. Future Considerations
- User editing interface
- Enhanced privacy controls
- Additional note types
- Advanced knowledge mapping
-
### Critical Path

1. Note System Implementation
   - Make sure manicode is correctly packaged
   - Create _machine/ directory structure
      ```
        screenshots/
        notes/
          _machine/                               # App-managed source notes
            city_governance/                      # Organized by topic
              san_mateo_budget_pdf/               # Organized by source
                fiscal_summary.md                 # Subtopic
                public_works.md                   # Subtopic
              city_governance.knowledge.md        # Compares sources
            machine_notes.knowledge.md            # Tracks research topics
          research/                               # User knowledge space
          meadow_notes.knowledge.md               # Overall description of research folder
      ```
   - Add browser URL capture
   - Implement metadata frontmatter handling
   - Add privacy levels and filtering system

2. Documentation
   - Installation guide for non-technical users
   - Configuration guide
   - Troubleshooting section
   - API key setup walkthrough
   - Add screenshots/demo video

### Testing Plan

1. Unit Tests
   - OCR Processing
     - Vision framework text extraction
     - EasyOCR fallback when Vision fails
     - Queue management for EasyOCR
     - Image format handling (CGImage, PNG)
     - Error handling and recovery
   - Screenshot Management
     - Window capture vs full screen fallback
     - Temp file creation and cleanup
     - Permanent storage for relevant screenshots
   - Analysis Pipeline
     - Claude API integration
     - XML response parsing
     - Research topic matching
     - Log file management

2. Integration Tests
   - Full screenshot capture → OCR → analysis pipeline
   - PDF upload → analysis → note generation
   - Web viewer log display and filtering
   - Settings persistence and reload
   - Menubar monitoring lifecycle

3. System Tests
   - macOS permissions handling
   - Multi-monitor support
   - Resource usage under load
   - Crash recovery
   - API key management

4. Performance Tests
   - OCR method comparison benchmarks
   - Screenshot capture timing
   - Analysis pipeline latency
   - Memory usage patterns
   - API response times

### Nice to Have

1. User Experience
   - First-run setup wizard (basic version)
   - Better error messages for permissions
   - Progress indicators for long operations
   - Keyboard shortcuts

2. Features
   - Auto-update mechanism
   - Backup/restore settings
   - Export research in different formats
   - Browser integration for URL capture
   - Privacy level controls
   - Metadata editing UI
   - Note organization tools

3. Testing
   - Unit test coverage
   - Integration tests
   - User acceptance testing
   - Performance benchmarks

4. Distribution
   - Website/landing page
   - Mac App Store submission
   - Update notification system
   - Analytics for crash reporting

5. Security & Privacy
   - Document data privacy practices
   - Add data deletion/export options
   - Add privacy level enforcement
   - Implement content redaction system
   - Add atomic note generation
