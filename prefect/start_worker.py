import subprocess
import sys
import os

def start_worker():
    """Start a Prefect worker for task processing"""
    try:
        # Start the worker
        subprocess.run([
            "prefect", "worker", "start",
            "-p", "task-processing",  # Work queue name
            "-n", "task-processor-worker"  # Worker name
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting worker: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nWorker stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    start_worker() 