import os
import uuid
import random
from typing import Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio

app = FastAPI()

store: Dict[str, str] = {}
store_lock = asyncio.Lock()

FOLLOWER_PORT = int(os.getenv("FOLLOWER_PORT", "8001"))
FOLLOWER_ID = os.getenv("FOLLOWER_ID", "follower1")
MIN_DELAY_MS = int(os.getenv("MIN_DELAY_MS", "0"))
MAX_DELAY_MS = int(os.getenv("MAX_DELAY_MS", "1000"))

print(f"Follower {FOLLOWER_ID} initialized on port {FOLLOWER_PORT}")
print(f"Delay range: [{MIN_DELAY_MS}ms, {MAX_DELAY_MS}ms]")

class ReplicateRequest(BaseModel):
    key: str
    value: str

@app.get("/")
async def root():
    return {"role": "follower", "id": FOLLOWER_ID}


@app.get("/health")
async def health():
    return {"status": "healthy", "role": "follower", "id": FOLLOWER_ID}


@app.get("/keys/{key}")
async def read(key: str):
    async with store_lock:
        if key in store:
            return {"key": key, "value": store[key]}
        else:
            raise HTTPException(status_code=404, detail="Key not found")


@app.get("/keys")
async def list_keys():
    return {"keys": list(store.keys())}


@app.post("/replicate")
async def replicate(request: ReplicateRequest):
    delay_ms = random.uniform(MIN_DELAY_MS, MAX_DELAY_MS)
    delay_seconds = delay_ms / 1000.0
    await asyncio.sleep(delay_seconds)
    
    async with store_lock:
        store[request.key] = request.value
    return {"status": "replicated"}


@app.get("/state")
async def get_state():
    return {"store": store, "keys_count": len(store), "follower_id": FOLLOWER_ID}


if __name__ == "__main__":
    import uvicorn
    import os
    workers = int(os.getenv("WORKERS", "10"))

    uvicorn.run("follower:app", host="0.0.0.0", port=FOLLOWER_PORT, workers=workers, loop="asyncio")

