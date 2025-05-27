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
        # Run the command to get CPU usage by user
        command = "ps -eo user,%cpu,uid --sort=-%cpu | awk 'NR>1 && $3>=1000 {cpu[$1]+=$2} END {for (u in cpu) print u, cpu[u]}' | sort -k2 -nr"
        result = subprocess.run(
            ['bash', '-c', command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            return False, result.stderr.strip()

        # Parse the output
        user_cpu_usage = []
        for line in result.stdout.strip().split('\n'):
            if line:
                username, cpu_percent = line.split()
                user_cpu_usage.append({
                    'username': username,
                    'cpu_percent': float(cpu_percent)
                })

        return True, user_cpu_usage
    except Exception as e:
        return False, f"Error fetching user CPU usage: {str(e)}"

def get_user_gpu_usage():
    try:
        # Run the command to get GPU usage by user
        command = '''
        nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader,nounits | while read -r pid pname mem; do
            uid=$(stat -c %u /proc/$pid 2>/dev/null)
            if [ "$uid" -ge 1000 ]; then
                user=$(ps -o user= -p $pid)
                echo "$user $mem"
            fi
        done | awk '{mem[$1]+=$2} END {for (u in mem) print u, mem[u]}' | sort -k2 -nr
        '''
        
        result = subprocess.run(
            ['bash', '-c', command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            return False, result.stderr.strip()

        # Parse the output
        user_gpu_usage = []
        for line in result.stdout.strip().split('\n'):
            if line:
                username, gpu_memory = line.split()
                user_gpu_usage.append({
                    'username': username,
                    'gpu_memory_mib': float(gpu_memory)
                })

        return True, user_gpu_usage
    except Exception as e:
        return False, f"Error fetching user GPU usage: {str(e)}"

