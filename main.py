from fastapi import FastAPI
import redis
from fastapi.responses import JSONResponse
from datetime import datetime
import time
import os
from dotenv import load_dotenv

load_dotenv() 

app = FastAPI()


# Redis connection (cloud Redis)
r = redis.Redis(
     host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT",0)),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
)


# Rate limiter function
def rate_limiter(api_key: str) -> str:
    key = f"rate:{api_key}"
    try:
        # Increment request count
        count = r.incr(key, 1)
        r.expire(key, 60)
        
        # Record request with timestamp
        ts = int(time.time())
        request_key = f"requests:{api_key}:{ts}"
        r.set(request_key, 1, ex=60)  # old method if needed

        # ✅ Add to sorted set for fast dashboard retrieval
        r.zadd("recent_requests", {api_key + f":{ts}": ts})
        r.zremrangebyscore("recent_requests", 0, ts-60)  # keep only last 60 sec

        # Determine status
        if count <= 5:
            return "allowed"
        elif count <= 10:
            return "throttled"
        else:
            # Include API key in violation
            r.lpush("violations", f"{api_key}:blocked at {ts}")
            r.expire("violations", 3600)
            return "blocked"
    except redis.exceptions.ConnectionError:
        return "redis_error"


# API endpoint
@app.get("/api")
async def api_endpoint(api_key: str):
    status = rate_limiter(api_key)
    
    if status == "allowed":
        return JSONResponse(content={"status": "allowed", "message": "Request successful."})
    elif status == "throttled":
        return JSONResponse(content={"status": "throttled", "message": "Too many requests. Slow down."})
    elif status == "blocked":
        return JSONResponse(content={"status": "blocked", "message": "You are blocked due to excessive requests."})
    elif status == "redis_error":
        return JSONResponse(content={"status": "error", "message": "Cannot connect to Redis."}, status_code=500)
    else:
        return JSONResponse(content={"status": "error", "message": "Unknown error."}, status_code=500)
