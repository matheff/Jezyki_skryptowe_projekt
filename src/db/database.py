import psycopg2


# conn = None
# cur = None

class DatabaseError(Exception):
    pass

class SalesDatabase:
    def __init__(self):
        self.conn = None
        self.cur = None

    def connect(self, host, port, dbname, user, password):
        try:
            try:
                import psycopg2
            except ImportError:
                raise ImportError(
                    "Pakiet psycopg2 nie jest zainstalowany. "
                    "Zainstaluj go poleceniem: pip install psycopg2-binary"
                )

            self.conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password
            )

            self.cur = self.conn.cursor()

        except ImportError:
            raise
        except Exception as e:
            raise DatabaseError(str(e))

    def disconnect(self):
        if self.cur:
            self.cur.close()

        if self.conn:
            self.conn.close()

        self.cur = None
        self.conn = None

    def is_connected(self) -> bool:
        return self.conn is not None and not self.conn.closed

    def create_schema(self):
        try:
            self.cur.execute("""
                                CREATE TABLE IF NOT EXISTS products (
                                    product_id VARCHAR(10) PRIMARY KEY,
                                    name VARCHAR(255) NOT NULL,
                                    category VARCHAR(100) NOT NULL,
                                    unit_price NUMERIC(10,2) NOT NULL
                                        CHECK (unit_price > 0)
                                );
                            """)

            self.cur.execute("""
                                CREATE TABLE IF NOT EXISTS transactions (
                                    id SERIAL PRIMARY KEY,
                                    date DATE NOT NULL,
                                    product_id VARCHAR(10) NOT NULL
                                        REFERENCES products(product_id),
                                    quantity INTEGER NOT NULL
                                        CHECK (quantity >= 1),
                                    seller VARCHAR(255) NOT NULL,
                                    region_code CHAR(2) NOT NULL,
                                    total_value NUMERIC(12,2) NOT NULL
                                );
                            """)

            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(str(e))

    def drop_schema(self):
        try:
            self.cur.execute("DROP TABLE IF EXISTS transactions;")
            self.cur.execute("DROP TABLE IF EXISTS products;")

            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(str(e))

    def import_dataset(self, dataset) -> int:
        try:
            products = [
                (
                    p["product_id"],
                    p["name"],
                    p["category"],
                    float(p["unit_price"])
                )
                for p in dataset["products"]
            ]

            transactions = [
                (
                    t["date"],
                    t["product_id"],
                    int(t["quantity"]),
                    t["seller"],
                    t["region_code"],
                    float(t["total_value"])
                )
                for t in dataset["transactions"]
            ]

            self.cur.executemany("""
                                    INSERT INTO products
                                    (product_id, name, category, unit_price)
                                    VALUES (%s, %s, %s, %s)
                                    ON CONFLICT (product_id) DO NOTHING
                                """, products)

            self.cur.executemany("""
                                    INSERT INTO transactions
                                    (date, product_id, quantity,
                                    seller, region_code, total_value)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, transactions)

            self.conn.commit()

            return len(transactions)

        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(str(e))

    def get_revenue_by_category(self):
        try:
            self.cur.execute("""
                                SELECT
                                    p.category,
                                    SUM(t.total_value) AS revenue
                                FROM transactions t
                                JOIN products p
                                    ON p.product_id = t.product_id
                                GROUP BY p.category
                                ORDER BY revenue DESC
                            """)

            return [
                (row[0], float(row[1]))
                for row in self.cur.fetchall()
            ]

        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(str(e))

    def get_top_sellers(self, n=5):
        try:
            self.cur.execute("""
                                SELECT
                                    seller,
                                    SUM(total_value) AS revenue
                                FROM transactions
                                GROUP BY seller
                                ORDER BY revenue DESC
                                LIMIT %s
                            """, (n,))

            return [
                (row[0], float(row[1]))
                for row in self.cur.fetchall()
            ]

        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(str(e))

    def get_monthly_summary(self):
        try:
            self.cur.execute("""
                                SELECT
                                    TO_CHAR(date, 'YYYY-MM') AS month,
                                    SUM(total_value) AS revenue
                                FROM transactions
                                GROUP BY month
                                ORDER BY month
                            """)

            return [
                (row[0], float(row[1]))
                for row in self.cur.fetchall()
            ]

        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(str(e))

    def get_transaction_count(self) -> int:
        try:
            self.cur.execute("""
                                SELECT COUNT(*)
                                FROM transactions
                            """)

            return self.cur.fetchone()[0]

        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(str(e))