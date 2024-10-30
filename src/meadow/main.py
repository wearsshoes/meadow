import multiprocessing
from meadow.ui.menubar_app import MenubarApp
from meadow.web.web_viewer import start_viewer

def main():
    print("\n[DEBUG] Starting Meadow...")
    # Start web viewer in a separate process
    viewer_process = multiprocessing.Process(target=start_viewer)
    viewer_process.start()

    try:
        # Start the menubar app
        MenubarApp().run()
    except Exception as e:
        print(f"[ERROR] Menubar app crashed: {e}")
    finally:
        # Always clean up the web viewer process
        print("[DEBUG] Cleaning up web viewer...")
        viewer_process.terminate()
        viewer_process.join(timeout=5)  # Wait up to 5 seconds
        if viewer_process.is_alive():
            viewer_process.kill()  # Force kill if still running
            viewer_process.join()

if __name__ == "__main__":
    main()
