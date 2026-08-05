from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from src.database import get_shard_id, get_db_session, get_all_db_sessions
from src.models import User, Order
from src.schemas import UserCreate, OrderCreate


def create_user(user_data: UserCreate) -> Tuple[User, int]:
    shard_id = get_shard_id(user_data.id)
    db: Session = get_db_session(shard_id)
    try:
        user = User(
            id=user_data.id,
            name=user_data.name,
            email=user_data.email,
            country=user_data.country,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, shard_id
    finally:
        db.close()


def get_user_by_id(user_id: int) -> Tuple[Optional[User], int]:
    shard_id = get_shard_id(user_id)
    db: Session = get_db_session(shard_id)
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user, shard_id
    finally:
        db.close()


def create_order(order_data: OrderCreate) -> Tuple[Order, int]:
    shard_id = get_shard_id(order_data.user_id)
    db: Session = get_db_session(shard_id)
    try:
        order = Order(
            user_id=order_data.user_id,
            amount=order_data.amount,
            status=order_data.status,
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order, shard_id
    finally:
        db.close()


def get_orders_by_user(user_id: int) -> Tuple[List[Order], int]:
    shard_id = get_shard_id(user_id)
    db: Session = get_db_session(shard_id)
    try:
        orders = db.query(Order).filter(Order.user_id == user_id).all()
        return orders, shard_id
    finally:
        db.close()


def get_all_users_scatter_gather() -> List[dict]:
    aggregated_users = []
    shard_sessions = get_all_db_sessions()
    for shard_id, db in shard_sessions:
        try:
            users = db.query(User).all()
            for user in users:
                aggregated_users.append(
                    {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "country": user.country,
                        "located_on_shard": shard_id,
                    }
                )
        finally:
            db.close()
    return aggregated_users
