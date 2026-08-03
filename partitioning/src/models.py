from sqlalchemy import text
from src.database import engine

def init_partitioned_tables():
    """Initializes Range, Hash, and List partitioned tables in PostgreSQL."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders_range (
                id SERIAL,
                order_date DATE NOT NULL,
                customer_id INT NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                PRIMARY KEY (id, order_date)
            ) PARTITION BY RANGE (order_date);
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders_2026_06 PARTITION OF orders_range
            FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders_2026_07 PARTITION OF orders_range
            FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders_2026_08 PARTITION OF orders_range
            FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users_hash (
                user_id INT NOT NULL,
                username VARCHAR(50) NOT NULL,
                email VARCHAR(100) NOT NULL,
                PRIMARY KEY (user_id)
            ) PARTITION BY HASH (user_id);
        """))
        
        for i in range(4):
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS users_hash_p{i} PARTITION OF users_hash
                FOR VALUES WITH (MODULUS 4, REMAINDER {i});
            """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customers_list (
                id SERIAL,
                name VARCHAR(100) NOT NULL,
                region VARCHAR(10) NOT NULL,
                PRIMARY KEY (id, region)
            ) PARTITION BY LIST (region);
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customers_us PARTITION OF customers_list
            FOR VALUES IN ('US', 'CA');
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customers_eu PARTITION OF customers_list
            FOR VALUES IN ('EU', 'UK');
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customers_asia PARTITION OF customers_list
            FOR VALUES IN ('IN', 'JP', 'SG');
        """))

        # Seed initial sample records into Range Partitioned Table
        conn.execute(text("""
            INSERT INTO orders_range (order_date, customer_id, amount)
            SELECT '2026-06-15', 101, 150.00
            WHERE NOT EXISTS (SELECT 1 FROM orders_range WHERE customer_id = 101 AND order_date = '2026-06-15');
            
            INSERT INTO orders_range (order_date, customer_id, amount)
            SELECT '2026-07-20', 102, 299.99
            WHERE NOT EXISTS (SELECT 1 FROM orders_range WHERE customer_id = 102 AND order_date = '2026-07-20');
            
            INSERT INTO orders_range (order_date, customer_id, amount)
            SELECT '2026-08-01', 103, 499.50
            WHERE NOT EXISTS (SELECT 1 FROM orders_range WHERE customer_id = 103 AND order_date = '2026-08-01');
        """))

        # Seed initial sample records into Hash Partitioned Table
        conn.execute(text("""
            INSERT INTO users_hash (user_id, username, email)
            SELECT 1, 'alice', 'alice@example.com'
            WHERE NOT EXISTS (SELECT 1 FROM users_hash WHERE user_id = 1);
            
            INSERT INTO users_hash (user_id, username, email)
            SELECT 2, 'bob', 'bob@example.com'
            WHERE NOT EXISTS (SELECT 1 FROM users_hash WHERE user_id = 2);
            
            INSERT INTO users_hash (user_id, username, email)
            SELECT 3, 'charlie', 'charlie@example.com'
            WHERE NOT EXISTS (SELECT 1 FROM users_hash WHERE user_id = 3);
            
            INSERT INTO users_hash (user_id, username, email)
            SELECT 4, 'david', 'david@example.com'
            WHERE NOT EXISTS (SELECT 1 FROM users_hash WHERE user_id = 4);
        """))

        # Seed initial sample records into List Partitioned Table
        conn.execute(text("""
            INSERT INTO customers_list (name, region)
            SELECT 'Acme Corp', 'US'
            WHERE NOT EXISTS (SELECT 1 FROM customers_list WHERE name = 'Acme Corp');
            
            INSERT INTO customers_list (name, region)
            SELECT 'Global Logistics', 'EU'
            WHERE NOT EXISTS (SELECT 1 FROM customers_list WHERE name = 'Global Logistics');
            
            INSERT INTO customers_list (name, region)
            SELECT 'Tokyo Tech', 'JP'
            WHERE NOT EXISTS (SELECT 1 FROM customers_list WHERE name = 'Tokyo Tech');
        """))

        conn.commit()

