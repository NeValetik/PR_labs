#!/usr/bin/env python3

import socket
import threading
import time
import sys

def make_request(host, port, filename, thread_id):
    """Make a single HTTP request and measure response time"""
    start_time = time.time()
    
    try:
        # Create a socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(10)  # 10 second timeout
        
        # Connect to the server
        client_socket.connect((host, port))
        
        # Send HTTP GET request
        request = f"GET /{filename} HTTP/1.1\r\nHost: {host}\r\n\r\n"
        client_socket.send(request.encode())
        
        # Receive the response
        response = b""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            response += data
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Check if request was successful
        response_str = response.decode()
        success = "200 OK" in response_str or "301 Moved Permanently" in response_str
        
        print(f"Thread {thread_id}: {'SUCCESS' if success else 'FAILED'} - {response_time:.2f}s")
        
        return success, response_time
        
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        print(f"Thread {thread_id}: ERROR - {e} - {response_time:.2f}s")
        return False, response_time
    finally:
        try:
            client_socket.close()
        except:
            pass

def test_concurrent_requests(host, port, filename, num_requests=10):
    """Test concurrent requests and measure total time"""
    print(f"Testing {num_requests} concurrent requests to {host}:{port}/{filename}")
    print("=" * 60)
    
    start_time = time.time()
    threads = []
    results = []
    
    # Create and start threads
    for i in range(num_requests):
        thread = threading.Thread(
            target=lambda i=i: results.append(make_request(host, port, filename, i+1))
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Calculate statistics
    successful_requests = sum(1 for success, _ in results if success)
    failed_requests = num_requests - successful_requests
    avg_response_time = sum(response_time for _, response_time in results) / len(results)
    
    print("=" * 60)
    print(f"RESULTS:")
    print(f"Total time: {total_time:.2f}s")
    print(f"Successful requests: {successful_requests}/{num_requests}")
    print(f"Failed requests: {failed_requests}")
    print(f"Average response time: {avg_response_time:.2f}s")
    print(f"Requests per second: {successful_requests/total_time:.2f}")
    
    return total_time, successful_requests, failed_requests

def test_rate_limiting(host, port, filename, requests_per_second=6):
    """Test rate limiting by sending requests faster than the limit"""
    print(f"\nTesting rate limiting with {requests_per_second} requests/second")
    print("=" * 60)
    
    start_time = time.time()
    threads = []
    results = []
    
    # Send requests at specified rate
    for i in range(requests_per_second):
        thread = threading.Thread(
            target=lambda i=i: results.append(make_request(host, port, filename, f"RL-{i+1}"))
        )
        threads.append(thread)
        thread.start()
        time.sleep(1.0 / requests_per_second)  # Control the rate
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    
    # Count successful vs rate-limited requests
    successful = sum(1 for success, _ in results if success)
    rate_limited = sum(1 for success, _ in results if not success)
    
    print("=" * 60)
    print(f"RATE LIMITING RESULTS:")
    print(f"Successful requests: {successful}")
    print(f"Rate limited requests: {rate_limited}")
    print(f"Rate limiting working: {'YES' if rate_limited > 0 else 'NO'}")

def main():
    if len(sys.argv) < 4:
        print("Usage: concurrent_test.py host port filename [num_requests]")
        print("Example: python concurrent_test.py localhost 6789 hello.html 10")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    filename = sys.argv[3]
    num_requests = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    
    print("Concurrent HTTP Server Test")
    print("=" * 60)
    
    # Test concurrent requests
    test_concurrent_requests(host, port, filename, num_requests)
    
    # Test rate limiting
    test_rate_limiting(host, port, filename, 6)  # 6 requests/second (above 5 req/s limit)
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()
