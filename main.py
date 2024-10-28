import multiprocessing
from menubar_app import MenubarApp
from web_viewer import start_viewer

def main():
    # Start web viewer in a separate process
    viewer_process = multiprocessing.Process(target=start_viewer)
    viewer_process.start()

    # Start the menubar app
    MenubarApp().run()

    # When the menubar app exits, terminate the web viewer process
    viewer_process.terminate()
    viewer_process.join()

if __name__ == "__main__":
    main()
