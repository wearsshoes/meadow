# ReThread
A macOS menubar app that acts as an AI research assistant by analyzing your screen activity using Claude API.

## Project Mission
- Assist researchers by tracking and analyzing topic-relevant content
- Filter and analyze content based on configured research topics
- Generate detailed summaries of relevant research material
- Keep all data private and local

## Core Design Principles
- Skip automatic screenshots of ReThread's own interface
  - Check active window before taking screenshot
  
- UI Patterns
  - Auto-save changes immediately with visual feedback
  - Use browser-native UI components over OS-native when in web context
  - Keep menubar icon simple but informative (📸 idle, 👁️ monitoring)
  - Show status in icon title, not menu

- Prefer simple solutions over complex ones
- Use multiprocessing for clean process separation
Application data stored in ~/Library/Application Support/ReThread/:
- config/config.json - User preferences
- data/screenshots/ - Screenshot images
- data/logs/ - Analysis logs
- cache/thumbnails/ - Web viewer thumbnail cache
User content stored in configurable locations:
- All paths configurable through settings
## Dependencies
- rumps 0.4.0 - macOS menubar app framework
- pillow 11.0.0 - Image processing
- anthropic 0.37.1 - Claude API client
- pyobjc-framework-Quartz - Native macOS window management
- Flask 3.0.3 - Web viewer server
- Validate loaded config has all required keys
- Use XML tags for structured AI responses
- Keep UI minimal and intuitive
- menubar_app.py: UI and coordination

## Data Storage
- Screenshots and logs stored in ~/Library/Application Support/ReThread/
- Research notes default to ~/Documents/ReThread Notes
- All paths configurable through settings

## Requirements
- macOS only
- Screen recording permissions
- Anthropic API key in environment