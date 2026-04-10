import socket

def main():
    # 服务器配置
    host = '127.0.0.1'  # 本地回环地址
    port = 8080         # 使用非80端口，避免冲突

    # 创建 TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # 允许端口重用（方便调试，避免 Address already in use 错误）
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # 绑定地址和端口
    server_socket.bind((host, port))
    
    # 开始监听，最大等待连接数设为5
    server_socket.listen(5)
    
    print(f"服务器已启动: http://{host}:{port}")
    print("等待客户端连接...\n")

    while True:
        # 接受客户端连接
        client_socket, client_addr = server_socket.accept()
        print(f"[新连接] 来自: {client_addr}")
        
        # 接收 HTTP 请求（最多接收 4096 字节）
        request_data = client_socket.recv(4096).decode('utf-8', errors='ignore')
        
        # 打印请求内容（便于调试）
        print(f"[请求内容]\n{request_data}")
        print("-" * 50)
        
        # 临时响应：固定返回 Hello World
        response_body = "<h1>Hello World</h1><p>Your Web server is running!</p>"
        response_headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            f"Content-Length: {len(response_body)}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        
        # 发送响应
        client_socket.send(response_headers.encode() + response_body.encode())
        
        # 关闭连接
        client_socket.close()
        print(f"[关闭连接] {client_addr}\n")

if __name__ == "__main__":
    main()
