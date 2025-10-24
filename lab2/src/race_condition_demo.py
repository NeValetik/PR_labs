#!/usr/bin/env python3

import socket
import threading
import time
import sys
from concurrent.futures import ThreadPoolExecutor

# Global counter without synchronization (naive implementation)
naive_counter = 0

def increment_naive_counter():
    """Increment counter without synchronization (demonstrates race condition)"""
    global naive_counter
    # Simulate some work
    time.sleep(0.001)  # Small delay to increase chance of race condition
    temp = naive_counter
    time.sleep(0.001)  # Another delay to force race condition
    naive_counter = temp + 1

def make_request_with_counter(server_host, server_port, filename, request_id):
    """Make request and demonstrate race condition in counter"""
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        client_socket.connect((server_host, server_port))
        
        request = f"GET /{filename} HTTP/1.1\r\nHost: {server_host}\r\n\r\n"
        client_socket.send(request.encode())
        
        # Increment naive counter (demonstrates race condition)
        increment_naive_counter()
        
        response = b""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            response += data
        
        client_socket.close()
        return True
        
    except Exception as e:
        print(f"Request {request_id} failed: {e}")
        return False

def demonstrate_race_condition(server_host, server_port, filename, num_requests=20):
    """Demonstrate race condition with concurrent requests"""
    print(f"Demonstrating race condition with {num_requests} concurrent requests")
    print("=" * 60)
    
    global naive_counter
    naive_counter = 0  # Reset counter
    
    start_time = time.time()
    
    # Make concurrent requests
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [
            executor.submit(make_request_with_counter, server_host, server_port, filename, i+1)
            for i in range(num_requests)
        ]
        
        # Wait for all requests to complete
        results = [future.result() for future in futures]
    
    end_time = time.time()
    total_time = end_time - start_time
    
    successful_requests = sum(results)
    
    print(f"\nRace Condition Results:")
    print(f"Expected counter value: {num_requests}")
    print(f"Actual counter value: {naive_counter}")
    print(f"Lost increments: {num_requests - naive_counter}")
    print(f"Successful requests: {successful_requests}")
    print(f"Total time: {total_time:.2f} seconds")
    
    if naive_counter < num_requests:
        print(f"\n RACE CONDITION DETECTED!")
        print(f"   Expected: {num_requests}, Got: {naive_counter}")
        print(f"   Lost {num_requests - naive_counter} increments due to race condition")
    else:
        print(f"\n No race condition detected (lucky timing)")

def main():
    if len(sys.argv) < 2:
        print("Usage: python race_condition_demo.py <server_host> [port] [filename]")
        print("  server_host: server hostname")
        print("  port: server port (default: 6789)")
        print("  filename: file to request (default: hello.html)")
        sys.exit(1)
    
    server_host = sys.argv[1]
    server_port = int(sys.argv[2]) if len(sys.argv) > 2 else 6789
    filename = sys.argv[3] if len(sys.argv) > 3 else 'hello.html'
    
    print(f"Race Condition Demonstration")
    print(f"Server: {server_host}:{server_port}")
    print(f"File: {filename}")
    
    # Run multiple tests to increase chance of seeing race condition
    for test_num in range(3):
        print(f"\n--- Test {test_num + 1} ---")
        demonstrate_race_condition(server_host, server_port, filename, 20)
        time.sleep(1)  # Brief pause between tests

if __name__ == "__main__":
    main()
