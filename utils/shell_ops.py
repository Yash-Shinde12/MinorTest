import subprocess
import pexpect

def create_user(username, password, fullname, room, workphone, homephone, other):
    try:
        child = pexpect.spawn(f"sudo adduser {username}")
        child.timeout = 10

        child.expect("New password:")
        child.sendline(password)

        child.expect("Retype new password:")
        child.sendline(password)

        child.expect("Full Name")
        child.sendline(fullname)

        child.expect("Room Number")
        child.sendline(room)

        child.expect("Work Phone")
        child.sendline(workphone)

        child.expect("Home Phone")
        child.sendline(homephone)

        child.expect("Other")
        child.sendline(other)

        child.expect("Is the information correct?")
        child.sendline("Y")

        child.expect(pexpect.EOF)

        return True, f"User '{username}' created successfully."

    except Exception as e:
        return False, f"Error during user creation: {str(e)}"


def delete_user(username):
    try:
        child = pexpect.spawn(f"sudo deluser {username}")

        # Set a timeout in case something hangs
        child.timeout = 10

        child.expect("Removing user")
        child.sendline("Y")

        child.expect(pexpect.EOF)  # Wait for process to end

        return True, f"User '{username}' deleted successfully."

    except Exception as e:
        #return False, f"Error during user deletion: {str(e)}"
        return False, f"User {username} does not exist or is not a system user."

def list_users():
    try:
        # Fetch users with UID >= 1000 (non-system users)
        child = pexpect.spawn("awk -F: '$3 >= 1000 && $3 < 65534 { print $1 }' /etc/passwd")
        child.timeout = 10
        child.expect(pexpect.EOF)
        users = child.before.decode().splitlines()
        return True, users
    except Exception as e:
        return False, f"Error during user listing: {str(e)}"

def get_inactive_users(days=7):  # Changed default to 7 days
    try:
        # Create the command as a shell script
        command = f'''
        awk -F: '$3 >= 1000 && $1 != "nobody" {{ print $1 }}' /etc/passwd | while read user; do
            lastlog -u "$user" | tail -n 1 | awk -v u="$user" -v days={days} '
            {{
                if ($0 ~ /Never logged in/) {{
                    print u ": Never logged in"
                }} else {{
                    login = $4 " " $5 " " $6 " " $7
                    cmd = "date -d \"" login "\" +%s"
                    cmd | getline login_time
                    close(cmd)
                    now = systime()
                    if ((now - login_time) > (days * 86400)) {{
                        print u ": Last login over " days " days ago (" login ")"
                    }}
                }}
            }}'
        done
        '''
        
        # Run the command
        result = subprocess.run(
            ['bash', '-c', command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            return False, result.stderr.strip()

        # Process the output
        inactive_users = []
        for line in result.stdout.strip().split('\n'):
            if line:  # Skip empty lines
                # Extract just the username from the detailed output
                username = line.split(':')[0].strip()
                if username:
                    inactive_users.append(line)  # Store the full message instead of just username

        return True, inactive_users

    except Exception as e:
        return False, f"Error fetching inactive users: {str(e)}"

def get_gpu_stats():
    try:
        # Run the `nvidia-smi` command
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,utilization.gpu,utilization.memory,memory.total,memory.used,memory.free,temperature.gpu", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            return False, result.stderr.strip()

        # Parse the output
        gpu_stats = []
        for line in result.stdout.strip().split("\n"):
            fields = line.split(", ")
            gpu_stats.append({
                "index": int(fields[0]),
                "name": fields[1],
                "gpu_util": int(fields[2]),
                "mem_util": int(fields[3]),
                "mem_total": int(fields[4]),
                "mem_used": int(fields[5]),
                "mem_free": int(fields[6]),
                "temperature": int(fields[7])
            })

        return True, gpu_stats
    except Exception as e:
        return False, f"Error fetching GPU stats: {str(e)}"

def get_cpu_live_info():
    import platform
    import os
    import subprocess
    try:
        if platform.system() != 'Linux':
            return False, 'Live CPU info only supported on Linux.'
        # Get CPU usage percentage (average over all cores)
        cpu_percent = None
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.5)
            per_core = psutil.cpu_percent(interval=0.5, percpu=True)
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (None, None, None)
        except ImportError:
            # Fallback to top command
            top_out = subprocess.check_output(["top", "-bn1"]).decode()
            for line in top_out.split("\n"):
                if "Cpu(s):" in line:
                    cpu_percent = float(line.split("%id,")[0].split()[-1])
                    cpu_percent = 100 - cpu_percent  # idle to usage
                    per_core = []
                    break
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (None, None, None)
        # Get CPU info
        cpu_info = subprocess.check_output(["lscpu"]).decode()
        model_name = None
        for line in cpu_info.split("\n"):
            if "Model name:" in line:
                model_name = line.split(":", 1)[1].strip()
                break
        return True, {
            'cpu_percent': cpu_percent,
            'per_core': per_core,
            'load_avg': load_avg,
            'model_name': model_name
        }
    except Exception as e:
        return False, str(e)

def get_user_cpu_usage():
    try:
        # More detailed command that gets process info with CPU usage per user
        command = """
        ps aux --no-headers | awk '
        BEGIN {
            PROCCOUNT=0
            CPUSUM=0
        }
        {
            user=$1
            pid=$2
            cpu=$3
            mem=$4
            cmd=substr($0, index($0,$11))  # Get full command
            if (cpu > 0.0) {  # Only count processes using CPU
                CPUSUM[user] += cpu
                PROCCOUNT[user] += 1
                # Store process details in an array
                if (length(PROCDETAILS[user]) < 1000) {  # Limit details to avoid overflow
                    PROCDETAILS[user] = PROCDETAILS[user] sprintf("%d,%.1f,%.1f,%s;", pid, cpu, mem, cmd)
                }
            }
        }
        END {
            for (user in CPUSUM) {
                if (user != "root" && user != "nobody" && user != "systemd+") {
                    # Print: username, total CPU, process count, and process details
                    printf "%s,%.2f,%d,%s\\n", user, CPUSUM[user], PROCCOUNT[user], PROCDETAILS[user]
                }
            }
        }' | sort -t, -k2 -nr
        """
        
        result = subprocess.run(
            ['bash', '-c', command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={'LANG': 'C'}  # Ensure consistent output format
        )
        
        if result.returncode != 0:
            return False, result.stderr.strip()

        # Parse the output into a more detailed structure
        user_cpu_usage = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    # Split the main fields
                    user_data = line.split(',', 3)  # Split into 4 parts: user, cpu, proccount, details
                    if len(user_data) >= 4:
                        username, cpu_percent, proc_count = user_data[0:3]
                        process_details = []
                        
                        # Parse process details
                        if user_data[3]:
                            for proc in user_data[3].split(';'):
                                if proc:
                                    pid, proc_cpu, proc_mem, cmd = proc.split(',', 3)
                                    process_details.append({
                                        'pid': int(pid),
                                        'cpu_percent': float(proc_cpu),
                                        'memory_percent': float(proc_mem),
                                        'command': cmd.strip()
                                    })
                        
                        user_cpu_usage.append({
                            'username': username,
                            'cpu_percent': float(cpu_percent),
                            'process_count': int(proc_count),
                            'processes': process_details
                        })
                except (ValueError, IndexError) as e:
                    continue  # Skip malformed lines
                
        return True, user_cpu_usage
    except Exception as e:
        return False, f"Error fetching user CPU usage: {str(e)}"

def get_user_gpu_usage():
    try:
        # More robust command for GPU usage by user
        command = """
        nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits 2>/dev/null | while read -r line; do
            if [ ! -z "$line" ]; then
                pid=$(echo $line | cut -d, -f1)
                mem=$(echo $line | cut -d, -f2)
                if [ -e "/proc/$pid" ]; then
                    user=$(ps -o user= -p $pid 2>/dev/null)
                    if [ ! -z "$user" ] && [ "$user" != "root" ]; then
                        echo "$user $mem"
                    fi
                fi
            fi
        done | awk '
        {
            mem[$1] += $2
        }
        END {
            for (user in mem) {
                printf "%s %.0f\n", user, mem[user]
            }
        }' | sort -k2 -nr
        """
        
        result = subprocess.run(
            ['bash', '-c', command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={'LANG': 'C'}  # Ensure consistent output format
        )
        
        if result.returncode != 0:
            # Check if nvidia-smi is available
            nvidia_check = subprocess.run(['which', 'nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if nvidia_check.returncode != 0:
                return False, "nvidia-smi not found. Please ensure NVIDIA drivers are installed."
            return False, result.stderr.strip()

        # Parse the output
        user_gpu_usage = []
        for line in result.stdout.strip().split('\n'):
            if line and not line.isspace():
                try:
                    username, gpu_memory = line.split()
                    user_gpu_usage.append({
                        'username': username,
                        'gpu_memory_mib': float(gpu_memory)
                    })
                except (ValueError, IndexError) as e:
                    continue  # Skip malformed lines

        return True, user_gpu_usage
    except Exception as e:
        return False, f"Error fetching user GPU usage: {str(e)}"

