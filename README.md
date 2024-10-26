```markdown
# Selfveillance Screen Monitor

macOS menubar app that periodically captures and analyzes screenshots using Claude API.

## Features
- Menubar interface with screenshot controls
- Configurable screenshot intervals
- Automatic screenshot capture and Claude analysis
- Web viewer for browsing screenshot history

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set ANTHROPIC_API_KEY environment variable with your Claude API key

3. Run the app:
```bash
python main.py
```

## Configuration
- Config stored in ~/.screen_monitor_config.json
- Screenshots saved to ~/screen_monitor_screenshots
- Analysis logs saved as analysis_log.json in screenshots directory

## System Requirements
- macOS only (rumps dependency)
- Screen recording permissions required
- Python 3.x
```
