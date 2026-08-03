from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import init_partitioned_tables
import src.crud as crud
import src.schemas as schemas

app = FastAPI(
    title="Database Partitioning Demo API",
    description="Demonstrates PostgreSQL Range, Hash, and List partitioning with Partition Pruning in FastAPI",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    try:
        init_partitioned_tables()
    except Exception as e:
        print(f"Database initialization deferred/failed: {e}")

@app.get("/")
def read_root():
    return {"message": "Database Partitioning FastAPI Demo"}

# --- RANGE PARTITIONING ENDPOINTS ---
@app.post("/orders/range", response_model=schemas.OrderResponse, tags=["Range Partitioning"])
def add_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    return crud.create_order(db, order)

@app.get("/orders/range/pruning-demo", tags=["Range Partitioning"])
def query_orders_with_pruning(start_date: str = "2026-08-01", end_date: str = "2026-08-31", db: Session = Depends(get_db)):
    """Demonstrates Partition Pruning by checking EXPLAIN ANALYZE output."""
    return crud.get_orders_by_date_range(db, start_date, end_date)

# --- HASH PARTITIONING ENDPOINTS ---
@app.post("/users/hash", tags=["Hash Partitioning"])
def add_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user_hash(db, user)

@app.get("/users/hash/{user_id}/pruning-demo", tags=["Hash Partitioning"])
def get_user_hash_pruning(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user_partition_info(db, user_id)

# --- LIST PARTITIONING ENDPOINTS ---
@app.post("/customers/list", response_model=schemas.CustomerResponse, tags=["List Partitioning"])
def add_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    if customer.region not in ["US", "CA", "EU", "UK", "IN", "JP", "SG"]:
        raise HTTPException(status_code=400, detail="Unsupported region for list partitioning")
    return crud.create_customer_list(db, customer)
