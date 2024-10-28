import threading
from menubar_app import MenubarApp
from web_viewer import start_viewer

def main():
    # Start web viewer in a separate thread
    viewer_thread = threading.Thread(target=start_viewer, daemon=True)
    viewer_thread.start()

    # Start the menubar app
    MenubarApp().run()

if __name__ == "__main__":
    main()
