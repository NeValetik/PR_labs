#!/usr/bin/env python3

import socket
import threading
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

def make_request(server_host, server_port, filename, request_id):
    """Make a single HTTP request and measure response time"""
    start_time = time.time()
    
    try:
        # Create a socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(10)  # 10 second timeout
        
        # Connect to the server
        client_socket.connect((server_host, server_port))
        
        # Send HTTP GET request
        request = f"GET /{filename} HTTP/1.1\r\nHost: {server_host}\r\n\r\n"
        client_socket.send(request.encode())
        
        # Receive and measure response
        response = b""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            response += data
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Check if request was successful
        success = response.startswith(b'HTTP/1.1 200') or response.startswith(b'HTTP/1.1 301')
        
        client_socket.close()
        
        return {
            'request_id': request_id,
            'success': success,
            'response_time': response_time,
            'response_size': len(response)
        }
        
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        return {
            'request_id': request_id,
            'success': False,
            'response_time': response_time,
            'error': str(e)
        }

def test_concurrent_requests(server_host, server_port, filename, num_requests=10):
    """Test concurrent requests and measure performance"""
    print(f"Testing {num_requests} concurrent requests to {server_host}:{server_port}/{filename}")
    print("=" * 60)
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor for concurrent requests
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        # Submit all requests
        futures = [
            executor.submit(make_request, server_host, server_port, filename, i+1)
            for i in range(num_requests)
        ]
        
        # Collect results
        results = []
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"Request {result['request_id']}: {'SUCCESS' if result['success'] else 'FAILED'} - {result['response_time']:.2f}s")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Calculate statistics
    successful_requests = [r for r in results if r['success']]
    failed_requests = [r for r in results if not r['success']]
    
    if successful_requests:
        avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)
        min_response_time = min(r['response_time'] for r in successful_requests)
        max_response_time = max(r['response_time'] for r in successful_requests)
    else:
        avg_response_time = min_response_time = max_response_time = 0
    
    print("\n" + "=" * 60)
    print("PERFORMANCE RESULTS:")
    print(f"Total requests: {num_requests}")
    print(f"Successful requests: {len(successful_requests)}")
    print(f"Failed requests: {len(failed_requests)}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average response time: {avg_response_time:.2f} seconds")
    print(f"Min response time: {min_response_time:.2f} seconds")
    print(f"Max response time: {max_response_time:.2f} seconds")
    print(f"Throughput: {len(successful_requests)/total_time:.2f} requests/second")
    
    if failed_requests:
        print("\nFAILED REQUESTS:")
        for req in failed_requests:
            error_msg = req.get('error', 'Unknown error')
            print(f"  Request {req['request_id']}: {error_msg}")
    
    return results

def test_rate_limiting(server_host, server_port, filename, num_requests=20, delay=0.1):
    """Test rate limiting by making rapid requests"""
    print(f"\nTesting rate limiting with {num_requests} rapid requests (delay: {delay}s)")
    print("=" * 60)
    
    results = []
    for i in range(num_requests):
        result = make_request(server_host, server_port, filename, i+1)
        results.append(result)
        
        status = "SUCCESS" if result['success'] else "FAILED/RATE LIMITED"
        print(f"Request {i+1}: {status} - {result['response_time']:.2f}s")
        
        time.sleep(delay)  # Small delay between requests
    
    # Analyze results
    successful = [r for r in results if r['success']]
    rate_limited = [r for r in results if not r['success']]
    
    print(f"\nRate Limiting Results:")
    print(f"Successful requests: {len(successful)}")
    print(f"Rate limited requests: {len(rate_limited)}")
    print(f"Rate limiting effectiveness: {len(rate_limited)/len(results)*100:.1f}%")

def main():
    if len(sys.argv) < 2:
        print("Usage: python concurrent_test.py <server_type> [host] [port] [filename]")
        print("  server_type: 'multithreaded' or 'single'")
        print("  host: server hostname (default: localhost)")
        print("  port: server port (default: 6789)")
        print("  filename: file to request (default: README.md)")
        sys.exit(1)
    
    server_type = sys.argv[1]
    server_host = sys.argv[2] if len(sys.argv) > 2 else 'localhost'
    server_port = int(sys.argv[3]) if len(sys.argv) > 3 else 6789
    filename = sys.argv[4] if len(sys.argv) > 4 else 'README.md'
    
    print(f"Testing {server_type} server at {server_host}:{server_port}")
    print(f"Requesting file: {filename}")
    
    # Test concurrent requests
    results = test_concurrent_requests(server_host, server_port, filename, 10)
    
    # Test rate limiting (only for multithreaded server)
    if server_type == 'multithreaded':
        test_rate_limiting(server_host, server_port, filename, 20, 0.1)

if __name__ == "__main__":
    main()
