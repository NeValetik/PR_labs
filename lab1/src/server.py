import socket
import sys
import os
import mimetypes
from urllib.parse import unquote

def get_mime_type(filename):
    """Get MIME type for a file"""
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        return mime_type
    elif filename.lower().endswith('.pdf'):
        return 'application/pdf'
    elif filename.lower().endswith('.png'):
        return 'image/png'
    elif filename.lower().endswith('.html'):
        return 'text/html'
    else:
        return 'application/octet-stream'

def generate_directory_listing(directory_path, request_path):
    """Generate HTML directory listing"""
    try:
        items = os.listdir(directory_path)
        items.sort()
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Directory listing for {request_path}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin: 10px 0; }}
        a {{ text-decoration: none; color: #0066cc; }}
        a:hover {{ text-decoration: underline; }}
        .directory {{ font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Directory listing for {request_path}</h1>
    <ul>"""
        
        # Add parent directory link if not at root
        if request_path != '/':
            parent_path = '/'.join(request_path.rstrip('/').split('/')[:-1]) or '/'
            html += f'        <li><a href="{parent_path}">.. (Parent Directory)</a></li>\n'
        
        for item in items:
            item_path = os.path.join(directory_path, item)
            if os.path.isdir(item_path):
                html += f'        <li class="directory"><a href="{request_path.rstrip("/")}/{item}/">{item}/</a></li>\n'
            else:
                html += f'        <li><a href="{request_path.rstrip("/")}/{item}">{item}</a></li>\n'
        
        html += """    </ul>
</body>
</html>"""
        return html
    except Exception as e:
        return f"<html><body><h1>Error listing directory</h1><p>{str(e)}</p></body></html>"

def main():
    if len(sys.argv) != 2:
        print("Usage: python server.py <directory>")
        print("Example: python server.py ./content")
        sys.exit(1)
    
    serve_directory = sys.argv[1]
    
    if not os.path.isdir(serve_directory):
        print(f"Error: Directory '{serve_directory}' does not exist")
        sys.exit(1)
    
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        serverSocket.bind(('0.0.0.0', 6789))
        serverSocket.listen(1)
        print(f"Server started on http://0.0.0.0:6789")
        print(f"Serving directory: {os.path.abspath(serve_directory)}")
        print("Try: http://localhost:6789/")
    except OSError as e:
        print(f"Error binding to port 6789: {e}")
        print("Trying alternative port 8080...")
        try:
            serverSocket.bind(('0.0.0.0', 8080))
            serverSocket.listen(1)
            print(f"Server started on http://0.0.0.0:8080")
            print(f"Serving directory: {os.path.abspath(serve_directory)}")
            print("Try: http://localhost:8080/")
        except OSError as e2:
            print(f"Error binding to port 8080: {e2}")
            sys.exit(1)

    while True:
        # Establish the connection
        print('Ready to serve...')
        connectionSocket, addr = serverSocket.accept()
        print(f"Connection from {addr}")
        
        try:
            message = connectionSocket.recv(1024).decode()
            print(f"Received request: {message[:100]}...")
            
            # Parse the request
            request_lines = message.split('\n')
            if not request_lines:
                connectionSocket.close()
                continue
                
            request_line = request_lines[0]
            parts = request_line.split()
            if len(parts) < 2:
                connectionSocket.close()
                continue
                
            method = parts[0]
            path = unquote(parts[1])  # URL decode the path
            
            print(f"Requested path: {path}")
            
            # Handle directory requests
            if path.endswith('/') or path == '/':
                if path == '/':
                    target_path = serve_directory
                    request_path = '/'
                else:
                    target_path = os.path.join(serve_directory, path[1:])
                    request_path = path
                
                if os.path.isdir(target_path):
                    # Generate directory listing
                    directory_html = generate_directory_listing(target_path, request_path)
                    response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {len(directory_html)}\r\n\r\n{directory_html}"
                    connectionSocket.send(response.encode())
                    print("Directory listing sent successfully")
                else:
                    # Directory not found
                    error_html = "<html><body><h1>404 Not Found</h1><p>Directory not found</p></body></html>"
                    response = f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\nContent-Length: {len(error_html)}\r\n\r\n{error_html}"
                    connectionSocket.send(response.encode())
                    print("Directory not found - 404 sent")
            else:
                # Handle file requests
                file_path = os.path.join(serve_directory, path[1:])
                
                if os.path.isfile(file_path):
                    # File exists, serve it
                    mime_type = get_mime_type(file_path)
                    
                    # Read file content
                    if mime_type.startswith('text/') or mime_type == 'application/pdf':
                        # Text files and PDFs - read as text
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        response = f"HTTP/1.1 200 OK\r\nContent-Type: {mime_type}\r\nContent-Length: {len(content.encode('utf-8'))}\r\n\r\n{content}"
                        connectionSocket.send(response.encode())
                    else:
                        # Binary files - read as binary
                        with open(file_path, 'rb') as f:
                            content = f.read()
                        response = f"HTTP/1.1 200 OK\r\nContent-Type: {mime_type}\r\nContent-Length: {len(content)}\r\n\r\n"
                        connectionSocket.send(response.encode())
                        connectionSocket.send(content)
                    
                    print(f"File sent successfully: {file_path}")
                else:
                    # File not found
                    error_html = "<html><body><h1>404 Not Found</h1><p>File not found</p></body></html>"
                    response = f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\nContent-Length: {len(error_html)}\r\n\r\n{error_html}"
                    connectionSocket.send(response.encode())
                    print(f"File not found - 404 sent: {file_path}")
            
            connectionSocket.close()
            
        except Exception as e:
            print(f"Error handling request: {e}")
            try:
                error_html = "<html><body><h1>500 Internal Server Error</h1><p>Server error occurred</p></body></html>"
                response = f"HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\nContent-Length: {len(error_html)}\r\n\r\n{error_html}"
                connectionSocket.send(response.encode())
            except:
                pass
            connectionSocket.close()

    serverSocket.close()
    sys.exit()

if __name__ == "__main__":
    main()