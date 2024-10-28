# Meadow
A macOS menubar app that acts as an AI research assistant by analyzing your screen activity using Claude API.

## Project Mission
- Assist researchers by tracking and analyzing topic-relevant content
- Filter and analyze content based on configured research topics
- Generate detailed summaries of relevant research material
- Keep all data private and local

## Core Design Principles
- Co-locate related data
  - Keep research logs with research notes
  - Separate application data from user content
- Skip automatic screenshots of Meadow's own interface
- Prefer simple solutions over complex ones
- Use multiprocessing for clean process separation

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
