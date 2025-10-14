#import socket module
from socket import *
import sys # In order to terminate the program
import os
import mimetypes

def is_allowed_file_type(filename):
    """Check if the file type is allowed (txt, png, html, md, pdf)"""
    allowed_extensions = {'.txt', '.png', '.html', '.md', '.pdf'}
    _, ext = os.path.splitext(filename.lower())
    return ext in allowed_extensions

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
            html += f'<li><a href="{current_url}{file}">{file}</a></li>'
    
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

while True:
    #Establish the connection
    print('Ready to serve...')
    connectionSocket, addr = serverSocket.accept()  #Fill in start #Fill in end
    print(f"Connection from {addr}")
    try:
        message = connectionSocket.recv(1024).decode()  #Fill in start #Fill in end
        print(f"Received request: {message[:100]}...")
        filename = message.split()[1]
        print(f"Requested path: {filename}")
        
        # Remove leading slash and normalize path
        path = filename[1:] if filename.startswith('/') else filename
        
        # Security: Prevent directory traversal attacks
        if '..' in path or path.startswith('/'):
            connectionSocket.sendall(b'HTTP/1.1 403 Forbidden\r\n\r\n')
            connectionSocket.close()
            continue
            
        # If path is empty, default to current directory
        if not path:
            path = '.'
            
        # Handle directory requests
        if os.path.isdir(path):
            # If directory doesn't end with slash, redirect to add trailing slash
            if not filename.endswith('/'):
                redirect_url = filename + '/'
                response = f'HTTP/1.1 301 Moved Permanently\r\nLocation: {redirect_url}\r\n\r\n'
                connectionSocket.sendall(response.encode())
                connectionSocket.close()
                continue
            
            # Generate directory listing
            try:
                files = os.listdir(path)
                html_content = generate_directory_listing(path, files, filename)
                send_response(connectionSocket, html_content, 'text/html')
                print("Directory listing sent successfully")
            except PermissionError:
                connectionSocket.sendall(b'HTTP/1.1 403 Forbidden\r\n\r\n')
                connectionSocket.close()
                
        # Handle file requests
        elif os.path.isfile(path):
            # Check if file type is allowed
            if not is_allowed_file_type(path):
                connectionSocket.sendall(b'HTTP/1.1 404 Not Found\r\n\r\n')
                connectionSocket.close()
                continue
                
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                
                # Determine content type
                content_type, _ = mimetypes.guess_type(path)
                if content_type is None:
                    content_type = 'application/octet-stream'
                
                send_response(connectionSocket, content, content_type, is_binary=True)
                print("File sent successfully")
            except PermissionError:
                connectionSocket.sendall(b'HTTP/1.1 403 Forbidden\r\n\r\n')
                connectionSocket.close()
        else:
            connectionSocket.sendall(b'HTTP/1.1 404 Not Found\r\n\r\n')
            connectionSocket.close()

    except Exception as e:
        print(f"Error processing request: {e}")
        connectionSocket.sendall(b'HTTP/1.1 500 Internal Server Error\r\n\r\n')
        connectionSocket.close()

serverSocket.close()
sys.exit()#Terminate the program after sending the corresponding data