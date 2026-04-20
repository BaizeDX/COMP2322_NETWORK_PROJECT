import socket
import os
import threading
import time
import subprocess
from datetime import datetime

# Server configuration
HOST = '127.0.0.1'
PORT = 8080
WEB_ROOT = 'webs'
LOG_FILE = 'logs/server.log'

# Global counters for statistics
request_count = 0
start_time = time.time()
counter_lock = threading.Lock()

# MIME type mapping for different file extensions
MIME_TYPES = {
    '.html': 'text/html',
    '.htm': 'text/html',
    '.txt': 'text/plain',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.css': 'text/css',
    '.js': 'application/javascript',
}

def get_uptime():
    """Get server uptime in human readable format"""
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    return f"{hours}h {minutes}m {seconds}s"

def get_recent_logs(lines=10):
    """Get the most recent log entries"""
    try:
        if not os.path.exists(LOG_FILE):
            return "No logs yet."
        with open(LOG_FILE, 'r') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except:
        return "Unable to read logs."

def get_http_date(timestamp=None):
    """Convert timestamp to HTTP date format (RFC 1123)"""
    if timestamp is None:
        timestamp = time.time()
    return time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp))

def parse_if_modified_since(header_value):
    """Parse If-Modified-Since header to timestamp"""
    try:
        return time.mktime(time.strptime(header_value, '%a, %d %b %Y %H:%M:%S GMT'))
    except:
        return None

def get_mime_type(filepath):
    """Return the MIME type based on file extension"""
    ext = os.path.splitext(filepath)[1].lower()
    return MIME_TYPES.get(ext, 'application/octet-stream')

def write_log(client_ip, method, path, status_code):
    """Write request log to file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{client_ip} | {timestamp} | {method} {path} | {status_code}\n"
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)

def parse_headers(request_data):
    """Parse HTTP headers from request data"""
    headers = {}
    lines = request_data.split('\r\n')
    
    for line in lines[1:]:
        if ': ' in line:
            key, value = line.split(': ', 1)
            headers[key] = value
        elif line == '':
            break
    return headers

def generate_status_page():
    """Generate server status HTML page"""
    global request_count
    
    with counter_lock:
        current_requests = request_count
    
    active_threads = threading.active_count() - 1
    
    # Get status code statistics from log
    status_stats = {}
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                for line in f:
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 4:
                            status = parts[3].strip()
                            status_stats[status] = status_stats.get(status, 0) + 1
    except:
        pass
    
    # Build status table rows
    status_rows = ""
    for code, count in sorted(status_stats.items()):
        status_rows += f"<tr><td>{code}</td><td>{count}</td></tr>\n"
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Server Status</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background: #4CAF50;
            color: white;
        }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .metric {{
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        }}
        .log-box {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .nav {{
            background: #333;
            overflow: hidden;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .nav a {{
            float: left;
            color: white;
            text-align: center;
            padding: 14px 20px;
            text-decoration: none;
        }}
        .nav a:hover {{
            background: #4CAF50;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-success {{ background: #4CAF50; color: white; }}
        .badge-warning {{ background: #ff9800; color: white; }}
        .badge-error {{ background: #f44336; color: white; }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #888;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="/">Home</a>
        <a href="/status">Status</a>
    </div>
    
    <h1>🚀 Web Server Status Dashboard</h1>
    
    <div class="card">
        <h2>📊 Server Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Server Uptime</td><td class="metric">{get_uptime()}</td></tr>
            <tr><td>Active Threads</td><td class="metric">{active_threads}</td></tr>
            <tr><td>Total Requests Processed</td><td class="metric">{current_requests}</td></tr>
            <tr><td>Port</td><td>{PORT}</td></tr>
            <tr><td>Document Root</td><td>{os.path.abspath(WEB_ROOT)}</td></tr>
            <tr><td>Log File</td><td>{os.path.abspath(LOG_FILE)}</td></tr>
        </table>
    </div>
    
    <div class="card">
        <h2>📈 Status Code Distribution</h2>
        <table>
            <tr><th>Status Code</th><th>Count</th></tr>
            {status_rows if status_rows else "<tr><td colspan='2'>No requests yet</td></tr>"}
        </table>
    </div>
    
    <div class="card">
        <h2>📋 Recent Logs (Last 10 lines)</h2>
        <div class="log-box">{get_recent_logs()}</div>
    </div>
    
    <div class="card">
        <h2>🔧 Supported Features</h2>
        <table>
            <tr><th>Feature</th><th>Status</th></tr>
            <tr><td>Multi-threading</td><td><span class="badge badge-success">✓ Enabled</span></td></tr>
            <tr><td>GET Method</td><td><span class="badge badge-success">✓ Supported</span></td></tr>
            <tr><td>HEAD Method</td><td><span class="badge badge-success">✓ Supported</span></td></tr>
            <tr><td>Keep-Alive Connections</td><td><span class="badge badge-success">✓ Supported</span></td></tr>
            <tr><td>Last-Modified / 304</td><td><span class="badge badge-success">✓ Supported</span></td></tr>
            <tr><td>Path Traversal Protection</td><td><span class="badge badge-success">✓ Enabled</span></td></tr>
            <tr><td>Logging</td><td><span class="badge badge-success">✓ Enabled</span></td></tr>
        </table>
    </div>
    
    <div class="footer">
        <p>Multi-Thread Web Server | Built for Comp 2322 Computer Networking</p>
        <p>Current Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
</body>
</html>
    """

def handle_client(client_socket, client_addr):
    """Handle a single client request (runs in its own thread)"""
    global request_count
    
    client_ip = client_addr[0]
    print(f"[New connection] From: {client_addr}")
    
    connection_open = True
    
    while connection_open:
        try:
            request_data = client_socket.recv(4096).decode('utf-8', errors='ignore')
            
            if not request_data:
                break
            
            request_line = request_data.splitlines()[0] if request_data.splitlines() else ""
            parts = request_line.split()
            
            if len(parts) < 2:
                status_code = 400
                send_error_response(client_socket, 400, "Bad Request", "Invalid request format")
                write_log(client_ip, "UNKNOWN", "UNKNOWN", status_code)
                break
            
            method, path, version = parts[0], parts[1], parts[2] if len(parts) > 2 else "HTTP/1.1"
            
            headers = parse_headers(request_data)
            
            # Update request counter
            with counter_lock:
                request_count += 1
            
            # Check Connection header
            connection_header = headers.get('Connection', '').lower()
            if connection_header == 'close':
                connection_open = False
            else:
                connection_open = (version == 'HTTP/1.1')
            
            print(f"[Request] {method} {path}")
            
            # Special handler for /status page
            if path == "/status":
                status_html = generate_status_page()
                content = status_html.encode('utf-8')
                content_type = 'text/html'
                last_modified = get_http_date()
                
                if method == "GET":
                    send_success_response(client_socket, content_type, content, last_modified, connection_open)
                elif method == "HEAD":
                    send_head_response(client_socket, content_type, len(content), last_modified, connection_open)
                else:
                    send_error_response(client_socket, 405, "Method Not Allowed", f"Method {method} not supported")
                
                write_log(client_ip, method, path, 200)
                if not connection_open:
                    break
                continue
            
            # Handle root path
            if path == "/":
                path = "/index.html"
            
            safe_path = path.lstrip('/')
            file_path = os.path.join(WEB_ROOT, safe_path)
            
            # Security check
            real_root = os.path.realpath(WEB_ROOT)
            real_file = os.path.realpath(file_path)
            if not real_file.startswith(real_root):
                status_code = 403
                send_error_response(client_socket, 403, "Forbidden", "Access denied")
                write_log(client_ip, method, path, status_code)
                break
            
            if not os.path.exists(file_path):
                status_code = 404
                send_error_response(client_socket, 404, "Not Found", f"File '{path}' not found")
                write_log(client_ip, method, path, status_code)
                break
            
            if not os.path.isfile(file_path):
                status_code = 404
                send_error_response(client_socket, 404, "Not Found", "Requested path is not a file")
                write_log(client_ip, method, path, status_code)
                break
            
            file_mtime = os.path.getmtime(file_path)
            file_mtime_http = get_http_date(file_mtime)
            
            # Check If-Modified-Since
            if_modified_since = headers.get('If-Modified-Since', '')
            if if_modified_since:
                client_time = parse_if_modified_since(if_modified_since)
                if client_time is not None and file_mtime <= client_time:
                    send_304_response(client_socket)
                    write_log(client_ip, method, path, 304)
                    if not connection_open:
                        break
                    continue
            
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
            except PermissionError:
                status_code = 403
                send_error_response(client_socket, 403, "Forbidden", "Permission denied")
                write_log(client_ip, method, path, status_code)
                break
            
            content_type = get_mime_type(file_path)
            
            if method == "GET":
                send_success_response(client_socket, content_type, file_content, file_mtime_http, connection_open)
                status_code = 200
            elif method == "HEAD":
                send_head_response(client_socket, content_type, len(file_content), file_mtime_http, connection_open)
                status_code = 200
            else:
                send_error_response(client_socket, 405, "Method Not Allowed", f"Method {method} not supported")
                status_code = 405
            
            write_log(client_ip, method, path, status_code)
            
        except Exception as e:
            print(f"[Error] {e}")
            try:
                send_error_response(client_socket, 500, "Internal Server Error", "Server error occurred")
                write_log(client_ip, "ERROR", "ERROR", 500)
            except:
                pass
            break
    
    client_socket.close()
    print(f"[Connection closed] {client_addr}\n")

def send_success_response(client_socket, content_type, content, last_modified, keep_alive):
    """Send HTTP 200 OK response with headers and body"""
    connection_header = "keep-alive" if keep_alive else "close"
    response_headers = (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(content)}\r\n"
        f"Last-Modified: {last_modified}\r\n"
        f"Connection: {connection_header}\r\n"
        "\r\n"
    )
    client_socket.send(response_headers.encode() + content)

def send_head_response(client_socket, content_type, content_length, last_modified, keep_alive):
    """Send HTTP 200 OK response with headers ONLY"""
    connection_header = "keep-alive" if keep_alive else "close"
    response_headers = (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {content_length}\r\n"
        f"Last-Modified: {last_modified}\r\n"
        f"Connection: {connection_header}\r\n"
        "\r\n"
    )
    client_socket.send(response_headers.encode())

def send_304_response(client_socket):
    """Send 304 Not Modified response"""
    response_headers = (
        "HTTP/1.1 304 Not Modified\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    client_socket.send(response_headers.encode())

def send_error_response(client_socket, status_code, status_text, error_message):
    """Send HTTP error response with HTML error page"""
    body = f"""
    <html>
    <head><title>{status_code} {status_text}</title></head>
    <body>
        <h1>{status_code} {status_text}</h1>
        <p>{error_message}</p>
        <hr>
        <p>Multi-Thread Web Server | <a href="/status">Server Status</a></p>
    </body>
    </html>
    """
    response_headers = (
        f"HTTP/1.1 {status_code} {status_text}\r\n"
        "Content-Type: text/html\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    client_socket.send(response_headers.encode() + body.encode())

def main():
    """Main server entry point"""
    global start_time
    
    # Ensure webs directory exists
    if not os.path.exists('webs'):
        os.makedirs('webs')
        print("[Info] Created webs/ directory")
    
    # Ensure index.html exists
    index_path = os.path.join('webs', 'index.html')
    if not os.path.exists(index_path):
        with open(index_path, 'w') as f:
            f.write("""<html>
<head><title>Web Server</title></head>
<body>
    <h1>Web Server Working!</h1>
    <p>This is index.html</p>
    <p>If you see this, your server is running correctly.</p>
    <p>📊 <a href="/status">View Server Status Dashboard</a></p>
</body>
</html>""")
        print("[Info] Created webs/index.html")
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    print("[Info] Created logs/ directory")
    
    # Create TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    
    print(f"Server started: http://{HOST}:{PORT}")
    print(f"Document root: {WEB_ROOT}/")
    print(f"Log file: {LOG_FILE}")
    print(f"Status page: http://{HOST}:{PORT}/status")
    print("Waiting for connections...\n")
    
    start_time = time.time()
    
    while True:
        client_socket, client_addr = server_socket.accept()
        client_thread = threading.Thread(
            target=handle_client, 
            args=(client_socket, client_addr)
        )
        client_thread.start()
        print(f"[Active threads] {threading.active_count() - 1}")

if __name__ == "__main__":
    main()
