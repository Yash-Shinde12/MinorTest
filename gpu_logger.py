import time
from utils.shell_ops import get_gpu_stats
from utils.db import insert_gpu_log

def log_gpu_stats():
    """Get current GPU stats and log them to the database."""
    success, gpu_data = get_gpu_stats()
    if success and isinstance(gpu_data, list):
        for gpu in gpu_data:
            try:
                insert_gpu_log(
                    gpu_index=gpu.get('index'),
                    gpu_name=gpu.get('name'),
                    utilization=gpu.get('utilization'),
                    memory_used=gpu.get('memory_used')
                )
            except Exception as e:
                print(f"Error logging GPU stats: {str(e)}")
    else:
        print(f"Failed to get GPU stats: {gpu_data}")

def main():
    """Main loop to periodically log GPU stats."""
    interval = 300  # 5 minutes in seconds
    print("Starting GPU logger...")
    print(f"Logging interval: {interval} seconds")
    
    while True:
        try:
            log_gpu_stats()
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nGPU logger stopped.")
            break
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
            time.sleep(interval)

if __name__ == "__main__":
    main() 