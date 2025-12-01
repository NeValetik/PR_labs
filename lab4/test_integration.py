"""
Integration test for the key-value store with single-leader replication.
"""
import pytest
import httpx
import asyncio
import time

LEADER_URL = "http://localhost:8000"
FOLLOWERS = [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003",
    "http://localhost:8004",
    "http://localhost:8005",
]


@pytest.mark.asyncio
async def test_leader_health():
    """Test that leader is healthy."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{LEADER_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["role"] == "leader"


@pytest.mark.asyncio
async def test_followers_health():
    """Test that all followers are healthy."""
    async with httpx.AsyncClient() as client:
        for follower_url in FOLLOWERS:
            response = await client.get(f"{follower_url}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["role"] == "follower"


@pytest.mark.asyncio
async def test_write_and_read():
    """Test writing to leader and reading from leader and followers."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Write to leader
        write_response = await client.post(
            f"{LEADER_URL}/keys",
            json={"key": "test_key_1", "value": "test_value_1"}
        )
        assert write_response.status_code == 200
        write_data = write_response.json()
        assert write_data["status"] == "success"
        assert write_data["key"] == "test_key_1"
        assert write_data["value"] == "test_value_1"
        
        # Wait a bit for replication
        await asyncio.sleep(2)
        
        # Read from leader
        read_response = await client.get(f"{LEADER_URL}/keys/test_key_1")
        assert read_response.status_code == 200
        read_data = read_response.json()
        assert read_data["key"] == "test_key_1"
        assert read_data["value"] == "test_value_1"
        
        # Read from all followers
        for follower_url in FOLLOWERS:
            read_response = await client.get(f"{follower_url}/keys/test_key_1")
            assert read_response.status_code == 200
            read_data = read_response.json()
            assert read_data["key"] == "test_key_1"
            assert read_data["value"] == "test_value_1"


@pytest.mark.asyncio
async def test_multiple_writes():
    """Test multiple writes and verify replication."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Write multiple keys
        test_data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
        }
        
        for key, value in test_data.items():
            write_response = await client.post(
                f"{LEADER_URL}/keys",
                json={"key": key, "value": value}
            )
            assert write_response.status_code == 200
        
        # Wait for replication
        await asyncio.sleep(3)
        
        # Verify all keys exist on leader
        for key, expected_value in test_data.items():
            read_response = await client.get(f"{LEADER_URL}/keys/{key}")
            assert read_response.status_code == 200
            assert read_response.json()["value"] == expected_value
        
        # Verify all keys exist on all followers
        for follower_url in FOLLOWERS:
            for key, expected_value in test_data.items():
                read_response = await client.get(f"{follower_url}/keys/{key}")
                assert read_response.status_code == 200
                assert read_response.json()["value"] == expected_value


@pytest.mark.asyncio
async def test_write_quorum():
    """Test that write quorum is respected."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Write a key
        write_response = await client.post(
            f"{LEADER_URL}/keys",
            json={"key": "quorum_test", "value": "quorum_value"}
        )
        assert write_response.status_code == 200
        write_data = write_response.json()
        
        # Check that replication count is reported
        assert "replicated_to" in write_data
        assert "write_quorum" in write_data
        assert write_data["replicated_to"] >= write_data["write_quorum"]


@pytest.mark.asyncio
async def test_read_nonexistent_key():
    """Test reading a non-existent key returns 404."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{LEADER_URL}/keys/nonexistent_key")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_state_consistency():
    """Test that leader and followers have consistent state after writes."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Write a few keys
        for i in range(5):
            await client.post(
                f"{LEADER_URL}/keys",
                json={"key": f"consistency_test_{i}", "value": f"value_{i}"}
            )
        
        # Wait for replication
        await asyncio.sleep(3)
        
        # Get state from leader
        leader_state_response = await client.get(f"{LEADER_URL}/state")
        assert leader_state_response.status_code == 200
        leader_store = leader_state_response.json()["store"]
        
        # Get state from all followers and compare
        for follower_url in FOLLOWERS:
            follower_state_response = await client.get(f"{follower_url}/state")
            assert follower_state_response.status_code == 200
            follower_store = follower_state_response.json()["store"]
            
            # Check that all keys from leader exist in follower
            for key, value in leader_store.items():
                assert key in follower_store, f"Key {key} missing in follower {follower_url}"
                assert follower_store[key] == value, f"Value mismatch for key {key} in follower {follower_url}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

