import socket
import os
import threading
import time
from datetime import datetime

# Server configuration
HOST = '127.0.0.1'
PORT = 8080
WEB_ROOT = 'webs'
LOG_FILE = 'logs/server.log'

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

def get_mime_type(filepath):
    """Return the MIME type based on file extension"""
    ext = os.path.splitext(filepath)[1].lower()
    return MIME_TYPES.get(ext, 'application/octet-stream')

def write_log(client_ip, method, path, status_code):
    """Write request log to file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{client_ip} | {timestamp} | {method} {path} | {status_code}\n"
    
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    # Write to log file
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)

def handle_client(client_socket, client_addr):
    """Handle a single client request (runs in its own thread)"""
    client_ip = client_addr[0]
    print(f"[New connection] From: {client_addr}")
    
    try:
        # Receive HTTP request
        request_data = client_socket.recv(4096).decode('utf-8', errors='ignore')
        
        if not request_data:
            client_socket.close()
            return
        
        # Parse request line
        request_line = request_data.splitlines()[0] if request_data.splitlines() else ""
        parts = request_line.split()
        
        # Validate request format
        if len(parts) < 2:
            status_code = 400
            send_error_response(client_socket, 400, "Bad Request", "Invalid request format")
            write_log(client_ip, "UNKNOWN", "UNKNOWN", status_code)
            client_socket.close()
            return
        
        method, path, version = parts[0], parts[1], parts[2] if len(parts) > 2 else "HTTP/1.1"
        
        print(f"[Request] {method} {path}")
        
        # Handle root path
        if path == "/":
            path = "/index.html"
        
        # Convert URL path to file system path
        safe_path = path.lstrip('/')
        file_path = os.path.join(WEB_ROOT, safe_path)
        
        # Security check: prevent directory traversal attacks
        real_root = os.path.realpath(WEB_ROOT)
        real_file = os.path.realpath(file_path)
        if not real_file.startswith(real_root):
            status_code = 403
            send_error_response(client_socket, 403, "Forbidden", "Access denied")
            write_log(client_ip, method, path, status_code)
            client_socket.close()
            return
        
        # Check if file exists
        if not os.path.exists(file_path):
            status_code = 404
            send_error_response(client_socket, 404, "Not Found", f"File '{path}' not found")
            write_log(client_ip, method, path, status_code)
            client_socket.close()
            return
        
        # Check if it's a file (not a directory)
        if not os.path.isfile(file_path):
            status_code = 404
            send_error_response(client_socket, 404, "Not Found", "Requested path is not a file")
            write_log(client_ip, method, path, status_code)
            client_socket.close()
            return
        
        # Read file content
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
        except PermissionError:
            status_code = 403
            send_error_response(client_socket, 403, "Forbidden", "Permission denied")
            write_log(client_ip, method, path, status_code)
            client_socket.close()
            return
        
        content_type = get_mime_type(file_path)
        
        # Handle different HTTP methods
        if method == "GET":
            send_success_response(client_socket, content_type, file_content)
            status_code = 200
        elif method == "HEAD":
            send_head_response(client_socket, content_type, len(file_content))
            status_code = 200
        else:
            send_error_response(client_socket, 405, "Method Not Allowed", f"Method {method} not supported")
            status_code = 405
        
        # Log the request
        write_log(client_ip, method, path, status_code)
        
    except Exception as e:
        print(f"[Error] {e}")
        try:
            status_code = 500
            send_error_response(client_socket, 500, "Internal Server Error", "Server error occurred")
            write_log(client_ip, "ERROR", "ERROR", status_code)
        except:
            pass
    
    client_socket.close()
    print(f"[Connection closed] {client_addr}\n")

def send_success_response(client_socket, content_type, content):
    """Send HTTP 200 OK response with headers and body"""
    response_headers = (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(content)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    client_socket.send(response_headers.encode() + content)

def send_head_response(client_socket, content_type, content_length):
    """Send HTTP 200 OK response with headers ONLY (no body)"""
    response_headers = (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {content_length}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    client_socket.send(response_headers.encode())
    # Note: No body is sent for HEAD requests

def send_error_response(client_socket, status_code, status_text, error_message):
    """Send HTTP error response with HTML error page"""
    body = f"""
    <html>
    <head><title>{status_code} {status_text}</title></head>
    <body>
        <h1>{status_code} {status_text}</h1>
        <p>{error_message}</p>
        <hr>
        <p>Multi-Thread Web Server</p>
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
</body>
</html>""")
        print("[Info] Created webs/index.html")
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    print("[Info] Created logs/ directory")
    
    # Create TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Allow port reuse
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to address and port
    server_socket.bind((HOST, PORT))
    
    # Start listening
    server_socket.listen(5)
    
    print(f"Server started: http://{HOST}:{PORT}")
    print(f"Document root: {WEB_ROOT}/")
    print(f"Log file: {LOG_FILE}")
    print("Waiting for connections...\n")
    
    # Main loop: accept and handle connections with threads
    while True:
        client_socket, client_addr = server_socket.accept()
        
        # Create a new thread for each client
        client_thread = threading.Thread(
            target=handle_client, 
            args=(client_socket, client_addr)
        )
        client_thread.start()
        
        # Optional: Print active thread count
        print(f"[Active threads] {threading.active_count() - 1}")  # -1 for main thread

if __name__ == "__main__":
    main()
