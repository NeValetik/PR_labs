"""
Performance analysis script for the key-value store.
Tests write performance with different write quorum values.
"""
import asyncio
import httpx
import time
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict

LEADER_URL = "http://localhost:8000"
FOLLOWERS = [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003",
    "http://localhost:8004",
    "http://localhost:8005",
]

NUM_WRITES = 100
NUM_WORKERS = 10  # Number of concurrent workers
NUM_KEYS = 10
QUORUM_VALUES = [1, 2, 3, 4, 5]


async def write_key(client: httpx.AsyncClient, key: str, value: str):
    start_time = time.time()
    try:
        response = await client.post(
            f"{LEADER_URL}/keys",
            json={"key": key, "value": value},
            timeout=15.0
        )
        latency = time.time() - start_time
        success = response.status_code == 200
        return latency, success
    except Exception as e:
        latency = time.time() - start_time
        return latency, False


async def test_quorum(quorum: int) -> Dict:
    print(f"\nTesting with write quorum = {quorum}")
    print(f"Using {NUM_WORKERS} concurrent workers")
    
    limits = httpx.Limits(max_keepalive_connections=NUM_WORKERS * 2, max_connections=100)
    async with httpx.AsyncClient(timeout=15.0, limits=limits) as client:
        latencies = []
        successes = []
        
        test_data = [
            (f"perf_key_{i % NUM_KEYS}", f"value_{i}_{quorum}_{time.time()}")
            for i in range(NUM_WRITES)
        ]
        
        semaphore = asyncio.Semaphore(NUM_WORKERS)
        
        async def write_with_semaphore(key: str, value: str):
            async with semaphore:
                return await write_key(client, key, value)
        
        tasks = [write_with_semaphore(key, value) for key, value in test_data]
        
        results = await asyncio.gather(*tasks)
        
        for latency, success in results:
            latencies.append(latency)
            successes.append(success)
        
        latencies_array = np.array(latencies) if latencies else np.array([])
        avg_latency = np.mean(latencies_array) if len(latencies_array) > 0 else 0
        median_latency = np.median(latencies_array) if len(latencies_array) > 0 else 0
        p95_latency = np.percentile(latencies_array, 95) if len(latencies_array) > 0 else 0
        p99_latency = np.percentile(latencies_array, 99) if len(latencies_array) > 0 else 0
        success_rate = sum(successes) / len(successes) if successes else 0
        
        print(f"  Average latency: {avg_latency:.4f} seconds")
        print(f"  Median latency: {median_latency:.4f} seconds")
        print(f"  P95 latency: {p95_latency:.4f} seconds")
        print(f"  P99 latency: {p99_latency:.4f} seconds")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Total writes: {len(successes)}")
        
        return {
            "quorum": quorum,
            "avg_latency": avg_latency,
            "median_latency": median_latency,
            "p95_latency": p95_latency,
            "p99_latency": p99_latency,
            "latencies": latencies,
            "success_rate": success_rate,
            "test_data": test_data
        }


async def verify_consistency(test_data: List[tuple]) -> Dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        leader_response = await client.get(f"{LEADER_URL}/state")
        leader_store = leader_response.json()["store"]
        
        consistency_results = {}
        
        for follower_url in FOLLOWERS:
            follower_response = await client.get(f"{follower_url}/state")
            follower_store = follower_response.json()["store"]
            
            missing_keys = []
            mismatched_values = []
            
            for key, expected_value in test_data:
                if key not in follower_store:
                    missing_keys.append(key)
                elif follower_store[key] != expected_value:
                    mismatched_values.append((key, expected_value, follower_store[key]))
            
            consistency_results[follower_url] = {
                "missing_keys": len(missing_keys),
                "mismatched_values": len(mismatched_values),
                "total_keys_in_leader": len(leader_store),
                "total_keys_in_follower": len(follower_store),
                "missing_keys_list": missing_keys[:10],  # First 10 for debugging
                "mismatched_list": mismatched_values[:10]  # First 10 for debugging
            }
        
        return consistency_results


async def main():
    """Main function to run performance analysis."""
    print("=" * 60)
    print("Performance Analysis: Write Quorum vs Latency")
    print("=" * 60)
    print(f"Total writes: {NUM_WRITES}")
    print(f"Concurrent batch size: {NUM_WORKERS}")
    print(f"Number of keys: {NUM_KEYS}")
    print(f"Quorum values to test: {QUORUM_VALUES}")
    print("\nNOTE: This script assumes docker-compose is running.")
    print("Quorum will be updated via API endpoint (no docker-compose modification needed)")
    print("=" * 60)
    
    results = []
    
    for quorum in QUORUM_VALUES:
        print(f"\n{'='*60}")
        print(f"Testing with WRITE_QUORUM={quorum}")
        print(f"{'='*60}")
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                health_response = await client.get(f"{LEADER_URL}/health")
                if health_response.status_code != 200:
                    print(f"ERROR: Leader not healthy. Skipping quorum {quorum}")
                    continue
                
                quorum_response = await client.post(
                    f"{LEADER_URL}/config/quorum",
                    json={"quorum": quorum}
                )
                if quorum_response.status_code == 200:
                    quorum_data = quorum_response.json()
                    print(f"Updated quorum: {quorum_data['old_quorum']} -> {quorum_data['new_quorum']}")
                else:
                    print(f"ERROR: Failed to update quorum: {quorum_response.status_code}")
                    continue
        except Exception as e:
            print(f"ERROR: Cannot connect to leader: {e}. Skipping quorum {quorum}")
            continue
        
        result = await test_quorum(quorum)
        results.append(result)
        
        print("\nVerifying consistency...")
        consistency = await verify_consistency(result["test_data"])
        for follower_url, stats in consistency.items():
            print(f"  {follower_url}:")
            print(f"    Missing keys: {stats['missing_keys']}")
            print(f"    Mismatched values: {stats['mismatched_values']}")
            print(f"    Leader keys: {stats['total_keys_in_leader']}, Follower keys: {stats['total_keys_in_follower']}")
    
    quorums = [r["quorum"] for r in results]
    avg_latencies = [r["avg_latency"] for r in results]
    median_latencies = [r["median_latency"] for r in results]
    p95_latencies = [r["p95_latency"] for r in results]
    p99_latencies = [r["p99_latency"] for r in results]
    
    plt.figure(figsize=(12, 7))
    
    plt.plot(quorums, avg_latencies, marker='o', linewidth=2, markersize=8, 
             label='Average', color='blue')
    plt.plot(quorums, median_latencies, marker='s', linewidth=2, markersize=8, 
             label='Median', color='green')
    plt.plot(quorums, p95_latencies, marker='^', linewidth=2, markersize=8, 
             label='P95', color='orange')
    plt.plot(quorums, p99_latencies, marker='d', linewidth=2, markersize=8, 
             label='P99', color='red')
    
    plt.xlabel('Write Quorum', fontsize=12)
    plt.ylabel('Latency (seconds)', fontsize=12)
    plt.title('Write Quorum vs Latency Metrics\n(100 writes, 10 concurrent batches, 10 keys)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.xticks(quorums)
    plt.legend(loc='best', fontsize=10)
    
    for i, (q, lat) in enumerate(zip(quorums, avg_latencies)):
        plt.annotate(f'{lat:.3f}s', (q, lat), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=8, color='blue')
    
    plt.tight_layout()
    plt.savefig('quorum_vs_latency.png', dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to quorum_vs_latency.png")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"{'Quorum':<8} {'Average':<10} {'Median':<10} {'P95':<10} {'P99':<10} {'Success Rate':<12}")
    print("-" * 60)
    for r in results:
        print(f"{r['quorum']:<8} {r['avg_latency']:<10.4f} {r['median_latency']:<10.4f} "
              f"{r['p95_latency']:<10.4f} {r['p99_latency']:<10.4f} {r['success_rate']:<12.2%}")
    

if __name__ == "__main__":
    asyncio.run(main())

