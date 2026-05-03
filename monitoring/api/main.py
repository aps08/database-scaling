import asyncio
import logging
import os
import time
import random
import string

from fastapi import FastAPI, BackgroundTasks, Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
REQUEST_COUNT = Counter("aps08_api_requests_total", "Total API Requests", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("aps08_api_request_latency_seconds", "API Request Latency", ["endpoint"])
DB_INSERT_COUNT = Counter("aps08_db_inserts_total", "Total Database Inserts")
DB_QUERY_LATENCY = Histogram("aps08_db_query_latency_seconds", "Database Query Latency", ["query_type"])

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/aps08_monitoring_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserData(Base):
    __tablename__ = "user_data"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    payload = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="APS08 Database Scaling Monitor API")

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(latency)
    return response

@app.get("/users")
async def get_users(page: int = 1, limit: int = 10):
    start_time = time.time()
    db = SessionLocal()
    try:
        query = db.query(UserData)
        offset = (page - 1) * limit
        records = query.order_by(UserData.created_at.desc()).offset(offset).limit(limit).all()
        
        latency = time.time() - start_time
        DB_QUERY_LATENCY.labels(query_type="select_users").observe(latency)
        
        return [{"id": r.id, "username": r.username, "created_at": r.created_at} for r in records]
    finally:
        db.close()

@app.get("/user/{username}")
async def get_user_by_username(username: str):
    start_time = time.time()
    db = SessionLocal()
    try:
        user = db.query(UserData).filter(UserData.username == username).first()
        
        latency = time.time() - start_time
        DB_QUERY_LATENCY.labels(query_type="select_user_by_username").observe(latency)
        
        if user:
            return {"id": user.id, "username": user.username, "payload": user.payload, "created_at": user.created_at}
        return {"error": "User not found"}
    finally:
        db.close()

generating = False

async def generate_records():
    global generating
    logger.info("Starting data generation...")
    while generating:
        db = SessionLocal()
        try:
            for _ in range(10):
                uname = "".join(random.choices(string.ascii_lowercase, k=8))
                new_record = UserData(
                    username=uname,
                    payload="x" * 100
                )
                db.add(new_record)
            db.commit()
            DB_INSERT_COUNT.inc(10)
        except Exception as e:
            logger.error(f"Error inserting record: {e}")
            db.rollback()
        finally:
            db.close()
        await asyncio.sleep(1)

@app.post("/data/generate/start")
async def start_generation(background_tasks: BackgroundTasks):
    global generating
    if not generating:
        generating = True
        background_tasks.add_task(generate_records)
        return {"status": "started"}
    return {"status": "already running"}

@app.post("/data/generate/stop")
async def stop_generation():
    global generating
    generating = False
    return {"status": "stopped"}

@app.post("/index/create")
async def create_db_index():
    start_time = time.time()
    with engine.connect() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_data_username ON user_data (username)"))
        conn.commit()
    latency = time.time() - start_time
    return {"status": "index created", "duration": latency}

@app.get("/metrics")
def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/status")
def get_status():
    db = SessionLocal()
    try:
        count = db.query(UserData).count()
        result = db.execute(text("SELECT count(*) FROM pg_indexes WHERE tablename = 'user_data' AND indexname = 'idx_user_data_username'"))
        index_exists = result.scalar() > 0
        return {
            "total_records": count,
            "index_active": index_exists,
            "generating": generating
        }
    finally:
        db.close()
