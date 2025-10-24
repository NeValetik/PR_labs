#import socket module
from socket import *
import sys # In order to terminate the program
import os
import mimetypes
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta

# Global variables for request counting and rate limiting
request_counters = defaultdict(int)  # File path -> count
request_counters_lock = threading.Lock()  # Lock for thread-safe access

# Rate limiting: IP -> list of request timestamps
client_requests = defaultdict(list)
rate_limit_lock = threading.Lock()
RATE_LIMIT = 5  # requests per second
RATE_WINDOW = 1  # time window in seconds

def is_allowed_file_type(filename):
    """Check if the file type is allowed (txt, png, html, md, pdf)"""
    allowed_extensions = {'.txt', '.png', '.html', '.md', '.pdf'}
    _, ext = os.path.splitext(filename.lower())
    return ext in allowed_extensions

def check_rate_limit(client_ip):
    """Check if client is within rate limit (thread-safe)"""
    current_time = time.time()
    
    with rate_limit_lock:
        # Clean old requests outside the time window
        client_requests[client_ip] = [
            req_time for req_time in client_requests[client_ip]
            if current_time - req_time < RATE_WINDOW
        ]
        
        # Check if under rate limit
        if len(client_requests[client_ip]) >= RATE_LIMIT:
            return False
        
        # Add current request
        client_requests[client_ip].append(current_time)
        return True

def generate_directory_listing(path, files, current_url):
    """Generate HTML directory listing with request counters"""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Directory listing for /{path}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin: 5px 0; }}
        a {{ text-decoration: none; color: #0066cc; }}
        a:hover {{ text-decoration: underline; }}
        .parent {{ font-weight: bold; color: #666; }}
        .counter {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>Directory listing for /{path}</h1>
    <ul>"""
    
    # Add parent directory link if not at root
    if path and path != '.':
        parent_url = '/'.join(current_url.rstrip('/').split('/')[:-1])
        if parent_url:
            parent_url += '/'
        else:
            parent_url = '/'
        html += f'<li><a href="{parent_url}" class="parent">.. (Parent Directory)</a></li>'
    
    # Sort files and directories
    files.sort()
    directories = []
    regular_files = []
    
    for file in files:
        if os.path.isdir(os.path.join(path, file)):
            directories.append(file)
        else:
            regular_files.append(file)
    
    # Add directories first
    for directory in directories:
        html += f'<li><a href="{current_url}{directory}/">{directory}/</a></li>'
    
    # Add files (only allowed file types) with request counters
    for file in regular_files:
        if is_allowed_file_type(file):
            file_path = f"{current_url}{file}".lstrip('/')
            with request_counters_lock:
                count = request_counters[file_path]
            html += f'<li><a href="{current_url}{file}">{file}</a> <span class="counter">({count} requests)</span></li>'
    
    html += """</ul>
</body>
</html>"""
    return html

def handle_request(connection_socket, addr):
    """Handle a single client request in a separate thread"""
    try:
        message = connection_socket.recv(1024).decode()
        print(f"Received request from {addr}: {message[:100]}...")
        
        # Extract client IP for rate limiting
        client_ip = addr[0]
        
        # Check rate limit
        if not check_rate_limit(client_ip):
            print(f"Rate limit exceeded for {client_ip}")
            connection_socket.sendall(b'HTTP/1.1 429 Too Many Requests\r\n\r\n')
            connection_socket.close()
            return
        
        filename = message.split()[1]
        print(f"Requested path: {filename}")
        
        # Remove leading slash and normalize path
        path = filename[1:] if filename.startswith('/') else filename
        
        # Security: Prevent directory traversal attacks
        if '..' in path or path.startswith('/'):
            connection_socket.sendall(b'HTTP/1.1 403 Forbidden\r\n\r\n')
            connection_socket.close()
            return
            
        # If path is empty, default to current directory
        if not path:
            path = '.'
        
        # Increment request counter (thread-safe)
        with request_counters_lock:
            request_counters[path] += 1
            print(f"Request counter for {path}: {request_counters[path]}")
        
        # Add delay to simulate work (~1s)
        time.sleep(1)
            
        # Handle directory requests
        if os.path.isdir(path):
            # If directory doesn't end with slash, redirect to add trailing slash
            if not filename.endswith('/'):
                redirect_url = filename + '/'
                response = f'HTTP/1.1 301 Moved Permanently\r\nLocation: {redirect_url}\r\n\r\n'
                connection_socket.sendall(response.encode())
                connection_socket.close()
                return
            
            # Generate directory listing
            try:
                files = os.listdir(path)
                html_content = generate_directory_listing(path, files, filename)
                send_response(connection_socket, html_content, 'text/html')
                print("Directory listing sent successfully")
            except PermissionError:
                connection_socket.sendall(b'HTTP/1.1 403 Forbidden\r\n\r\n')
                connection_socket.close()
                
        # Handle file requests
        elif os.path.isfile(path):
            # Check if file type is allowed
            if not is_allowed_file_type(path):
                connection_socket.sendall(b'HTTP/1.1 404 Not Found\r\n\r\n')
                connection_socket.close()
                return
                
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                
                # Determine content type
                content_type, _ = mimetypes.guess_type(path)
                if content_type is None:
                    content_type = 'application/octet-stream'
                
                send_response(connection_socket, content, content_type, is_binary=True)
                print("File sent successfully")
            except PermissionError:
                connection_socket.sendall(b'HTTP/1.1 403 Forbidden\r\n\r\n')
                connection_socket.close()
        else:
            connection_socket.sendall(b'HTTP/1.1 404 Not Found\r\n\r\n')
            connection_socket.close()

    except Exception as e:
        print(f"Error processing request from {addr}: {e}")
        try:
            connection_socket.sendall(b'HTTP/1.1 500 Internal Server Error\r\n\r\n')
        except:
            pass
        connection_socket.close()

def send_response(connection_socket, content, content_type, is_binary=False):
    """Send HTTP response with proper headers"""
    if is_binary:
        response = f'HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n'
        connection_socket.send(response.encode())
        connection_socket.send(content)
    else:
        response = f'HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n'
        connection_socket.send(response.encode())
        connection_socket.send(content.encode())
    connection_socket.close()

serverSocket = socket(AF_INET, SOCK_STREAM)
#Prepare a sever socket
#Fill in start
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
try:
    serverSocket.bind(('0.0.0.0', 6789))
    serverSocket.listen(1)
    print("Server started on http://0.0.0.0:6789")
    print("Accessible at http://localhost:6789")
except OSError as e:
    print(f"Error binding to port 6789: {e}")
    print("Trying alternative port 8080...")
    try:
        serverSocket.bind(('0.0.0.0', 8080))
        serverSocket.listen(1)
        print("Server started on http://0.0.0.0:8080")
        print("Accessible at http://localhost:8080")
    except OSError as e2:
        print(f"Error binding to port 8080: {e2}")
        sys.exit(1)
#Fill in end

print("Concurrent HTTP Server with Rate Limiting and Request Counters")
print("Rate limit: 5 requests/second per IP")
print("Request counters are thread-safe with locks")

while True:
    # Establish the connection
    print('Ready to serve...')
    connectionSocket, addr = serverSocket.accept()
    print(f"Connection from {addr}")
    
    # Create a new thread for each request
    client_thread = threading.Thread(
        target=handle_request,
        args=(connectionSocket, addr),
        daemon=True
    )
    client_thread.start()
    print(f"Started thread for client {addr}")

serverSocket.close()
sys.exit()#Terminate the program after sending the corresponding data