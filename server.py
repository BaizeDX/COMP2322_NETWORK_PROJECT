import html
import os
import socket
import threading
import time
from datetime import datetime
from email.utils import formatdate, parsedate_to_datetime
from urllib.parse import unquote, urlsplit

# Server configuration
HOST = '127.0.0.1'
PORT = 8848
WEB_ROOT = 'webs'
LOG_FILE = 'logs/server.log'
MAX_REQUEST_SIZE = 65536
SOCKET_TIMEOUT = 10

# Global stats
request_count = 0
start_time = time.time()
counter_lock = threading.Lock()      # Protects request_count
log_lock = threading.Lock()           # Protects log file writes

# MIME type mapping
MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.htm': 'text/html; charset=utf-8',
    '.txt': 'text/plain; charset=utf-8',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
}


def get_uptime():
    """Return human-readable server uptime"""
    elapsed = int(time.time() - start_time)
    hours, rem = divmod(elapsed, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours}h {minutes}m {seconds}s"


def get_recent_logs(lines=10):
    """Return last N lines from log file"""
    try:
        if not os.path.exists(LOG_FILE):
            return "No logs yet."
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return ''.join(f.readlines()[-lines:]) or "No logs yet."
    except OSError:
        return "Unable to read logs."


def get_http_date(timestamp=None):
    """Convert timestamp to RFC 1123 HTTP date format"""
    if timestamp is None:
        timestamp = time.time()
    return formatdate(timestamp, usegmt=True)


def parse_if_modified_since(value):
    """Parse If-Modified-Since header to timestamp"""
    try:
        dt = parsedate_to_datetime(value)
        return dt.timestamp()
    except Exception:
        return None


def get_mime_type(filepath):
    """Return MIME type based on file extension"""
    ext = os.path.splitext(filepath)[1].lower()
    return MIME_TYPES.get(ext, 'application/octet-stream')


def write_log(client_ip, method, path, status_code):
    """Append request log entry (thread-safe)"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{client_ip} | {timestamp} | {method} {path} | {status_code}\n"
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with log_lock:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)


def parse_headers(request_data):
    """Parse HTTP headers into case-insensitive dict"""
    headers = {}
    lines = request_data.split('\r\n')
    for line in lines[1:]:
        if not line:
            break
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip().lower()] = value.strip()
    return headers


def generate_status_page():
    """Generate real-time status dashboard HTML"""
    with counter_lock:
        current_requests = request_count

    active_threads = max(threading.active_count() - 1, 0)
    status_stats = {}
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 4:
                        code = parts[3]
                        status_stats[code] = status_stats.get(code, 0) + 1
    except OSError:
        pass

    status_rows = ''.join(
        f"<tr><td>{html.escape(code)}</td><td>{count}</td></tr>"
        for code, count in sorted(status_stats.items())
    )
    if not status_rows:
        status_rows = "<tr><td colspan='2'>No requests yet</td></tr>"

    recent_logs = html.escape(get_recent_logs())

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Server Status</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .metric {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
        .log-box {{ background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; font-family: 'Courier New', monospace; font-size: 12px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }}
        .nav {{ background: #333; overflow: hidden; border-radius: 5px; margin-bottom: 20px; }}
        .nav a {{ float: left; color: white; text-align: center; padding: 14px 20px; text-decoration: none; }}
        .nav a:hover {{ background: #4CAF50; }}
        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }}
        .badge-success {{ background: #4CAF50; color: white; }}
        .footer {{ text-align: center; margin-top: 30px; color: #888; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="/">Home</a>
        <a href="/status">Status</a>
    </div>

    <h1>Web Server Status Dashboard</h1>

    <div class="card">
        <h2>Server Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Server Uptime</td><td class="metric">{get_uptime()}</td></tr>
            <tr><td>Active Threads</td><td class="metric">{active_threads}</td></tr>
            <tr><td>Total Requests Processed</td><td class="metric">{current_requests}</td></tr>
            <tr><td>Port</td><td>{PORT}</td></tr>
            <tr><td>Document Root</td><td>{html.escape(os.path.abspath(WEB_ROOT))}</td></tr>
            <tr><td>Log File</td><td>{html.escape(os.path.abspath(LOG_FILE))}</td></tr>
        </table>
    </div>

    <div class="card">
        <h2>Status Code Distribution</h2>
        <table>
            <tr><th>Status Code</th><th>Count</th></tr>
            {status_rows}
        </table>
    </div>

    <div class="card">
        <h2>Recent Logs</h2>
        <div class="log-box">{recent_logs}</div>
    </div>

    <div class="card">
        <h2>Supported Features</h2>
        <table>
            <tr><th>Feature</th><th>Status</th></tr>
            <tr><td>Multi-threading</td><td><span class="badge badge-success">Enabled</span></td></tr>
            <tr><td>GET Method</td><td><span class="badge badge-success">Supported</span></td></tr>
            <tr><td>HEAD Method</td><td><span class="badge badge-success">Supported</span></td></tr>
            <tr><td>Keep-Alive Connections</td><td><span class="badge badge-success">Supported</span></td></tr>
            <tr><td>Last-Modified / 304</td><td><span class="badge badge-success">Supported</span></td></tr>
            <tr><td>Path Traversal Protection</td><td><span class="badge badge-success">Enabled</span></td></tr>
            <tr><td>Logging</td><td><span class="badge badge-success">Enabled</span></td></tr>
        </table>
    </div>

    <div class="footer">
        <p>Multi-Thread Web Server | Built for Comp 2322 Computer Networking</p>
        <p>Current Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
</body>
</html>
"""


def recv_http_request(client_socket):
    """Read HTTP request until headers complete (\\r\\n\\r\\n)"""
    data = b''
    while b'\r\n\r\n' not in data:
        chunk = client_socket.recv(4096)
        if not chunk:
            break
        data += chunk
        if len(data) > MAX_REQUEST_SIZE:
            raise ValueError('Request too large')
    return data.decode('iso-8859-1', errors='replace')


def should_keep_alive(version, headers):
    """Determine if connection should persist after response"""
    connection = headers.get('connection', '').lower()
    if version == 'HTTP/1.1':
        return connection != 'close'      # HTTP/1.1 defaults to keep-alive
    return connection == 'keep-alive'     # HTTP/1.0 defaults to close


def resolve_file_path(path):
    """Safely resolve file path and prevent directory traversal"""
    parsed = urlsplit(path)
    clean_path = unquote(parsed.path)      # Decode URL-encoded characters
    if clean_path == '/':
        clean_path = '/index.html'
    safe_path = clean_path.lstrip('/')
    file_path = os.path.join(WEB_ROOT, safe_path)
    real_root = os.path.realpath(WEB_ROOT)
    real_file = os.path.realpath(file_path)
    # Security: ensure resolved path is inside web root
    if os.path.commonpath([real_root, real_file]) != real_root:
        return None, clean_path
    return real_file, clean_path


def handle_client(client_socket, client_addr):
    """Handle a single client connection (runs in its own thread)"""
    global request_count

    client_ip = client_addr[0]
    print(f"[New connection] From: {client_addr}")
    client_socket.settimeout(SOCKET_TIMEOUT)

    try:
        while True:
            # Read HTTP request
            try:
                request_data = recv_http_request(client_socket)
            except socket.timeout:
                break
            except ValueError:
                send_error_response(client_socket, 413, 'Payload Too Large', 'Request header too large', False)
                write_log(client_ip, 'UNKNOWN', 'UNKNOWN', 413)
                break

            if not request_data:
                break

            # Parse request line
            request_line = request_data.split('\r\n', 1)[0]
            parts = request_line.split()
            if len(parts) != 3:
                send_error_response(client_socket, 400, 'Bad Request', 'Invalid request line', False)
                write_log(client_ip, 'UNKNOWN', 'UNKNOWN', 400)
                break

            method, path, version = parts
            headers = parse_headers(request_data)
            keep_alive = should_keep_alive(version, headers)

            if version not in ('HTTP/1.0', 'HTTP/1.1'):
                send_error_response(client_socket, 400, 'Bad Request', 'Unsupported HTTP version', False)
                write_log(client_ip, method, path, 400)
                break

            # Update global counter
            with counter_lock:
                request_count += 1

            print(f"[Request] {method} {path}")

            # Special endpoint: status dashboard
            if path == '/status':
                status_html = generate_status_page().encode('utf-8')
                if method == 'GET':
                    send_success_response(client_socket, 'text/html; charset=utf-8', status_html, get_http_date(), keep_alive)
                    status_code = 200
                elif method == 'HEAD':
                    send_head_response(client_socket, 'text/html; charset=utf-8', len(status_html), get_http_date(), keep_alive)
                    status_code = 200
                else:
                    send_error_response(client_socket, 405, 'Method Not Allowed', f'Method {method} not supported', False)
                    status_code = 405
                    keep_alive = False
                write_log(client_ip, method, path, status_code)
                if not keep_alive:
                    break
                continue

            # Resolve and validate file path
            file_path, clean_path = resolve_file_path(path)
            if file_path is None:
                send_error_response(client_socket, 403, 'Forbidden', 'Access denied', False)
                write_log(client_ip, method, path, 403)
                break

            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                send_error_response(client_socket, 404, 'Not Found', f"File '{clean_path}' not found", False)
                write_log(client_ip, method, clean_path, 404)
                break

            if method not in ('GET', 'HEAD'):
                send_error_response(client_socket, 405, 'Method Not Allowed', f'Method {method} not supported', False)
                write_log(client_ip, method, clean_path, 405)
                break

            # Cache validation
            try:
                file_mtime = os.path.getmtime(file_path)
                if_modified_since = parse_if_modified_since(headers.get('if-modified-since', ''))
                if if_modified_since is not None and int(file_mtime) <= int(if_modified_since):
                    send_304_response(client_socket, keep_alive)
                    write_log(client_ip, method, clean_path, 304)
                    if not keep_alive:
                        break
                    continue

                with open(file_path, 'rb') as f:
                    content = f.read()
            except PermissionError:
                send_error_response(client_socket, 403, 'Forbidden', 'Permission denied', False)
                write_log(client_ip, method, clean_path, 403)
                break
            except OSError:
                send_error_response(client_socket, 500, 'Internal Server Error', 'Failed to read file', False)
                write_log(client_ip, method, clean_path, 500)
                break

            # Send response
            content_type = get_mime_type(file_path)
            last_modified = get_http_date(file_mtime)

            if method == 'GET':
                send_success_response(client_socket, content_type, content, last_modified, keep_alive)
            else:  # HEAD
                send_head_response(client_socket, content_type, len(content), last_modified, keep_alive)
            write_log(client_ip, method, clean_path, 200)

            if not keep_alive:
                break

    except Exception as e:
        print(f"[Error] {e}")
        try:
            send_error_response(client_socket, 500, 'Internal Server Error', 'Server error occurred', False)
            write_log(client_ip, 'ERROR', 'ERROR', 500)
        except Exception:
            pass
    finally:
        client_socket.close()
        print(f"[Connection closed] {client_addr}\n")


def send_success_response(client_socket, content_type, content, last_modified, keep_alive):
    """Send HTTP 200 OK response with body"""
    connection_header = 'keep-alive' if keep_alive else 'close'
    headers = (
        'HTTP/1.1 200 OK\r\n'
        f'Content-Type: {content_type}\r\n'
        f'Content-Length: {len(content)}\r\n'
        f'Last-Modified: {last_modified}\r\n'
        f'Connection: {connection_header}\r\n'
        '\r\n'
    )
    client_socket.sendall(headers.encode('ascii') + content)


def send_head_response(client_socket, content_type, content_length, last_modified, keep_alive):
    """Send HTTP 200 OK response without body (headers only)"""
    connection_header = 'keep-alive' if keep_alive else 'close'
    headers = (
        'HTTP/1.1 200 OK\r\n'
        f'Content-Type: {content_type}\r\n'
        f'Content-Length: {content_length}\r\n'
        f'Last-Modified: {last_modified}\r\n'
        f'Connection: {connection_header}\r\n'
        '\r\n'
    )
    client_socket.sendall(headers.encode('ascii'))


def send_304_response(client_socket, keep_alive):
    """Send 304 Not Modified response (no body)"""
    connection_header = 'keep-alive' if keep_alive else 'close'
    headers = (
        'HTTP/1.1 304 Not Modified\r\n'
        f'Connection: {connection_header}\r\n'
        '\r\n'
    )
    client_socket.sendall(headers.encode('ascii'))


def send_error_response(client_socket, status_code, status_text, error_message, keep_alive=False):
    """Send HTTP error response with HTML error page"""
    body = f"""<html>
<head><title>{status_code} {status_text}</title></head>
<body>
    <h1>{status_code} {status_text}</h1>
    <p>{html.escape(error_message)}</p>
    <hr>
    <p>Multi-Thread Web Server | <a href=\"/status\">Server Status</a></p>
</body>
</html>""".encode('utf-8')
    connection_header = 'keep-alive' if keep_alive else 'close'
    headers = (
        f'HTTP/1.1 {status_code} {status_text}\r\n'
        'Content-Type: text/html; charset=utf-8\r\n'
        f'Content-Length: {len(body)}\r\n'
        f'Connection: {connection_header}\r\n'
        '\r\n'
    )
    client_socket.sendall(headers.encode('ascii') + body)


def ensure_directories():
    """Create required directories and default files on first run"""
    os.makedirs(WEB_ROOT, exist_ok=True)
    print('[Info] Created webs/ directory')
    index_path = os.path.join(WEB_ROOT, 'index.html')
    if not os.path.exists(index_path):
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("""<html>
<head><title>Web Server</title></head>
<body>
    <h1>Web Server Working!</h1>
    <p>This is index.html</p>
    <p>If you see this, your server is running correctly.</p>
    <p><a href=\"/status\">View Server Status Dashboard</a></p>
</body>
</html>""")
        print('[Info] Created webs/index.html')
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    print('[Info] Created logs/ directory')


def main():
    """Main server entry point"""
    global start_time
    ensure_directories()

    # Create and configure server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(20)

    print(f'Server started: http://{HOST}:{PORT}')
    print(f'Document root: {WEB_ROOT}/')
    print(f'Log file: {LOG_FILE}')
    print(f'Status page: http://{HOST}:{PORT}/status')
    print('Waiting for connections...\n')

    start_time = time.time()

    try:
        # Main accept loop - each client gets its own thread
        while True:
            client_socket, client_addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_addr), daemon=True)
            client_thread.start()
            print(f'[Active threads] {max(threading.active_count() - 1, 0)}')
    finally:
        server_socket.close()


if __name__ == '__main__':
    main()
