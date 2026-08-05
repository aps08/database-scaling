from fastapi import FastAPI, HTTPException
from typing import List

from src import crud, schemas

app = FastAPI(
    title="PostgreSQL Application-Level Database Sharding API",
    description="Scalable 4-node database sharding architecture with FastAPI & PostgreSQL",
    version="1.0.0",
)


@app.get("/")
def read_root():
    return {
        "message": "Application-Level Database Sharding API Running",
        "sharding_strategy": "Modulo Hash Routing (user_id % 4)",
    }


@app.post("/users", response_model=schemas.UserResponse, status_code=201)
def create_user(user: schemas.UserCreate):
    created_user, shard_id = crud.create_user(user)
    response = schemas.UserResponse.model_validate(created_user)
    response.target_shard = shard_id
    return response


@app.get("/users/scatter-gather", response_model=List[schemas.UserScatterGatherResponse])
def get_all_users_scatter_gather():
    """Scatter-Gather query querying ALL physical database shard nodes concurrently."""
    return crud.get_all_users_scatter_gather()


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int):
    """Direct O(1) single-node routing query targeting only the user's specific shard node."""
    user, shard_id = crud.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found on Shard {shard_id}")
    response = schemas.UserResponse.model_validate(user)
    response.target_shard = shard_id
    return response


@app.post("/orders", response_model=schemas.OrderResponse, status_code=201)
def create_order(order: schemas.OrderCreate):
    created_order, shard_id = crud.create_order(order)
    response = schemas.OrderResponse.model_validate(created_order)
    response.target_shard = shard_id
    return response


@app.get("/users/{user_id}/orders", response_model=List[schemas.OrderResponse])
def get_user_orders(user_id: int):
    orders, shard_id = crud.get_orders_by_user(user_id)
    responses = []
    for o in orders:
        resp = schemas.OrderResponse.model_validate(o)
        resp.target_shard = shard_id
        responses.append(resp)
    return responses
