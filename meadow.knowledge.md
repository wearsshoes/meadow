# Meadow
A macOS menubar app that acts as an AI research assistant by analyzing your screen activity using Claude API.

## Knowledge Organization
Information about how the manicode wrapper interacts with notes is stored in ./src/meadow/core/notes.knowledge.md

## Project Mission
- Assist researchers by tracking and analyzing topic-relevant content
- Filter and analyze content based on configured research topics
- Generate detailed summaries of relevant research material
- Contribute new information to the user's existing markdown notes

## Architecture

### Core
- monitor.py
  - runs the monitoring loop and saves logs
- analyzer.py
  - contains the core logic and api calls
- manicode_wrapper.py
  - used to create notes from analysis

### UI
- menubar_app.py: UI and coordination
  - monitor continuously or analyze current screen
  - open web viewer

### Web
- web_viewer.py: settings and logs
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
- notes.knowledge.md - contains info about the organization of the notes for manicode's sake.
- _machine/ - (TODO) atomic notes from source material
  - browsers/ - organized by browser and URL
  - apps/ - organized by application
  - metadata.json - tracks processed logs
- research/ - (TODO) user's research notes with AI contributions
- screenshots/ - screenshots generated from monitoring
- this entire folder is accessible to manicode via the wrapper.

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

## Logging Patterns
- Store complete context with each log entry:
  - Raw inputs (screenshots, window info)
  - Processing steps (OCR text, prompts)
  - Analysis results (summaries, topics)
  - Continuation status
- Initialize empty log files with valid JSON ([])

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

   - Implement metadata tracking
   - Add browser URL capture
   - Add privacy filtering system
   - Add note contribution system
   - Include Manicode if necessary.
   - Implement metadata frontmatter handling
   - Add privacy levels and content redaction
   - Create machine/user space separation
   - Add epistemic status tracking
   - Implement browser integration for URL capture

1. Security & Privacy
   - Document data privacy practices
   - Add data deletion/export options
   - Add privacy level enforcement
   - Implement content redaction system
   - Add atomic note generation

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
