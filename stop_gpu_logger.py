import os
import signal
import sys

def stop_daemon():
    try:
        # Read PID from file
        with open('/tmp/gpu_logger.pid', 'r') as f:
            pid = int(f.read().strip())
        
        # Send SIGTERM signal to the process
        os.kill(pid, signal.SIGTERM)
        print(f"Successfully stopped GPU logger daemon (PID: {pid})")
        
        # Remove PID file
        os.remove('/tmp/gpu_logger.pid')
        print("Removed PID file")
        
    except FileNotFoundError:
        print("GPU logger daemon is not running (PID file not found)")
    except ProcessLookupError:
        print("GPU logger daemon is not running (Process not found)")
        # Clean up stale PID file if it exists
        try:
            os.remove('/tmp/gpu_logger.pid')
        except FileNotFoundError:
            pass
    except Exception as e:
        print(f"Error stopping GPU logger daemon: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    stop_daemon() 