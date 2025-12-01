# Lab 4: Key-Value Store with Single-Leader Replication

This lab implements a key-value store with single-leader replication using FastAPI, following the design patterns described in "Designing Data-Intensive Applications" by Martin Kleppmann.

## Features

- **Single-Leader Replication**: Only the leader accepts writes, replicates to followers
- **Semi-Synchronous Replication**: Leader waits for configurable write quorum before confirming writes
- **Concurrent Execution**: Both leader and followers handle requests concurrently
- **Network Lag Simulation**: Random delays (0-1000ms) before replicating to followers
- **Docker Compose**: Easy deployment with 1 leader and 5 followers

## Architecture

- **Leader**: Accepts writes, replicates to followers, waits for quorum
- **Followers**: Accept replication requests, serve read requests
- **Communication**: REST API with JSON over HTTP

## Setup

### Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for running tests locally)

### Running the System

1. Build and start all containers:
```bash
docker-compose up --build
```

2. The system will be available at:
   - Leader: http://localhost:8000
   - Followers: http://localhost:8001-8005

### Configuration

Edit `docker-compose.yml` to configure:

- `WRITE_QUORUM`: Number of follower confirmations required (default: 3)
- `MIN_DELAY_MS`: Minimum network delay in milliseconds (default: 0)
- `MAX_DELAY_MS`: Maximum network delay in milliseconds (default: 1000)

## API Endpoints

### Leader Endpoints

- `GET /` - Get leader info
- `GET /health` - Health check
- `GET /keys` - List all keys
- `GET /keys/{key}` - Read a value
- `POST /keys` - Write a key-value pair (requires quorum)
- `GET /state` - Get current store state

### Follower Endpoints

- `GET /` - Get follower info
- `GET /health` - Health check
- `GET /keys` - List all keys
- `GET /keys/{key}` - Read a value
- `POST /replicate` - Accept replication from leader (internal)
- `GET /state` - Get current store state

### Example Usage

```bash
# Write a key-value pair
curl -X POST http://localhost:8000/keys \
  -H "Content-Type: application/json" \
  -d '{"key": "test_key", "value": "test_value"}'

# Read from leader
curl http://localhost:8000/keys/test_key

# Read from follower
curl http://localhost:8001/keys/test_key
```

## Testing

### Integration Tests

Run the integration tests:

```bash
# Make sure containers are running
docker-compose up -d

# Run tests
pytest test_integration.py -v
```

### Performance Analysis

Run the performance analysis script:

```bash
# Make sure containers are running
docker-compose up -d

# Run performance analysis
python performance_analysis.py
```

**Note**: The script will prompt you to update `WRITE_QUORUM` in `docker-compose.yml` and restart the leader for each quorum value (1-5). You can automate this or do it manually:

```bash
# For each quorum value (1-5), update docker-compose.yml and run:
docker-compose restart leader
```

The script will:
1. Perform ~100 writes (10 concurrent batches) on 10 keys
2. Measure average latency for each quorum value
3. Generate a plot: `quorum_vs_latency.png`
4. Verify data consistency across all replicas

## Expected Results

### Write Quorum vs Latency

As the write quorum increases:
- **Latency increases** because the leader must wait for more follower confirmations
- With random network delays (0-1000ms), higher quorum means waiting for slower followers
- Since replication is concurrent, latency ≈ time for Nth fastest confirmation (N = quorum)

### Consistency

After all writes complete:
- All followers should eventually have the same data as the leader (eventual consistency)
- Some followers might temporarily be missing keys if replication is still in progress
- Given enough time, all replicas should converge to the same state

## Project Structure

```
lab4/
├── leader.py              # Leader server implementation
├── follower.py            # Follower server implementation
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile             # Docker image definition
├── requirements.txt       # Python dependencies
├── test_integration.py    # Integration tests
├── performance_analysis.py # Performance analysis script
└── README.md             # This file
```

## Implementation Details

### Semi-Synchronous Replication

The leader implements semi-synchronous replication:
1. Write is persisted locally on the leader immediately
2. Replication requests are sent to all followers concurrently
3. Each replication has a random delay (MIN_DELAY_MS to MAX_DELAY_MS)
4. Leader waits for WRITE_QUORUM confirmations before returning success
5. If quorum is not met, write is still persisted but error is returned

### Concurrency

- Leader uses FastAPI's async capabilities for concurrent replication
- Followers use FastAPI for concurrent request handling
- All replication requests are sent in parallel using `asyncio.gather()`

## Troubleshooting

- **Port conflicts**: Change ports in `docker-compose.yml` if 8000-8005 are in use
- **Connection errors**: Ensure all containers are running: `docker-compose ps`
- **Quorum not met**: Check follower logs: `docker-compose logs follower1`
- **Consistency issues**: Wait longer for replication to complete (network delays)

## References

- Chapter 5, Section 1 "Leaders and Followers" from "Designing Data-Intensive Applications" by Martin Kleppmann
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Docker Compose Documentation: https://docs.docker.com/compose/

