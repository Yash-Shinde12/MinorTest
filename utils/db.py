import sqlite3
from datetime import datetime
import os
import subprocess

DB_PATH = 'gpu_logs.db'

def get_system_timestamp():
    """Get current timestamp from system using date command on Linux."""
    try:
        # Use date command to get timestamp in ISO format
        timestamp = subprocess.check_output(['date', '+%Y-%m-%d %H:%M:%S']).decode().strip()
        return timestamp
    except Exception:
        # Fallback to Python's datetime if date command fails
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def init_db():
    """Initialize the database and create necessary tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    
    # Register custom function for system timestamp
    def system_timestamp():
        return get_system_timestamp()
    conn.create_function('system_timestamp', 0, system_timestamp)
    
    cursor = conn.cursor()
    
    # Create GPU logs table with system timestamp
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gpu_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gpu_index INTEGER,
        gpu_name TEXT,
        utilization_percent REAL,
        memory_used_mib REAL,
        timestamp DATETIME DEFAULT (system_timestamp())
    )
    ''')
    
    conn.commit()
    conn.close()

def insert_gpu_log(gpu_index, gpu_name, utilization, memory_used):
    """Insert a new GPU log entry into the database."""
    conn = sqlite3.connect(DB_PATH)
    
    # Register custom function for system timestamp
    def system_timestamp():
        return get_system_timestamp()
    conn.create_function('system_timestamp', 0, system_timestamp)
    
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO gpu_logs (gpu_index, gpu_name, utilization_percent, memory_used_mib, timestamp)
    VALUES (?, ?, ?, ?, system_timestamp())
    ''', (gpu_index, gpu_name, utilization, memory_used))
    
    conn.commit()
    conn.close()

def get_recent_gpu_logs(hours=None):
    """Get GPU logs from the last specified hours. If hours is None, returns all logs."""
    conn = sqlite3.connect(DB_PATH)
    
    # Register custom function for system timestamp
    def system_timestamp():
        return get_system_timestamp()
    conn.create_function('system_timestamp', 0, system_timestamp)
    
    cursor = conn.cursor()
    
    if hours is None:
        # Get all logs
        cursor.execute('''
        SELECT gpu_index, gpu_name, utilization_percent, memory_used_mib, timestamp
        FROM gpu_logs
        ORDER BY timestamp DESC
        ''')
    else:
        # Get logs for specified hours using system time
        cursor.execute('''
        SELECT gpu_index, gpu_name, utilization_percent, memory_used_mib, timestamp
        FROM gpu_logs
        WHERE timestamp >= datetime(system_timestamp(), '-' || ? || ' hours')
        ORDER BY timestamp DESC
        ''', (hours,))
    
    logs = cursor.fetchall()
    conn.close()
    return logs

def get_all_gpu_logs():
    """Get all GPU logs from the database."""
    return get_recent_gpu_logs(hours=None)

# Initialize the database when the module is imported
init_db() 