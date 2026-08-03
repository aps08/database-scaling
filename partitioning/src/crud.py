from sqlalchemy.orm import Session
from sqlalchemy import text
from src.schemas import OrderCreate, UserCreate, CustomerCreate

def create_order(db: Session, order: OrderCreate):
    query = text("""
        INSERT INTO orders_range (order_date, customer_id, amount)
        VALUES (:order_date, :customer_id, :amount)
        RETURNING id, order_date, customer_id, amount;
    """)
    result = db.execute(query, {
        "order_date": order.order_date,
        "customer_id": order.customer_id,
        "amount": order.amount
    })
    db.commit()
    row = result.fetchone()
    return {"id": row[0], "order_date": row[1], "customer_id": row[2], "amount": float(row[3])}

def get_orders_by_date_range(db: Session, start_date: str, end_date: str):
    query = text("""
        EXPLAIN ANALYZE
        SELECT * FROM orders_range
        WHERE order_date BETWEEN :start_date AND :end_date;
    """)
    explain_res = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
    
    data_query = text("""
        SELECT id, order_date, customer_id, amount FROM orders_range
        WHERE order_date BETWEEN :start_date AND :end_date;
    """)
    data_res = db.execute(data_query, {"start_date": start_date, "end_date": end_date}).fetchall()
    
    return {
        "execution_plan": [row[0] for row in explain_res],
        "results": [{"id": r[0], "order_date": str(r[1]), "customer_id": r[2], "amount": float(r[3])} for r in data_res]
    }

def create_user_hash(db: Session, user: UserCreate):
    query = text("""
        INSERT INTO users_hash (user_id, username, email)
        VALUES (:user_id, :username, :email)
        RETURNING user_id, username, email;
    """)
    result = db.execute(query, {"user_id": user.user_id, "username": user.username, "email": user.email})
    db.commit()
    row = result.fetchone()
    return {"user_id": row[0], "username": row[1], "email": row[2]}

def get_user_partition_info(db: Session, user_id: int):
    query = text("""
        EXPLAIN ANALYZE
        SELECT * FROM users_hash WHERE user_id = :user_id;
    """)
    explain_res = db.execute(query, {"user_id": user_id}).fetchall()
    return {"execution_plan": [row[0] for row in explain_res]}

def create_customer_list(db: Session, customer: CustomerCreate):
    query = text("""
        INSERT INTO customers_list (name, region)
        VALUES (:name, :region)
        RETURNING id, name, region;
    """)
    result = db.execute(query, {"name": customer.name, "region": customer.region})
    db.commit()
    row = result.fetchone()
    return {"id": row[0], "name": row[1], "region": row[2]}
