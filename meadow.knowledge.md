# Meadow
A macOS menubar app that acts as an AI research assistant by analyzing your screen activity using Claude API.

## Project Mission
- Assist researchers by tracking and analyzing topic-relevant content
- Filter and analyze content based on configured research topics
- Generate detailed summaries of relevant research material
- Keep all data private and local

## Core Design Principles
- Screenshot handling:
  - Only capture primary monitor to avoid PIL assertion errors
  - Skip automatic screenshots of Meadow's own interface
- Provide visibility into AI processing:
  - Log extracted text before analysis
  - Show intermediate steps in console
  - Make AI "thinking" visible to user
- Co-locate related data
  - Keep research logs with research notes
  - Separate application data from user content
- Skip automatic screenshots of Meadow's own interface
- Prefer simple solutions over complex ones
- Use multiprocessing for clean process separation
- Use modern ML-based approaches where beneficial
  - EasyOCR for text extraction (chosen over Tesseract for accuracy)
    - Requires input as file path, bytes, or numpy array (not PIL Image)
    - Convert PIL Images using np.array(image) before passing to readtext()
    - Requires input as file path, bytes, or numpy array (not PIL Image)
    - Convert PIL Images using np.array(image) before passing to readtext()
  - Claude API for content analysis
- Use modern ML-based approaches where beneficial
  - EasyOCR for text extraction (chosen over Tesseract for accuracy)
  - Claude API for content analysis

## UI Patterns
- Auto-save changes immediately with visual feedback
- Use browser-native UI components in web context
- Keep menubar icon simple but informative (📸 idle, 👁️ monitoring)
- Show status in icon title, not menu
- Provide console output for background operations
  - Log progress during note generation
  - Show errors and completion status
  - Print key execution points
  - Maintain visibility throughout execution

## Architecture
- menubar_app.py: UI and coordination
  - Run monitoring in separate thread from UI
  - Run analysis in separate thread from monitoring
  - Use threading for non-blocking operations
  - Keep UI responsive during long operations
- Use manicode wrapper for:
  - Research log analysis
  - Note synthesis and organization
  - Maintaining knowledge graph connections

## Data Storage
Application data in ~/Library/Application Support/Meadow/:
- config/config.json - User preferences
- data/screenshots/ - Screenshot images
- data/logs/ - Analysis logs
- cache/thumbnails/ - Web viewer thumbnail cache

### Initialization Patterns
- Create all required directories on startup before any operations
- Initialize empty log files with valid JSON ([])
- Validate file/directory existence before operations
- Handle first-run gracefully with default configurations
- Provide clear error messages for permission/access issues
- Create parent directories when creating files (os.makedirs with exist_ok=True)

### Initialization Patterns
- Create all required directories on startup before any operations
- Initialize empty log files with valid JSON ([])
- Validate file/directory existence before operations
- Handle first-run gracefully with default configurations
- Provide clear error messages for permission/access issues
- Create parent directories when creating files (os.makedirs with exist_ok=True)

User content in configurable locations:
- Research notes and analysis logs stored together
- Notes follow Obsidian-style markdown format
- Use bidirectional links between related concepts
- Focus on recent, relevant content

## Dependencies
- rumps - macOS menubar app framework
- pillow - Image processing
- anthropic - Claude API client
- pyobjc-framework-Quartz - Native macOS window management
- Flask - Web viewer server
- py2app - macOS app bundling

### Dependency Management
- Use setup.py as single source of truth for dependencies
- Generate requirements.txt only when needed: `pip install . && pip freeze > requirements.txt`
- Keep setup.py install_requires minimal - only direct dependencies
  - Requires Carbon.framework
  - Must include all required frameworks in OPTIONS
  - Common issues:
    - Carbon.framework missing: Add to py2app packages
    - Icon not showing: Verify icon path relative to bundle
    - Framework errors: Check dyld paths

## Todo for Publishing

### Critical Path
1. Package the app ✓
   - Create setup.py for pip installation ✓
   - Bundle as macOS .app with py2app ✓
   - Add app icon and proper signing
2. Security & Privacy ⚡
   - Add proper error handling for missing screen recording permissions ✓
   - Secure storage of API keys ✓
### Initialization Patterns
- Create all required directories on startup before any operations
- Initialize empty log files with valid JSON ([])
- Validate file/directory existence before operations
- Handle first-run gracefully with default configurations
- Provide clear error messages for permission/access issues
- Create parent directories when creating files (os.makedirs with exist_ok=True)

- pyobjc-framework-Quartz - Native macOS window management
- Flask - Web viewer server
   - ✓ Create setup.py for pip installation
   - ✓ Bundle as macOS .app with py2app
   - Test installation flow on clean machine

2. Security & Privacy
   - ✓ Add proper error handling for missing screen recording permissions
   - ✓ Secure storage of API keys
   - Document data privacy practices
   - Add data deletion/export options

3. Documentation
   - Installation guide for non-technical users
   - Configuration guide
   - Troubleshooting section
   - ✓ API key setup walkthrough
   - Add screenshots/demo video

### Nice to Have
1. User Experience
   - ✓ First-run setup wizard (basic version)
   - ✓ Better error messages for permissions
   - Progress indicators for long operations
   - Keyboard shortcuts

2. Features
   - Auto-update mechanism
   - Backup/restore settings
   - Export research in different formats
   - Configurable file organization

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
