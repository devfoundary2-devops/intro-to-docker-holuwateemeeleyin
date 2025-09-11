from fastapi import FastAPI, HTTPException
import redis
import os
import databases
import sqlalchemy



# Environment variables
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://demo:password@db:5432/demo")


# Set up async PostgreSQL connection using `databases`
# PostgreSQL setup
database = databases.Database(POSTGRES_URL)
metadata = sqlalchemy.MetaData()
engine = sqlalchemy.create_engine(POSTGRES_URL)
metadata.create_all(engine)


# Initialize Redis connection
# We wrap this in a try/except to avoid crashing the app if Redis isn't available
# decode_responses=True makes Redis return strings instead of bytes
# Redis setup
try:
    r = redis.Redis(host="redis", port=6379, decode_responses=True)
    r.ping()
except redis.exceptions.ConnectionError:
    r = None # fallback: Redis is not available

app = FastAPI()

# Connect to the PostgreSQL database on app startup
@app.on_event("startup")
async def startup():
    await database.connect()

# Disconnect from the PostgreSQL database on shutdown
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/cache/{key}")
def cache_get(key: str):
    if not r:
        raise HTTPException(status_code=500, detail="Redis not available")
    val = r.get(key)
    if val is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"key": key, "value": val}


@app.post("/cache/{key}/{value}")
def cache_set(key: str, value: str):
    if not r:
        raise HTTPException(status_code=500, detail="Redis not available")
    r.set(key, value)
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Hello from Bootcamp Day 3"}
