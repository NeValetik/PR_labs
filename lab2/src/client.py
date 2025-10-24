#!/usr/bin/env python3

import socket
import sys

def main():
    if len(sys.argv) != 4:
        print("Usage: client.py server_host server_port filename")
        print("Example: python client.py localhost 6789 HelloWorld.html")
        sys.exit(1)
    
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    filename = sys.argv[3]
    
    # Create a socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connect to the server
        client_socket.connect((server_host, server_port))
        
        # Send HTTP GET request
        request = f"GET /{filename} HTTP/1.1\r\nHost: {server_host}\r\n\r\n"
        client_socket.send(request.encode())
        
        # Receive and display the response
        response = b""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            response += data
        
        # Decode and print the response
        print(response.decode())
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
