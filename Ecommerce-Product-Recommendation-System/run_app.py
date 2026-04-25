import subprocess
import os
import sys
import time

def run():
    root_dir = os.path.abspath(os.path.dirname(__file__))
    venv_python = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
    venv_streamlit = os.path.join(root_dir, ".venv", "Scripts", "streamlit.exe")

    if not os.path.exists(venv_python):
        print(f"Error: Virtual environment not found at {venv_python}")
        return

    print("Starting FastAPI Backend...")
    backend_proc = subprocess.Popen(
        [venv_python, "app.py"],
        cwd=os.path.join(root_dir, "backend")
    )

    time.sleep(2) # Give backend a moment to start

    print("Starting Streamlit Frontend...")
    frontend_proc = subprocess.Popen(
        [venv_python, "-m", "streamlit", "run", "frontend/app.py", "--server.port", "8501"],
        cwd=root_dir
    )

    print("\nProject is running!")
    print("Backend: http://127.0.0.1:8000")
    print("Frontend: http://localhost:8501")
    print("\nPress Ctrl+C to stop both servers.")

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("Backend process terminated unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                print("Frontend process terminated unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\nStopping servers...")
    finally:
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Done.")

if __name__ == "__main__":
    run()
