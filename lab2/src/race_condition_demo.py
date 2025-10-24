#!/usr/bin/env python3

import threading
import time
from collections import defaultdict

# Global counter without synchronization (demonstrates race condition)
unsafe_counter = 0
unsafe_counters = defaultdict(int)

# Global counter with synchronization (fixes race condition)
safe_counter = 0
safe_counters = defaultdict(int)
safe_lock = threading.Lock()

def unsafe_increment_counter(file_path):
    """Increment counter without synchronization (race condition)"""
    global unsafe_counter, unsafe_counters
    
    # Simulate some work
    time.sleep(0.001)
    
    # This is NOT thread-safe - race condition occurs here
    unsafe_counter += 1
    unsafe_counters[file_path] += 1
    
    print(f"Unsafe: Counter={unsafe_counter}, {file_path}={unsafe_counters[file_path]}")

def safe_increment_counter(file_path):
    """Increment counter with synchronization (no race condition)"""
    global safe_counter, safe_counters
    
    # Simulate some work
    time.sleep(0.001)
    
    # This IS thread-safe - uses lock to prevent race condition
    with safe_lock:
        safe_counter += 1
        safe_counters[file_path] += 1
        print(f"Safe: Counter={safe_counter}, {file_path}={safe_counters[file_path]}")

def demonstrate_race_condition():
    """Demonstrate race condition with unsafe counter"""
    print("=" * 60)
    print("DEMONSTRATING RACE CONDITION (UNSAFE COUNTER)")
    print("=" * 60)
    
    global unsafe_counter, unsafe_counters
    unsafe_counter = 0
    unsafe_counters.clear()
    
    threads = []
    num_threads = 10
    requests_per_thread = 5
    
    start_time = time.time()
    
    # Create threads that increment unsafe counter
    for i in range(num_threads):
        for j in range(requests_per_thread):
            thread = threading.Thread(
                target=unsafe_increment_counter,
                args=(f"file_{i}.html",)
            )
            threads.append(thread)
            thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    
    print(f"\nUnsafe Counter Results:")
    print(f"Expected total: {num_threads * requests_per_thread}")
    print(f"Actual total: {unsafe_counter}")
    print(f"Race condition occurred: {'YES' if unsafe_counter != num_threads * requests_per_thread else 'NO'}")
    print(f"Time taken: {end_time - start_time:.3f}s")
    
    return unsafe_counter

def demonstrate_safe_counter():
    """Demonstrate safe counter with synchronization"""
    print("\n" + "=" * 60)
    print("DEMONSTRATING THREAD-SAFE COUNTER (WITH LOCKS)")
    print("=" * 60)
    
    global safe_counter, safe_counters
    safe_counter = 0
    safe_counters.clear()
    
    threads = []
    num_threads = 10
    requests_per_thread = 5
    
    start_time = time.time()
    
    # Create threads that increment safe counter
    for i in range(num_threads):
        for j in range(requests_per_thread):
            thread = threading.Thread(
                target=safe_increment_counter,
                args=(f"file_{i}.html",)
            )
            threads.append(thread)
            thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    
    print(f"\nSafe Counter Results:")
    print(f"Expected total: {num_threads * requests_per_thread}")
    print(f"Actual total: {safe_counter}")
    print(f"Race condition occurred: {'YES' if safe_counter != num_threads * requests_per_thread else 'NO'}")
    print(f"Time taken: {end_time - start_time:.3f}s")
    
    return safe_counter

def main():
    print("Race Condition Demonstration")
    print("This script demonstrates the difference between unsafe and safe counter implementations")
    print("in a multi-threaded environment.")
    
    # Run multiple iterations to increase chance of seeing race condition
    for iteration in range(3):
        print(f"\n{'='*80}")
        print(f"ITERATION {iteration + 1}")
        print(f"{'='*80}")
        
        unsafe_result = demonstrate_race_condition()
        safe_result = demonstrate_safe_counter()
        
        print(f"\nComparison for iteration {iteration + 1}:")
        print(f"Unsafe counter: {unsafe_result}")
        print(f"Safe counter: {safe_result}")
        print(f"Difference: {abs(unsafe_result - safe_result)}")
    
    print(f"\n{'='*80}")
    print("CONCLUSION:")
    print("- Unsafe counter may show race conditions (lost updates)")
    print("- Safe counter with locks prevents race conditions")
    print("- Locks ensure atomic operations but may reduce performance")
    print("- This is why the HTTP server uses locks for request counters")

if __name__ == "__main__":
    main()
