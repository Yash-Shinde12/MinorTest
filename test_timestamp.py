from utils.db import get_system_timestamp
import subprocess

def test_timestamps():
    print("Testing timestamp functionality...")
    
    # 1. Get timestamp from our function
    print("\n1. Timestamp from our function:")
    db_timestamp = get_system_timestamp()
    print(f"DB timestamp: {db_timestamp}")
    
    # 2. Get direct system timestamp for comparison
    print("\n2. Direct system timestamp:")
    try:
        system_time = subprocess.check_output(['date', '+%Y-%m-%d %H:%M:%S']).decode().strip()
        print(f"System time: {system_time}")
    except Exception as e:
        print(f"Error getting system time: {str(e)}")
    
    # 3. Insert and retrieve from database
    print("\n3. Database test:")
    from utils.db import insert_gpu_log, get_recent_gpu_logs
    
    # Insert test data
    insert_gpu_log(0, "Test GPU", 50, 1024)
    
    # Get most recent log
    logs = get_recent_gpu_logs()
    if logs:
        print(f"Database timestamp: {logs[0][4]}")  # timestamp is the 5th field
    else:
        print("No logs found in database")

if __name__ == "__main__":
    test_timestamps() 