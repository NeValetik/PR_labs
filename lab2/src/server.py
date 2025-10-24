#import socket module
from socket import *
import sys # In order to terminate the program
import os
import mimetypes
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
import queue

# Global variables for thread-safe operations
request_counters = defaultdict(int)  # Track requests per file
counter_lock = threading.Lock()  # Lock for counter operations
rate_limit_data = defaultdict(list)  # Track request timestamps per IP
rate_limit_lock = threading.Lock()  # Lock for rate limiting
RATE_LIMIT_REQUESTS = 5  # Max requests per second
RATE_LIMIT_WINDOW = 1  # Time window in seconds

def is_allowed_file_type(filename):
    """Check if the file type is allowed (txt, png, html, md, pdf)"""
    allowed_extensions = {'.txt', '.png', '.html', '.md', '.pdf'}
    _, ext = os.path.splitext(filename.lower())
    return ext in allowed_extensions

def check_rate_limit(client_ip):
    """Check if client IP is within rate limit (thread-safe)"""
    current_time = time.time()
    
    with rate_limit_lock:
        # Clean old timestamps (older than RATE_LIMIT_WINDOW seconds)
        rate_limit_data[client_ip] = [
            timestamp for timestamp in rate_limit_data[client_ip]
            if current_time - timestamp < RATE_LIMIT_WINDOW
        ]
        
        # Check if under rate limit
        if len(rate_limit_data[client_ip]) < RATE_LIMIT_REQUESTS:
            rate_limit_data[client_ip].append(current_time)
            return True
        else:
            return False

def increment_counter(filename):
    """Increment request counter for a file (thread-safe)"""
    with counter_lock:
        request_counters[filename] += 1
        return request_counters[filename]

def generate_directory_listing(path, files, current_url):
    """Generate HTML directory listing"""
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
    
    # Add files (only allowed file types)
    for file in regular_files:
        if is_allowed_file_type(file):
            # Get request count for this file
            with counter_lock:
                count = request_counters.get(f"/{file}", 0)
            html += f'<li><a href="{current_url}{file}">{file}</a> <span style="color: #666; font-size: 0.9em;">({count} requests)</span></li>'
    
    html += """</ul>
</body>
</html>"""
    return html

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

def handle_request(connection_socket, addr):
    """Handle a single client request (thread-safe)"""
    client_ip = addr[0]
    
    try:
        # Check rate limiting
        if not check_rate_limit(client_ip):
            print(f"Rate limit exceeded for {client_ip}")
            connection_socket.sendall(b'HTTP/1.1 429 Too Many Requests\r\n\r\n')
            connection_socket.close()
            return
        
        message = connection_socket.recv(1024).decode()
        print(f"Received request from {client_ip}: {message[:100]}...")
        filename = message.split()[1]
        print(f"Requested path: {filename}")
        
        # Add 1 second delay to simulate work
        time.sleep(1)
        
        # Increment counter for this request
        increment_counter(filename)
        
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
        print(f"Error processing request from {client_ip}: {e}")
        connection_socket.sendall(b'HTTP/1.1 500 Internal Server Error\r\n\r\n')
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

print("Multithreaded server ready to serve...")
print("Features: Request counters, Rate limiting (5 req/sec), 1s delay simulation")

while True:
    #Establish the connection
    print('Ready to serve...')
    connectionSocket, addr = serverSocket.accept()  #Fill in start #Fill in end
    print(f"Connection from {addr}")
    
    # Create a new thread to handle the request
    thread = threading.Thread(target=handle_request, args=(connectionSocket, addr))
    thread.daemon = True  # Allow main thread to exit even if threads are running
    thread.start()

serverSocket.close()
sys.exit()#Terminate the program after sending the corresponding data