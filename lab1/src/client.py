#!/usr/bin/env python3

import socket
import sys
import os
import re

def parse_http_response(response_data):
    """Parse HTTP response and return headers and body"""
    try:
        # Split headers and body
        header_end = response_data.find(b'\r\n\r\n')
        if header_end == -1:
            return None, response_data
        
        headers_raw = response_data[:header_end]
        body = response_data[header_end + 4:]
        
        # Parse headers
        headers = {}
        header_lines = headers_raw.decode('utf-8', errors='ignore').split('\r\n')
        
        for line in header_lines[1:]:  # Skip status line
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()
        
        return headers, body
    except Exception as e:
        print(f"Error parsing response: {e}")
        return None, response_data

def save_file(filename, content, directory="."):
    """Save file content to specified directory"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Get just the filename from the path
        base_filename = os.path.basename(filename)
        file_path = os.path.join(directory, base_filename)
        
        # Write the file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        print(f"File saved: {file_path}")
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False

def main():
    if len(sys.argv) != 4:
        print("Usage: client.py server_host server_port filename")
        print("Example: python client.py localhost 6789 index.html")
        print("Example: python client.py localhost 6789 image.png")
        print("Example: python client.py localhost 6789 document.pdf")
        sys.exit(1)
    
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    filename = sys.argv[3]
    
    # Create a socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connect to the server
        print(f"Connecting to {server_host}:{server_port}")
        client_socket.connect((server_host, server_port))
        
        # Send HTTP GET request
        request = f"GET /{filename} HTTP/1.1\r\nHost: {server_host}\r\nConnection: close\r\n\r\n"
        client_socket.send(request.encode())
        print(f"Request sent: GET /{filename}")
        
        # Receive the response
        response = b""
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            response += data
        
        # Parse the response
        headers, body = parse_http_response(response)
        
        if headers is None:
            print("Failed to parse HTTP response")
            print("Raw response:")
            print(response.decode('utf-8', errors='ignore'))
            return
        
        # Check status code
        status_line = response.decode('utf-8', errors='ignore').split('\r\n')[0]
        print(f"Response: {status_line}")
        
        if "200 OK" in status_line:
            # Determine file type and handle accordingly
            content_type = headers.get('content-type', '').lower()
            file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
            
            print(f"Content-Type: {content_type}")
            print(f"Content-Length: {len(body)}")
            
            if content_type.startswith('text/html') or file_extension == 'html':
                # HTML file - display the content
                print("\n" + "="*50)
                print("HTML CONTENT:")
                print("="*50)
                print(body.decode('utf-8', errors='ignore'))
                print("="*50)
                
            elif content_type.startswith('image/') or file_extension in ['png', 'jpg', 'jpeg', 'gif']:
                # Image file - save it
                print(f"\nSaving image file: {filename}")
                save_file(filename, body, "downloads")
                
            elif content_type == 'application/pdf' or file_extension == 'pdf':
                # PDF file - save it
                print(f"\nSaving PDF file: {filename}")
                save_file(filename, body, "downloads")
                
            else:
                # Unknown file type - save it anyway
                print(f"\nSaving file: {filename}")
                save_file(filename, body, "downloads")
        
        elif "404" in status_line:
            print("File not found (404)")
            print("Response body:")
            print(body.decode('utf-8', errors='ignore'))
            
        else:
            print(f"Server returned: {status_line}")
            print("Response body:")
            print(body.decode('utf-8', errors='ignore'))
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
