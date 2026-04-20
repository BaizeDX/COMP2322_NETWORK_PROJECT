# Multi-Thread Web Server

A production-ready multi-threaded web server implemented from scratch in Python using socket programming. Fully compliant with HTTP/1.1 features including persistent connections, cache validation, concurrent request handling, and real-time monitoring.

## 📋 Features

### Core Features
- ✅ **Multi-threading** - Thread-per-connection model with daemon threads for clean shutdown
- ✅ **GET Method** - Serves text files (HTML, CSS, JS, JSON, TXT) and images (JPG, PNG, GIF, SVG, ICO)
- ✅ **HEAD Method** - Returns response headers without body for resource inspection
- ✅ **HTTP Status Codes** - Full support for 200, 304, 400, 403, 404, 405, 413, 500

### Advanced Features
- ✅ **Robust Request Reading** - Loop-based recv() that handles split TCP packets
- ✅ **Cache Validation** - RFC-compliant Last-Modified / If-Modified-Since with timestamp comparison
- ✅ **Persistent Connections** - HTTP/1.1 keep-alive with correct Connection header handling
- ✅ **Path Traversal Protection** - Two-layer defense using realpath and commonpath validation
- ✅ **MIME Type Detection** - Automatic Content-Type for 15+ file extensions
- ✅ **Thread-Safe Logging** - Lock-protected pipe-separated log entries (IP, timestamp, request, status)
- ✅ **Status Dashboard** - Real-time HTML dashboard at `/status` with XSS protection
- ✅ **Zero-Config Startup** - Auto-creates webs/, logs/, and default index.html

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- No external packages required (uses only standard library)

### Running the Server

```bash
python server.py
```

Expected output:
```
[Info] Created webs/ directory
[Info] Created webs/index.html
[Info] Created logs/ directory
Server started: http://127.0.0.1:8848
Document root: webs/
Log file: logs/server.log
Status page: http://127.0.0.1:8848/status
Waiting for connections...
```

### Testing the Server

```bash
# Test GET request
curl http://127.0.0.1:8848/index.html

# Test HEAD request
curl -I http://127.0.0.1:8848/index.html

# Test 304 Not Modified (use actual Last-Modified value)
curl -v --header "If-Modified-Since: Mon, 20 Apr 2026 14:50:23 GMT" http://127.0.0.1:8848/index.html

# Test 404 Not Found
curl http://127.0.0.1:8848/nonexistent.html

# Test 403 Forbidden (use --path-as-is to prevent curl from normalizing)
curl --path-as-is http://127.0.0.1:8848/../server.py

# View status dashboard
curl http://127.0.0.1:8848/status
# Or open in browser
open http://127.0.0.1:8848/status
```

## 📁 Project Structure

```
project/
├── logs/
│   └── server.log                 # Server runtime log
├── report/
│   ├── Screenshots/               # Test screenshots directory
│   │   ├── 01_server_startup.png
│   │   ├── 02_stage1_request.png
│   │   ├── 03_get_text.png
│   │   ├── 04a_get_image_browser.png
│   │   ├── 04b_get_image_curl.png
│   │   ├── 05_head_method.png
│   │   ├── 06_404_not_found.png
│   │   ├── 07_403_forbidden.png
│   │   ├── 08_400_bad_request.png
│   │   ├── 09_10_lastmod_304.png
│   │   ├── 11_12_keepalive_close.png
│   │   ├── 13_concurrent_load.png
│   │   ├── 14_access_log.png
│   │   └── 15_status_dashboard.png
│   ├── NETWORK_PROJECT_REPORT.pdf # Final report PDF
│   └── reports.tex                # LaTeX source
├── webs/
│   ├── index.html                 # Homepage
│   ├── test.jpg                   # Test image (spotted dove)
│   └── test.txt                   # Test text file
├── Cell_tests.ipynb               # Jupyter notebook test suite
├── README.md                      # Project documentation
├── server.py                      # Main server implementation
└── status_dashboard.html          # Status dashboard preview
```

## 🔧 Configuration

Edit variables in `server.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `'127.0.0.1'` | Server listening address |
| `PORT` | `8848` | Server port number |
| `WEB_ROOT` | `'webs'` | Static file directory |
| `LOG_FILE` | `'logs/server.log'` | Log file path |
| `MAX_REQUEST_SIZE` | `65536` | Max request header size |
| `SOCKET_TIMEOUT` | `10` | Socket timeout in seconds |

## 📊 Log Format

Pipe-separated format for easy parsing:

```
127.0.0.1 | 2026-04-20 15:30:45 | GET /index.html | 200
127.0.0.1 | 2026-04-20 15:30:46 | HEAD /style.css | 200
127.0.0.1 | 2026-04-20 15:30:47 | GET /nonexistent.html | 404
127.0.0.1 | 2026-04-20 15:30:48 | GET /../server.py | 403
127.0.0.1 | 2026-04-20 15:30:49 | GET /index.html | 304
```

## 🧪 Complete Test Commands

### Basic Functionality

```bash
# 1. GET text file
curl -v http://127.0.0.1:8848/index.html

# 2. GET image file
curl -I http://127.0.0.1:8848/test.jpg

# 3. HEAD method
curl -I http://127.0.0.1:8848/index.html

# 4. 404 Not Found
curl http://127.0.0.1:8848/missing.html

# 5. 403 Forbidden (path traversal)
curl --path-as-is http://127.0.0.1:8848/../server.py

# 6. 400 Bad Request
python -c "import socket; s=socket.socket(); s.connect(('127.0.0.1',8848)); s.send(b'INVALID\r\n\r\n'); print(s.recv(1024))"
```

### Cache Validation

```bash
# Get Last-Modified timestamp
curl -v http://127.0.0.1:8848/index.html 2>&1 | grep -i "last-modified"

# Conditional request (use the timestamp from above)
curl -v --header "If-Modified-Since: Mon, 20 Apr 2026 14:50:23 GMT" http://127.0.0.1:8848/index.html
```

### Connection Management

```bash
# Keep-Alive test with telnet
telnet 127.0.0.1 8848
# Then paste:
GET /index.html HTTP/1.1
Host: 127.0.0.1
Connection: keep-alive

# After response, send second request:
GET /index.html HTTP/1.1
Host: 127.0.0.1
Connection: close
```

### Concurrent Load Test

```bash
# 10 simultaneous requests (Linux/Mac)
for i in {1..10}; do curl -s http://127.0.0.1:8848/index.html & done; wait

# Or use Python threading (see test.ipynb)
```

## 📈 Status Dashboard

The `/status` endpoint provides real-time monitoring:

| Metric | Description |
|--------|-------------|
| Server Uptime | Time since server started |
| Active Threads | Current worker thread count |
| Total Requests | Cumulative request count |
| Status Code Distribution | Breakdown by response code |
| Recent Logs | Last 10 log entries |

**Access:** `http://127.0.0.1:8848/status`

## 🔒 Security Features

| Feature | Implementation |
|---------|----------------|
| Path Traversal Protection | `os.path.commonpath()` validation against web root |
| URL Encoding Defense | `urllib.parse.unquote()` before path resolution |
| XSS Protection | `html.escape()` on all dynamic HTML content |
| Input Validation | Request line must have exactly 3 parts |
| Method Restriction | Only GET and HEAD allowed |
| Permission Checking | 403 on file read errors |

## 🛠️ Troubleshooting

### Port already in use
```bash
# Find and kill process on port 8848
lsof -ti :8848 | xargs kill -9
# Or change PORT in server.py
```

### curl normalizes ../ attacks
```bash
# Use --path-as-is to preserve raw path
curl --path-as-is http://127.0.0.1:8848/../server.py
```

### Log file not writing
```bash
# Ensure directory exists and is writable
mkdir -p logs
chmod 755 logs
```

## 📝 Code Structure

| Function | Purpose |
|----------|---------|
| `main()` | Server entry point, listening socket |
| `handle_client()` | Per-request handler (runs in thread) |
| `recv_http_request()` | Reads complete HTTP headers |
| `parse_headers()` | Extracts headers to dict |
| `should_keep_alive()` | Determines connection persistence |
| `resolve_file_path()` | Safe path resolution with traversal protection |
| `send_success_response()` | HTTP 200 with body |
| `send_head_response()` | HTTP 200 headers only |
| `send_304_response()` | HTTP 304 Not Modified |
| `send_error_response()` | HTTP error responses |
| `write_log()` | Thread-safe log append |
| `generate_status_page()` | Dynamic `/status` HTML |

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

## 🙏 Acknowledgments

- HTTP/1.1 Specification (RFC 2616)
- Python socket programming documentation
- email.utils for RFC-compliant date parsing

