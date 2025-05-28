from utils.db import init_db, insert_gpu_log, get_recent_gpu_logs
import sqlite3
import os

def test_database():
    print("Testing database functionality...")
    
    # 1. Initialize database
    print("\n1. Initializing database...")
    init_db()
    if os.path.exists('gpu_logs.db'):
        print("✓ Database file created successfully")
    else:
        print("✗ Failed to create database file")
    
    # 2. Insert test data
    print("\n2. Inserting test data...")
    try:
        insert_gpu_log(
            gpu_index=0,
            gpu_name="Test GPU",
            utilization=50.5,
            memory_used=1024
        )
        print("✓ Test data inserted successfully")
    except Exception as e:
        print(f"✗ Failed to insert test data: {str(e)}")
    
    # 3. Verify data
    print("\n3. Verifying data...")
    try:
        logs = get_recent_gpu_logs()
        if logs:
            print("✓ Data retrieved successfully")
            print("\nLast record:")
            print(f"GPU Index: {logs[0][0]}")
            print(f"GPU Name: {logs[0][1]}")
            print(f"Utilization: {logs[0][2]}%")
            print(f"Memory Used: {logs[0][3]} MiB")
            print(f"Timestamp: {logs[0][4]}")
        else:
            print("✗ No data found in database")
    except Exception as e:
        print(f"✗ Failed to retrieve data: {str(e)}")
    
    # 4. Show table schema
    print("\n4. Database schema:")
    try:
        conn = sqlite3.connect('gpu_logs.db')
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='gpu_logs';")
        schema = cursor.fetchone()[0]
        print(schema)
        conn.close()
    except Exception as e:
        print(f"✗ Failed to retrieve schema: {str(e)}")

if __name__ == "__main__":
    test_database() 