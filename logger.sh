#!/bin/bash

# Output CSV file
LOG_FILE="gpu_usage_log.csv"

# Interval between checks (in seconds)
INTERVAL=5

# Write CSV header if file doesn't exist
if [ ! -f "$LOG_FILE" ]; then
    echo "timestamp,type,gpu_id,gpu_name,username,pid,utilization_gpu,utilization_mem,memory_total,memory_used,memory_free,temperature,used_memory" >> "$LOG_FILE"
fi

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    ###### Per-GPU Stats Logging ######
    nvidia-smi --query-gpu=index,name,utilization.gpu,utilization.memory,memory.total,memory.used,memory.free,temperature.gpu \
               --format=csv,noheader,nounits | while IFS=',' read -r index name util_gpu util_mem mem_total mem_used mem_free temp; do
        echo "$TIMESTAMP,GPU,$index,$name,N/A,N/A,$util_gpu,$util_mem,$mem_total,$mem_used,$mem_free,$temp,N/A" >> "$LOG_FILE"
    done

    ###### Per-User GPU Process Logging ######
    nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv,noheader,nounits | while IFS=',' read -r pid uuid mem; do
        if ps -p "$pid" > /dev/null 2>&1; then
            user=$(ps -o user= -p "$pid")
            echo "$TIMESTAMP,USER,N/A,N/A,$user,$pid,N/A,N/A,N/A,N/A,N/A,N/A,$mem" >> "$LOG_FILE"
        fi
    done

    sleep $INTERVAL
done

