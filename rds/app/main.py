import os
import uuid
import shutil
import asyncio
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/postgres")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    name = Column(String)
    bio = Column(Text)
    large_payload = Column(Text, nullable=True)
    raw_data = Column(Text, nullable=True)
    sessions = relationship("UserSession", back_populates="user")

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_token = Column(String)
    device_info = Column(String)
    user = relationship("User", back_populates="sessions")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="APS08 RDS Scaling Simulator")

def generate_garbage_data(size_kb: float = 10.0):
    return "X" * int(size_kb * 1024)

def data_filler_task():
    while True:
        db = SessionLocal()
        try:
            batch_size = 500
            users = []
            for _ in range(batch_size):
                username = f"u_{uuid.uuid4().hex[:10]}"
                users.append(User(
                    name=f"Bulk User {username}",
                    username=username,
                    bio="Automated bulk record.",
                    large_payload=generate_garbage_data(1.0),
                    raw_data=generate_garbage_data(1.0)
                ))
            db.add_all(users)
            db.flush()
            
            sessions = []
            for user in users:
                sessions.append(UserSession(
                    user_id=user.id,
                    session_token=uuid.uuid4().hex,
                    device_info="Bulk-Worker"
                ))
            db.add_all(sessions)
            db.commit()
            print(f"[{datetime.now()}] [APS08] SUCCESS: Bulk inserted {batch_size} users and sessions")
        except Exception as e:
            db.rollback()
            print(f"[{datetime.now()}] ERROR: Filler task failed: {e}")
        finally:
            db.close()

@app.post("/start-filling")
async def start_filling(background_tasks: BackgroundTasks):
    background_tasks.add_task(data_filler_task)
    return {"status": "Data filler started in background"}

@app.get("/stats")
async def get_stats():
    try:
        total, used, free = shutil.disk_usage("/mnt/wsl/aps08_rds_sim")
        return {
            "total_mb": round(total / (1024 * 1024), 2),
            "used_mb": round(used / (1024 * 1024), 2),
            "free_mb": round(free / (1024 * 1024), 2),
            "percent_used": round((used / total) * 100, 2) if total > 0 else 0
        }
    except Exception as e:
        return {"error": str(e)}
