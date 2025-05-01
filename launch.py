import subprocess
import webbrowser
import time
import os
from app import app

def launch_app():
    """Launch Flask server and open browser."""
    print("Starting MapPhone Extractor...")
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static/css", exist_ok=True)
    os.makedirs("static/js", exist_ok=True)
    
    flask_process = subprocess.Popen(
        ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"],
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(2)
    
    print("Opening web interface in your default browser...")
    webbrowser.open("http://localhost:5000")
    
    try:
        flask_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        flask_process.terminate()
        flask_process.wait()

if __name__ == "__main__":
    launch_app()