# GPU Monitoring & User Management Dashboard

A Flask-based web dashboard for monitoring GPU and CPU stats, managing users, and analyzing GPU usage from CSV files.

---

## 🚀 Features

- **Live GPU & CPU Monitoring** (Linux)
- **User Management** (create, delete, list, search, inactive users)
- **CSV Analysis**: Upload and visualize GPU usage data
- **Downloadable Reports** (charts, inactive users)
- **Modern, Responsive UI** with loading indicators and interactive charts

---

## 🛠️ Setup Instructions

### 1. **Clone the Repository**
```bash
git clone <your-repo-url>
cd <your-repo-directory>
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Run the App**
```bash
python app.py
```
- The app will be available at [http://localhost:5000](http://localhost:5000)

### 4. **Login**
- Default credentials:  
  **Username:** `admin`  
  **Password:** `admin`

---

## 📂 Folder Structure

```
.
├── app.py
├── requirements.txt
├── utils/
│   └── shell_ops.py
├── static/
│   └── ... (CSS, images)
├── templates/
│   └── ... (HTML files)
```



## 🧑‍💻 Usage Examples

- **Monitor live GPU/CPU stats** on the dashboard.
- **Upload a CSV** on the CSV Analysis page to visualize GPU usage.
- **Manage users** (create, delete, list, search, view inactive).
- **Download** charts and inactive user lists as files.

---

## 📝 API Documentation

### **Authentication**
- Most API endpoints require a valid session (login via web UI).

---

### **Endpoints**

#### `GET /api/gpu_stats`
- **Description:** Get live GPU stats.
- **Auth:** Session required.
- **Response:**  
  ```json
  [
    {
      "index": 0,
      "name": "NVIDIA RTX 6000 Ada Generation",
      "gpu_util": 2,
      "mem_util": 413,
      "mem_total": 49140,
      "mem_used": 413,
      "mem_free": 48727,
      "temperature": 45
    },
    ...
  ]
  ```

#### `GET /api/cpu_live_info`
- **Description:** Get live CPU info (Linux only).
- **Auth:** None (or session, depending on your setup).
- **Response:**  
  ```json
  {
    "cpu_percent": 12.5,
    "per_core": [10.0, 15.0, ...],
    "load_avg": [0.5, 0.7, 0.8],
    "model_name": "Intel(R) Xeon(R) CPU"
  }
  ```

#### `POST /api/analyze_csv`
- **Description:** Analyze uploaded GPU CSV file.
- **Body:** `multipart/form-data` with `csvFile`
- **Response:**  
  ```json
  [
    {
      "index": 0,
      "name": "NVIDIA RTX 6000 Ada Generation",
      "timestamps": ["2025-04-29 14:18:23", ...],
      "utilization": [2, ...],
      "memory": [413, ...]
    },
    ...
  ]
  ```

---

## 🔒 Security Notes

- Change the default admin password after setup.
- For production, use HTTPS and secure session management.

---

## 🧩 Contributing

Pull requests and suggestions are welcome!


