#!/usr/bin/env python3

import socket
import threading
import time
import sys
from concurrent.futures import ThreadPoolExecutor
import random

def make_request(server_host, server_port, filename, client_id, request_id):
    """Make a single HTTP request"""
    start_time = time.time()
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        client_socket.connect((server_host, server_port))
        
        request = f"GET /{filename} HTTP/1.1\r\nHost: {server_host}\r\n\r\n"
        client_socket.send(request.encode())
        
        response = b""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            response += data
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Check response status
        if response.startswith(b'HTTP/1.1 200') or response.startswith(b'HTTP/1.1 301'):
            status = "SUCCESS"
        elif response.startswith(b'HTTP/1.1 429'):
            status = "RATE_LIMITED"
        else:
            status = "ERROR"
        
        client_socket.close()
        
        return {
            'client_id': client_id,
            'request_id': request_id,
            'status': status,
            'response_time': response_time,
            'timestamp': start_time
        }
        
    except Exception as e:
        end_time = time.time()
        return {
            'client_id': client_id,
            'request_id': request_id,
            'status': 'ERROR',
            'response_time': end_time - start_time,
            'error': str(e),
            'timestamp': start_time
        }

def spam_client(server_host, server_port, filename, client_id, num_requests, delay=0.0):
    """Simulate a spam client making rapid requests"""
    print(f"Spam client {client_id} starting with {num_requests} requests (delay: {delay}s)")
    
    results = []
    for i in range(num_requests):
        result = make_request(server_host, server_port, filename, client_id, i+1)
        results.append(result)
        
        status_emoji = "✅" if result['status'] == 'SUCCESS' else "🚫" if result['status'] == 'RATE_LIMITED' else "❌"
        print(f"  {status_emoji} Client {client_id} Request {i+1}: {result['status']} ({result['response_time']:.2f}s)")
        
        if delay > 0:
            time.sleep(delay)
    
    return results

def normal_client(server_host, server_port, filename, client_id, num_requests, delay=0.3):
    """Simulate a normal client making requests within rate limit"""
    print(f"Normal client {client_id} starting with {num_requests} requests (delay: {delay}s)")
    
    results = []
    for i in range(num_requests):
        result = make_request(server_host, server_port, filename, client_id, i+1)
        results.append(result)
        
        status_emoji = "✅" if result['status'] == 'SUCCESS' else "🚫" if result['status'] == 'RATE_LIMITED' else "❌"
        print(f"  {status_emoji} Client {client_id} Request {i+1}: {result['status']} ({result['response_time']:.2f}s)")
        
        time.sleep(delay)
    
    return results

def burst_client(server_host, server_port, filename, client_id, num_requests):
    """Simulate a burst client making requests with no delay"""
    print(f"Burst client {client_id} starting with {num_requests} requests (no delay)")
    
    results = []
    for i in range(num_requests):
        result = make_request(server_host, server_port, filename, client_id, i+1)
        results.append(result)
        
        status_emoji = "✅" if result['status'] == 'SUCCESS' else "🚫" if result['status'] == 'RATE_LIMITED' else "❌"
        print(f"  {status_emoji} Client {client_id} Request {i+1}: {result['status']} ({result['response_time']:.2f}s)")
    
    return results

def concurrent_spam_client(server_host, server_port, filename, client_id, num_requests):
    """Simulate a spam client making truly concurrent requests"""
    print(f"Concurrent spam client {client_id} starting with {num_requests} requests (truly concurrent)")
    
    # Create all requests concurrently
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = []
        for i in range(num_requests):
            future = executor.submit(make_request, server_host, server_port, filename, client_id, i+1)
            futures.append(future)
        
        results = []
        for i, future in enumerate(futures):
            result = future.result()
            results.append(result)
            
            status_emoji = "✅" if result['status'] == 'SUCCESS' else "🚫" if result['status'] == 'RATE_LIMITED' else "❌"
            print(f"  {status_emoji} Client {client_id} Request {i+1}: {result['status']} ({result['response_time']:.2f}s)")
    
    return results

def test_rate_limiting_scenarios(server_host, server_port, filename):
    """Test different rate limiting scenarios"""
    print("Rate Limiting Test Scenarios")
    print("=" * 60)
    
    # Scenario 0: Burst client (no delay)
    print("\n--- Scenario 0: Burst Client (No Delay) ---")
    burst_results = burst_client(server_host, server_port, filename, "BURST", 25)
    
    burst_success = len([r for r in burst_results if r['status'] == 'SUCCESS'])
    burst_rate_limited = len([r for r in burst_results if r['status'] == 'RATE_LIMITED'])
    burst_errors = len([r for r in burst_results if r['status'] == 'ERROR'])
    
    print(f"\nBurst Client Results:")
    print(f"  Total requests: {len(burst_results)}")
    print(f"  Successful: {burst_success}")
    print(f"  Rate limited: {burst_rate_limited}")
    print(f"  Errors: {burst_errors}")
    print(f"  Success rate: {burst_success/len(burst_results)*100:.1f}%")
    
    # Scenario 1: Spam client vs Normal client
    print("\n--- Scenario 1: Spam Client vs Normal Client ---")
    
    # Start both clients concurrently
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Spam client (rapid requests - no delay)
        spam_future = executor.submit(spam_client, server_host, server_port, filename, "SPAM", 30, 0.0)
        
        # Normal client (within rate limit)
        normal_future = executor.submit(normal_client, server_host, server_port, filename, "NORMAL", 20, 0.3)
        
        # Wait for both to complete
        spam_results = spam_future.result()
        normal_results = normal_future.result()
    
    # Analyze results
    spam_success = len([r for r in spam_results if r['status'] == 'SUCCESS'])
    spam_rate_limited = len([r for r in spam_results if r['status'] == 'RATE_LIMITED'])
    spam_errors = len([r for r in spam_results if r['status'] == 'ERROR'])
    
    normal_success = len([r for r in normal_results if r['status'] == 'SUCCESS'])
    normal_rate_limited = len([r for r in normal_results if r['status'] == 'RATE_LIMITED'])
    normal_errors = len([r for r in normal_results if r['status'] == 'ERROR'])
    
    print(f"\n--- Results Summary ---")
    print(f"Spam Client:")
    print(f"  Total requests: {len(spam_results)}")
    print(f"  Successful: {spam_success}")
    print(f"  Rate limited: {spam_rate_limited}")
    print(f"  Errors: {spam_errors}")
    print(f"  Success rate: {spam_success/len(spam_results)*100:.1f}%")
    
    print(f"\nNormal Client:")
    print(f"  Total requests: {len(normal_results)}")
    print(f"  Successful: {normal_success}")
    print(f"  Rate limited: {normal_rate_limited}")
    print(f"  Errors: {normal_errors}")
    print(f"  Success rate: {normal_success/len(normal_results)*100:.1f}%")
    
    # Scenario 2: Multiple spam clients
    print(f"\n--- Scenario 2: Multiple Spam Clients ---")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(5):
            future = executor.submit(spam_client, server_host, server_port, filename, f"SPAM{i+1}", 15, 0.0)
            futures.append(future)
        
        all_results = []
        for future in futures:
            all_results.extend(future.result())
    
    total_requests = len(all_results)
    total_success = len([r for r in all_results if r['status'] == 'SUCCESS'])
    total_rate_limited = len([r for r in all_results if r['status'] == 'RATE_LIMITED'])
    
    print(f"\nMultiple Spam Clients Results:")
    print(f"  Total requests: {total_requests}")
    print(f"  Successful: {total_success}")
    print(f"  Rate limited: {total_rate_limited}")
    print(f"  Success rate: {total_success/total_requests*100:.1f}%")
    
    # Calculate throughput
    if total_requests > 0:
        # Estimate time window (assuming requests were made over ~10 seconds)
        time_window = 10
        throughput = total_success / time_window
        print(f"  Throughput: {throughput:.2f} successful requests/second")
    
    # Scenario 3: Extreme stress test
    print(f"\n--- Scenario 3: Extreme Stress Test ---")
    print("Testing with very high request volume to demonstrate rate limiting...")
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for i in range(8):
            future = executor.submit(spam_client, server_host, server_port, filename, f"STRESS{i+1}", 25, 0.0)
            futures.append(future)
        
        stress_results = []
        for future in futures:
            stress_results.extend(future.result())
    
    stress_total = len(stress_results)
    stress_success = len([r for r in stress_results if r['status'] == 'SUCCESS'])
    stress_rate_limited = len([r for r in stress_results if r['status'] == 'RATE_LIMITED'])
    stress_errors = len([r for r in stress_results if r['status'] == 'ERROR'])
    
    print(f"\nExtreme Stress Test Results:")
    print(f"  Total requests: {stress_total}")
    print(f"  Successful: {stress_success}")
    print(f"  Rate limited: {stress_rate_limited}")
    print(f"  Errors: {stress_errors}")
    print(f"  Success rate: {stress_success/stress_total*100:.1f}%")
    print(f"  Rate limiting effectiveness: {stress_rate_limited/stress_total*100:.1f}%")
    
    # Scenario 4: Truly concurrent requests (no delays at all)
    print(f"\n--- Scenario 4: Truly Concurrent Requests ---")
    print("Testing with truly concurrent requests (all at once) to maximize rate limiting...")
    
    concurrent_results = concurrent_spam_client(server_host, server_port, filename, "CONCURRENT", 20)
    
    concurrent_total = len(concurrent_results)
    concurrent_success = len([r for r in concurrent_results if r['status'] == 'SUCCESS'])
    concurrent_rate_limited = len([r for r in concurrent_results if r['status'] == 'RATE_LIMITED'])
    concurrent_errors = len([r for r in concurrent_results if r['status'] == 'ERROR'])
    
    print(f"\nTruly Concurrent Results:")
    print(f"  Total requests: {concurrent_total}")
    print(f"  Successful: {concurrent_success}")
    print(f"  Rate limited: {concurrent_rate_limited}")
    print(f"  Errors: {concurrent_errors}")
    print(f"  Success rate: {concurrent_success/concurrent_total*100:.1f}%")
    print(f"  Rate limiting effectiveness: {concurrent_rate_limited/concurrent_total*100:.1f}%")

def main():
    if len(sys.argv) < 2:
        print("Usage: python rate_limit_test.py <server_host> [port] [filename]")
        print("  server_host: server hostname")
        print("  port: server port (default: 6789)")
        print("  filename: file to request (default: hello.html)")
        sys.exit(1)
    
    server_host = sys.argv[1]
    server_port = int(sys.argv[2]) if len(sys.argv) > 2 else 6789
    filename = sys.argv[3] if len(sys.argv) > 3 else 'hello.html'
    
    print(f"Rate Limiting Test")
    print(f"Server: {server_host}:{server_port}")
    print(f"File: {filename}")
    print(f"Rate limit: 5 requests/second per IP")
    
    test_rate_limiting_scenarios(server_host, server_port, filename)

if __name__ == "__main__":
    main()
