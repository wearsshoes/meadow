"""One-time script to split existing logs by date"""
import json
import os
from datetime import datetime

def split_logs():
    """Split the analysis_log.json file into dated files"""
    app_dir = os.path.expanduser('~/Library/Application Support/Meadow')
    log_dir = os.path.join(app_dir, 'data', 'logs')
    main_log = os.path.join(log_dir, 'analysis_log.json')

    if not os.path.exists(main_log):
        print("No log file found to split")
        return

    with open(main_log, 'r', encoding='utf-8') as f:
        logs = json.load(f)

    # Group logs by date
    dated_logs = {}
    for log in logs:
        date = datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d')
        dated_logs.setdefault(date, []).append(log)

    # Write each date's logs to a separate file
    for date, entries in dated_logs.items():
        filename = f'log_{date}.json'
        filepath = os.path.join(log_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2)

    # Rename original file as backup
    os.rename(main_log, main_log + '.bak')
    print("Log files have been split by date")

if __name__ == '__main__':
    split_logs()
