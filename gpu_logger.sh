#!/bin/bash

# === CONFIGURATION ===
INTERVAL=5  # Interval in seconds
LOG_DIR=~/Desktop/GPU_Usage_Logs
mkdir -p "$LOG_DIR"

# === FUNCTIONS ===

log_gpu_usage() {
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    date_day=$(date +"%Y-%m-%d")
    date_week=$(date +"%Y-%V")     # Year-WeekNumber
    date_month=$(date +"%Y-%m")

    daily_log="$LOG_DIR/gpu_usage_daily_$date_day.csv"
    weekly_log="$LOG_DIR/gpu_usage_weekly_$date_week.csv"
    monthly_log="$LOG_DIR/gpu_usage_monthly_$date_month.csv"

    # Get GPU usage from nvidia-smi
    data=$(nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader,nounits)

    # Format data
    output=""
    while IFS=',' read -r pid pname mem; do
        user=$(ps -o user= -p $pid 2>/dev/null)
        if [ -n "$user" ]; then
            output+="$timestamp,$user,$pid,$pname,${mem}MiB"$'\n'
        fi
    done <<< "$data"

    # If no data, write timestamp with 'No GPU usage'
    if [ -z "$output" ]; then
        output="$timestamp,NONE,NONE,NONE,0MiB"
    fi

    # Header if not exists
    for file in "$daily_log" "$weekly_log" "$monthly_log"; do

