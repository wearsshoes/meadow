import threading
from screen_monitor_app import ScreenMonitorApp
from web_viewer import start_viewer

def main():
    # Start web viewer in a separate thread
    viewer_thread = threading.Thread(target=start_viewer, daemon=True)
    viewer_thread.start()

    # Start the menubar app
    ScreenMonitorApp().run()

if __name__ == "__main__":
    main()
