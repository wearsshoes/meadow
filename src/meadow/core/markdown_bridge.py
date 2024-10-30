import json
import os
import shutil
from datetime import datetime
from meadow.core.manicode_wrapper import execute_manicode

class MarkdownBridge:
    """Bridge between Application Support logs and Manicode working directory"""

    def __init__(self, notes_dir):
        self.notes_dir = notes_dir
        self.machine_dir = os.path.join(notes_dir, '_machine')
        self.temp_logs_dir = os.path.join(self.machine_dir, '_temp_logs')

    def prepare_workspace(self):
        """Set up the workspace structure"""
        os.makedirs(self.machine_dir, exist_ok=True)
        os.makedirs(self.temp_logs_dir, exist_ok=True)

    def convert_logs_to_markdown(self, logs):
        """Convert JSON log entries to markdown files"""
        for log in logs:
            # Create a markdown file for each log entry
            timestamp = datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S')
            filename = f"log_{timestamp.strftime('%Y%m%d_%H%M%S')}.knowledge.md"
            filepath = os.path.join(self.temp_logs_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"""---
timestamp: {log['timestamp']}
app: {log['app']}
window: {log['window']}
research_topic: {log.get('research_topic', 'none')}
image_path: {log['image_path']}
continuation: {log['continuation']}
---

# {log['window']}

## Action
{log['description']}

## Research Topic
{log['research_topic'] if log['research_topic'] != 'none' else 'No specific research topic'}

## Summary
{log['research_summary'] if log['research_summary'] else 'No summary available'}

## OCR Text
```text
{log['ocr_text']}
```
""")
        print(f"Saved converted md to {filepath}.")

    def cleanup(self):
        """Clean up temporary files after manicode is done"""
        shutil.rmtree(self.temp_logs_dir)

async def process_analysis_result(analysis_result: dict, notes_dir: str):
    """Process a single analysis result immediately after screenshot analysis"""
    try:
        print("\n[DEBUG] Processing single analysis result...")

        # Initialize bridge
        bridge = MarkdownBridge(notes_dir)
        bridge.prepare_workspace()

        # Convert single result to markdown
        bridge.convert_logs_to_markdown([analysis_result])

    except OSError as e:
        print(f"Error processing analysis result: {e}")

    finally:
        # Clean up temporary files
        bridge.cleanup()


async def process_saved_logs(notes_dir: str):
    """Process saved unprocessed logs from Application Support"""
    # Get logs from Application Support
    app_support_dir = os.path.expanduser('~/Library/Application Support/Meadow')
    log_dir = os.path.join(app_support_dir, 'data', 'logs')

    try:
        print("\n[DEBUG] Processing saved logs...")

        # Initialize bridge
        bridge = MarkdownBridge(notes_dir)
        bridge.prepare_workspace()

        # Get all unprocessed logs from dated files
        unprocessed_logs = []

        for filename in os.listdir(log_dir):
            if filename.startswith('log_') and filename.endswith('.json') and len(filename) == 17:  # log_YYYYMMDD.json
                log_file = os.path.join(log_dir, filename)
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    # Filter for unprocessed logs
                    unprocessed = [log for log in logs if not log.get('processed', False)]
                    unprocessed_logs.extend(unprocessed)

                    # Update processed status
                    if unprocessed:
                        for log in logs:
                            if log in unprocessed:
                                log['processed'] = True
                        with open(log_file, 'w', encoding='utf-8') as f:
                            json.dump(logs, f, indent=2)

        bridge.convert_logs_to_markdown(unprocessed_logs)


    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        print(f"Error processing saved logs: {e}")

    finally:
        # Clean up temporary files
        bridge.cleanup()
