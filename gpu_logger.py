import time
import sys
import os
import logging
from datetime import datetime
from utils.shell_ops import get_gpu_stats
from utils.db import insert_gpu_log
import daemon
from daemon import pidfile

# Setup logging
def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'gpu_logger.log')),
            logging.StreamHandler(sys.stdout)
        ]
    )

def log_gpu_stats():
    """Get current GPU stats and log them to the database."""
    success, gpu_data = get_gpu_stats()
    if success and isinstance(gpu_data, list):
        for gpu in gpu_data:
            try:
                # Extract correct values from GPU data
                gpu_index = gpu.get('index')
                gpu_name = gpu.get('name')
                utilization = gpu.get('gpu_util', 0)  # Changed from 'utilization' to 'gpu_util'
                memory_used = gpu.get('mem_used', 0)  # Changed from 'memory_used' to 'mem_used'
                
                # Log the values
                insert_gpu_log(
                    gpu_index=gpu_index,
                    gpu_name=gpu_name,
                    utilization=utilization,
                    memory_used=memory_used
                )
                logging.info(f"Logged stats for GPU {gpu_index}: Utilization={utilization}%, Memory={memory_used}MiB")
            except Exception as e:
                logging.error(f"Error logging GPU stats: {str(e)}")
                logging.error(f"GPU data received: {gpu}")  # Added to debug data structure
    else:
        logging.error(f"Failed to get GPU stats: {gpu_data}")

def main():
    """Main loop to periodically log GPU stats."""
    setup_logging()
    interval = 300  # 5 minutes in seconds
    
    logging.info("Starting GPU logger daemon...")
    logging.info(f"Logging interval: {interval} seconds")
    logging.info("Logger will run indefinitely until stopped manually")
    
    while True:
        try:
            log_gpu_stats()
            time.sleep(interval)
        except KeyboardInterrupt:
            logging.info("GPU logger stopped by user.")
            break
        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
            time.sleep(interval)

def run():
    """Run the daemon process."""
    pid_file = '/tmp/gpu_logger.pid'
    
    # Create daemon context
    context = daemon.DaemonContext(
        working_directory=os.getcwd(),
        umask=0o002,
        pidfile=pidfile.TimeoutPIDLockFile(pid_file),
    )
    
    # Open the daemon context and run the main function
    with context:
        main()

if __name__ == "__main__":
    run() 