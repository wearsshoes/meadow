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
- Separate UI concerns from configuration management
  - Web interface handles all config modifications
  - Menubar app has read-only access to config
  - Prevents race conditions between interfaces
  - Makes config changes traceable through web UI

- Research topic handling:
  - Source research topics from user config, not window context
  - Use configured topics to guide Claude analysis
  - Allow users to update topics without code changes

- Screenshot handling:
  - Only capture primary monitor to avoid PIL assertion errors
  - Skip automatic screenshots of Meadow's own interface
  - Handle macOS window detection edge cases:
    - "Window Server StatusIndicator" often appears instead of real app name
    - Most common during manual captures

- Data processing:
  - Use EasyOCR for text extraction
    - Requires input as numpy array, not PIL Image
    - Convert using np.array(image) before passing to readtext()

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

### Web Viewer
- Full-width entries with consistent layout:
  - Left-aligned thumbnails
  - Collapsible details
  - Clear visual hierarchy

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
