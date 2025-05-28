from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from utils.shell_ops import create_user, delete_user, list_users, get_inactive_users, get_gpu_stats, get_cpu_live_info, get_user_cpu_usage, get_user_gpu_usage  # Add new imports
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
from utils.db import insert_gpu_log, get_recent_gpu_logs

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for session
app.config['JSON_AS_ASCII'] = False  # Ensure proper JSON encoding
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto reload templates

# Login Page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['logged_in'] = True
            return redirect(url_for('display'))  # Redirect to the display page
        else:
            return render_template('login.html', error='Invalid Credentials')
    return render_template('login.html')

# Dashboard Page
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# List Users Page
@app.route('/search_user', methods=['GET', 'POST'])
def search_user_route():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').strip()
        success, users_or_error = list_users()
        if success:
            # Filter users based on the search query
            filtered_users = [user for user in users_or_error if search_query.lower() in user.lower()]
            return render_template('search_user.html', users=filtered_users, query=search_query)
        else:
            return render_template('search_user.html', error=users_or_error)
    
    # For GET requests, display all users
    success, users_or_error = list_users()
    if success:
        return render_template('search_user.html', users=users_or_error)
    else:
        return render_template('search_user.html', error=users_or_error)

# Create User Form Page
@app.route('/create_user', methods=['GET', 'POST'])
def create_user_route():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        fullname = request.form['fullname']
        room = request.form['room']
        workphone = request.form['workphone']
        homephone = request.form['homephone']
        other = request.form['other']

        success, message = create_user(username, password, fullname, room, workphone, homephone, other)
        return render_template('create_user.html', success=success, message=message)
    return render_template('create_user.html')

# Delete User Form Page
@app.route('/delete_user', methods=['GET', 'POST'])
def delete_user_route():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form['username']
        success, message = delete_user(username)  # Call the delete_user function
        return render_template('delete_user.html', success=success, message=message)
    return render_template('delete_user.html')

# List Users Page
@app.route('/list_users')
def list_users_route():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    success, users_or_error = list_users()
    if success:
        return render_template('list_users.html', users=users_or_error)
    else:
        return render_template('list_users.html', error=users_or_error)

# Add a new route for the display page
@app.route('/display')
def display():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('display.html')

# Add a new route for the server utilization dashboard
@app.route('/server_dashboard')
def server_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('serverdashboard.html')

# Add a new route for inactive users
@app.route('/inactive_users')
def inactive_users_route():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    success, users_or_error = get_inactive_users(days=30)  # Check for users inactive for 30 days
    if success:
        return render_template('inactive_users.html', users=users_or_error)
    else:
        return render_template('inactive_users.html', error=users_or_error)

@app.route('/api/gpu_stats')
def gpu_stats():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    success, gpu_data = get_gpu_stats()
    if success:
        return jsonify(gpu_data)
    else:
        return jsonify({"error": gpu_data}), 500

@app.route('/csv_analysis')
def csv_analysis():
    return render_template('csv_analysis.html')

@app.route('/api/analyze_csv', methods=['POST'])
def analyze_csv():
    if 'csvFile' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['csvFile']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400

    try:
        # Read CSV file 
        df = pd.read_csv(file)
        
        # Check required columns
        required_columns = ['GPU Index', 'GPU Name', 'Timestamp', 'Utilization %', 'Memory Used (MiB)']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Missing required columns: {", ".join(missing_columns)}'}), 400
        
        # Group data by GPU Index
        gpu_data = []
        for gpu_index in df['GPU Index'].unique():
            try:
                gpu_df = df[df['GPU Index'] == gpu_index]
                # Filter: utilization >= 1% or memory >= 100 MiB
                filtered_gpu_df = gpu_df[(gpu_df['Utilization %'] >= 1) | (gpu_df['Memory Used (MiB)'] >= 100)]
                if filtered_gpu_df.empty:
                    continue
                gpu_data.append({
                    'index': int(gpu_index),
                    'name': filtered_gpu_df['GPU Name'].iloc[0],
                    'timestamps': filtered_gpu_df['Timestamp'].tolist(),
                    'utilization': filtered_gpu_df['Utilization %'].tolist(),
                    'memory': filtered_gpu_df['Memory Used (MiB)'].tolist()
                })
            except Exception as e:
                return jsonify({'error': f'Error processing GPU {gpu_index}: {str(e)}'}), 500
        
        if not gpu_data:
            return jsonify({'error': 'No valid GPU data found in the CSV file'}), 400
            
        return jsonify(gpu_data)
    
    except pd.errors.EmptyDataError:
        return jsonify({'error': 'The CSV file is empty'}), 400
    except pd.errors.ParserError:
        return jsonify({'error': 'Error parsing CSV file. Please check the file format'}), 400
    except Exception as e:
        return jsonify({'error': f'Error processing CSV file: {str(e)}'}), 500

@app.route('/api/cpu_live_info')
def cpu_live_info():
    success, data = get_cpu_live_info()
    if success:
        return jsonify(data)
    else:
        return jsonify({'error': data}), 500

@app.route('/api/user_cpu_usage')
def user_cpu_usage():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    success, data = get_user_cpu_usage()
    if success:
        if not data:  # If no users are using CPU
            return jsonify([{
                'username': 'No active users',
                'cpu_percent': 0,
                'process_count': 0,
                'processes': []
            }])
            
        # Sort users by CPU usage
        data.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        # For each user, sort their processes by CPU usage
        for user in data:
            if 'processes' in user:
                user['processes'].sort(key=lambda x: x['cpu_percent'], reverse=True)
                # Limit to top 10 processes per user to avoid overwhelming the UI
                user['processes'] = user['processes'][:10]
        
        return jsonify(data)
    else:
        return jsonify({"error": data}), 500

@app.route('/api/user_gpu_usage')
def user_gpu_usage():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    success, data = get_user_gpu_usage()
    if success:
        if not data:  # If no users are using GPU
            return jsonify([{
                'username': 'No GPU usage',
                'gpu_memory_mib': 0
            }])
        return jsonify(data)
    else:
        if "nvidia-smi not found" in str(data):
            return jsonify([{
                'username': 'NVIDIA driver not installed',
                'gpu_memory_mib': 0
            }])
        return jsonify({"error": data}), 500

@app.route('/user_utilization')
def user_utilization():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('user_utilization.html')

@app.route('/api/historical_gpu_stats')
def historical_gpu_stats():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    time_range = request.args.get('range', 'daily')  # daily, weekly, monthly
    
    # Convert time range to hours
    hours = {
        'daily': 24,
        'weekly': 24 * 7,
        'monthly': 24 * 30
    }.get(time_range)
    
    if not hours:
        return jsonify({"error": "Invalid time range"}), 400
    
    try:
        # Get historical data from SQLite
        logs = get_recent_gpu_logs(hours=hours)
        
        # Process the data
        gpu_data = {}
        for log in logs:
            gpu_index, gpu_name, utilization, memory, timestamp = log
            
            if gpu_index not in gpu_data:
                gpu_data[gpu_index] = {
                    'index': gpu_index,
                    'name': gpu_name,
                    'timestamps': [],
                    'utilization': [],
                    'memory': []
                }
            
            gpu_data[gpu_index]['timestamps'].append(timestamp)
            gpu_data[gpu_index]['utilization'].append(utilization)
            gpu_data[gpu_index]['memory'].append(memory)
        
        return jsonify(list(gpu_data.values()))
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
