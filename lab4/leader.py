"""
Leader server for key-value store with single-leader replication.
Only the leader accepts writes and replicates them to followers.
"""
import os
import asyncio
import time
from typing import Dict, List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

shared_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global shared_client
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=100)
    shared_client = httpx.AsyncClient(
        timeout=10.0,
        limits=limits,
        http2=False
    )
    yield
    if shared_client:
        await shared_client.aclose()


app = FastAPI(lifespan=lifespan)

store: Dict[str, str] = {}
store_lock = asyncio.Lock()

FOLLOWERS = os.getenv("FOLLOWERS", "").split(",")
FOLLOWERS = [f.strip() for f in FOLLOWERS if f.strip()]
WRITE_QUORUM = int(os.getenv("WRITE_QUORUM", "3"))
MIN_DELAY_MS = int(os.getenv("MIN_DELAY_MS", "0"))
MAX_DELAY_MS = int(os.getenv("MAX_DELAY_MS", "1000"))
LEADER_PORT = int(os.getenv("LEADER_PORT", "8000"))

print(f"Leader initialized with {len(FOLLOWERS)} followers: {FOLLOWERS}")
print(f"Write quorum: {WRITE_QUORUM}, Delay range: [{MIN_DELAY_MS}ms, {MAX_DELAY_MS}ms]")


class WriteRequest(BaseModel):
    key: str
    value: str


class ReplicateRequest(BaseModel):
    key: str
    value: str


class QuorumUpdateRequest(BaseModel):
    quorum: int


@app.get("/")
async def root():
    return {"role": "leader", "followers": FOLLOWERS, "write_quorum": WRITE_QUORUM}


@app.get("/health")
async def health():
    return {"status": "healthy", "role": "leader"}


@app.get("/keys/{key}")
async def read(key: str):
    async with store_lock:
        if key in store:
            return {"key": key, "value": store[key]}
    raise HTTPException(status_code=404, detail="Key not found")


@app.get("/keys")
async def list_keys():
    return {"keys": list(store.keys())}


@app.post("/keys")
async def write(request: WriteRequest):
    start_time = time.time()
    
    async with store_lock:
        store[request.key] = request.value
    
    async def replicate_to_follower(follower_url: str) -> bool:
        try:
            if shared_client is None:
                raise RuntimeError("Shared HTTP client not initialized")
            response = await shared_client.post(
                f"{follower_url}/replicate",
                json={"key": request.key, "value": request.value}
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Error replicating to {follower_url}: {e}")
            return False
    
    replication_tasks = [asyncio.create_task(replicate_to_follower(follower)) 
                         for follower in FOLLOWERS]
    
    successful_count = 0
    pending_tasks = set(replication_tasks)
    
    # Wait for quorum by processing tasks as they complete
    while successful_count < WRITE_QUORUM and pending_tasks:
        done, pending_tasks = await asyncio.wait(
            pending_tasks,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        for task in done:
            try:
                if task.result() is True:
                    successful_count += 1
                    if successful_count >= WRITE_QUORUM:
                        # Cancel remaining tasks to avoid unnecessary work
                        for remaining_task in pending_tasks:
                            remaining_task.cancel()
                        break
            except Exception as e:
                pass
        
        if successful_count >= WRITE_QUORUM:
            break
    
    total_successful = successful_count
    
    latency = time.time() - start_time
    
    if total_successful >= WRITE_QUORUM:
        return {
            "status": "success",
            "key": request.key,
            "value": request.value,
            "replicated_to": total_successful,
            "total_followers": len(FOLLOWERS),
            "write_quorum": WRITE_QUORUM,
            "latency_seconds": latency
        }
    else:
        raise HTTPException(
            status_code=503,
            detail=f"Write quorum not met. Got {total_successful}/{WRITE_QUORUM} confirmations. "
                   f"Write persisted on leader but replication incomplete."
        )


@app.get("/state")
async def get_state():
    return {"store": store, "keys_count": len(store)}


@app.post("/config/quorum")
async def update_quorum(request: QuorumUpdateRequest):
    global WRITE_QUORUM
    if request.quorum < 1 or request.quorum > len(FOLLOWERS):
        raise HTTPException(
            status_code=400,
            detail=f"Quorum must be between 1 and {len(FOLLOWERS)}"
        )
    old_quorum = WRITE_QUORUM
    WRITE_QUORUM = request.quorum
    return {
        "status": "updated",
        "old_quorum": old_quorum,
        "new_quorum": WRITE_QUORUM,
        "total_followers": len(FOLLOWERS)
    }


@app.get("/config/quorum")
async def get_quorum():
    return {"quorum": WRITE_QUORUM, "total_followers": len(FOLLOWERS)}


if __name__ == "__main__":
    import uvicorn
    workers = int(os.getenv("WORKERS", "10"))
    uvicorn.run("leader:app", host="0.0.0.0", port=LEADER_PORT, workers=workers)

