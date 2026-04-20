# Multi-Thread Web Server

A multi-threaded web server implemented from scratch in Python using socket programming. Supports HTTP/1.1 features including persistent connections, cache validation, and concurrent request handling.

## 📋 Features

### Core Features
- ✅ **Multi-threading** - Handles multiple client requests concurrently
- ✅ **GET Method** - Serves both text files (HTML, CSS, JS, TXT) and image files (JPG, PNG, GIF)
- ✅ **HEAD Method** - Returns response headers without body for file inspection
- ✅ **HTTP Status Codes** - Full support for 200, 304, 400, 403, 404, 405, 500

### Advanced Features
- ✅ **Cache Validation** - Last-Modified and If-Modified-Since headers with 304 responses
- ✅ **Persistent Connections** - HTTP keep-alive support (reuses TCP connections)
- ✅ **Path Traversal Protection** - Security against directory traversal attacks (../)
- ✅ **MIME Type Detection** - Automatic Content-Type identification for various file types
- ✅ **Request Logging** - Comprehensive logging with client IP, timestamp, request, and status code
- ✅ **Status Dashboard** - Real-time server statistics at `/status` endpoint

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- No additional packages required (uses only standard library)

### Installation

1. Clone or download the project files:
```bash
git clone <repository-url>
cd multi-thread-web-server
```

2. No installation needed - the server uses only Python standard library.

### Running the Server

```bash
python server.py
```

Expected output:
```
[Info] Created webs/ directory
[Info] Created webs/index.html
[Info] Created logs/ directory
Server started: http://127.0.0.1:8080
Document root: webs/
Log file: logs/server.log
Status page: http://127.0.0.1:8080/status
Waiting for connections...
```

### Testing the Server

Open another terminal and run:

```bash
# Test GET request
curl http://127.0.0.1:8080/

# Test HEAD request
curl -I http://127.0.0.1:8080/

# Test 304 Not Modified (use the Last-Modified time from previous response)
curl -v --header "If-Modified-Since: Tue, 15 Apr 2025 10:30:00 GMT" http://127.0.0.1:8080/

# Test 404 Not Found
curl http://127.0.0.1:8080/nonexistent.html

# View server status dashboard
curl http://127.0.0.1:8080/status

# Or open in browser
open http://127.0.0.1:8080/
```

## 📁 Project Structure

```
multi-thread-web-server/
├── server.py          # Main server implementation
├── webs/              # Web root directory (static files)
│   └── index.html     # Default homepage (auto-generated)
├── logs/              # Log directory
│   └── server.log     # Request log file (auto-generated)
└── README.md          # This file
```

## 🔧 Configuration

Edit the following variables in `server.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `'127.0.0.1'` | Server listening address |
| `PORT` | `8080` | Server port number |
| `WEB_ROOT` | `'webs'` | Directory for static files |
| `LOG_FILE` | `'logs/server.log'` | Log file path |

## 📊 Log Format

Log entries are pipe-separated for easy parsing:

```
127.0.0.1 | 2026-04-20 15:30:45 | GET /index.html | 200
127.0.0.1 | 2026-04-20 15:30:46 | HEAD /style.css | 200
127.0.0.1 | 2026-04-20 15:30:47 | GET /missing.html | 404
```

## 🧪 Test Commands

### Basic Tests

```bash
# 1. Test default page
curl -v http://127.0.0.1:8080/

# 2. Test static file
echo "Hello World" > webs/test.txt
curl http://127.0.0.1:8080/test.txt

# 3. Test image file (place an image in webs/ first)
curl -O http://127.0.0.1:8080/photo.jpg

# 4. Test HEAD method
curl -I http://127.0.0.1:8080/index.html

# 5. Test 404
curl -v http://127.0.0.1:8080/does-not-exist.html

# 6. Test 403 (path traversal attack)
curl -v http://127.0.0.1:8080/../server.py

# 7. Test 304 (cache validation)
# First request - get Last-Modified time
curl -v http://127.0.0.1:8080/index.html 2>&1 | grep -i last-modified
# Second request - use that time
curl -v --header "If-Modified-Since: Tue, 15 Apr 2025 10:30:00 GMT" http://127.0.0.1:8080/index.html
```

### Concurrent Test (Multi-threading)

```bash
# Run multiple simultaneous requests
for i in {1..10}; do curl http://127.0.0.1:8080/ & done
wait
# Check active threads in server console
```

### Keep-Alive Test

```bash
# Using telnet
telnet 127.0.0.1 8080
# Then paste:
GET /index.html HTTP/1.1
Host: 127.0.0.1
Connection: keep-alive

# (Wait for response, then send another request)
GET /index.html HTTP/1.1
Host: 127.0.0.1
Connection: close
```

## 📈 Status Dashboard

The server provides a real-time status dashboard at `http://127.0.0.1:8080/status` featuring:

- Server uptime
- Active thread count
- Total requests processed
- Status code distribution
- Recent log entries (last 10 lines)
- Supported features checklist

## 🔒 Security Features

- **Path Traversal Protection**: Blocks requests containing `..` to prevent access outside web root
- **Permission Checking**: Returns 403 for files without read permission
- **Input Validation**: Validates request format before processing
- **Safe Path Resolution**: Uses `os.path.realpath()` to resolve symbolic links safely

## 🛠️ Troubleshooting

### Port already in use
```bash
# Change PORT in server.py or kill the process using port 8080
lsof -i :8080
kill -9 <PID>
```

### Permission denied
```bash
# Ensure webs/ directory has read permissions
chmod -R 755 webs/
```

### Log file not writing
```bash
# Ensure logs/ directory exists and is writable
mkdir -p logs
chmod 755 logs
```

## 📝 Code Structure

| Function | Purpose |
|----------|---------|
| `main()` | Server entry point, creates listening socket |
| `handle_client()` | Main request handler (runs in threads) |
| `send_success_response()` | Sends HTTP 200 response |
| `send_head_response()` | Sends HTTP HEAD response |
| `send_304_response()` | Sends 304 Not Modified |
| `send_error_response()` | Sends error responses |
| `parse_headers()` | Extracts headers from HTTP request |
| `write_log()` | Appends to log file |
| `generate_status_page()` | Creates `/status` dashboard HTML |

## 🎯 Requirements Met

| Requirement | Status |
|-------------|--------|
| Multi-threaded web server | ✅ |
| Proper request/response exchange | ✅ |
| GET for text files | ✅ |
| GET for image files | ✅ |
| HEAD command | ✅ |
| 200 OK | ✅ |
| 400 Bad Request | ✅ |
| 403 Forbidden | ✅ |
| 404 Not Found | ✅ |
| 304 Not Modified | ✅ |
| Last-Modified header | ✅ |
| If-Modified-Since header | ✅ |
| Connection: keep-alive | ✅ |
| Connection: close | ✅ |
| Log file | ✅ |

## 👨‍💻 Author

- Course: Comp 2322 Computer Networking
- Language: Python 3
- Implementation: Socket programming from scratch

## 📄 License

This project is for educational purposes as part of the Comp 2322 Computer Networking course.

## 🙏 Acknowledgments

- HTTP/1.1 specification (RFC 2616)
- Python socket programming documentation

