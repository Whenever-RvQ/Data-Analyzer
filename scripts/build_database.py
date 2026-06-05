"""
Olist 巴西电商数据集 - 数据库建库脚本
=======================================
功能：
1. 读取清洗后的 CSV 文件
2. 创建 SQLite 数据库及表结构
3. 导入清洗后数据
4. 为主键和外键字段创建索引
5. 验证数据完整性
"""

import sqlite3
import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(BASE_DIR, "ecommerce.db")

# ============================================================
# 1. 数据库表结构定义
# ============================================================
SCHEMA_SQL = """
-- 客户表
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT NOT NULL,
    customer_zip_code_prefix TEXT,
    customer_city TEXT,
    customer_state TEXT
);

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    order_status TEXT,
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 订单明细表
CREATE TABLE IF NOT EXISTS order_items (
    order_id TEXT NOT NULL,
    order_item_id INTEGER,
    product_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    shipping_limit_date TIMESTAMP,
    price REAL,
    freight_value REAL,
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
);

-- 商品表
CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_category_name TEXT,
    product_name_lenght REAL,
    product_description_lenght REAL,
    product_photos_qty REAL,
    product_weight_g REAL,
    product_length_cm REAL,
    product_height_cm REAL,
    product_width_cm REAL
);

-- 卖家表
CREATE TABLE IF NOT EXISTS sellers (
    seller_id TEXT PRIMARY KEY,
    seller_zip_code_prefix TEXT,
    seller_city TEXT,
    seller_state TEXT
);

-- 支付表
CREATE TABLE IF NOT EXISTS payments (
    order_id TEXT NOT NULL,
    payment_sequential INTEGER,
    payment_type TEXT,
    payment_installments INTEGER,
    payment_value REAL,
    PRIMARY KEY (order_id, payment_sequential),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- 评价表
CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- 商品类目翻译表
CREATE TABLE IF NOT EXISTS product_category_name_translation (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT
);
"""

INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_order_items_seller_id ON order_items(seller_id);
CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_reviews_order_id ON reviews(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_purchase_date ON orders(order_purchase_timestamp);
CREATE INDEX IF NOT EXISTS idx_reviews_score ON reviews(review_score);
"""

# ============================================================
# 2. 建库
# ============================================================
def create_database():
    """创建 SQLite 数据库和表结构"""
    logger.info(f"数据库路径: {DB_PATH}")

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        logger.info("已删除旧数据库文件")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 执行建表 SQL
    cursor.executescript(SCHEMA_SQL)
    logger.info("表结构创建完成")

    # 创建索引
    cursor.executescript(INDEX_SQL)
    logger.info("索引创建完成")

    conn.commit()
    conn.close()
    return DB_PATH

# ============================================================
# 3. 导入数据
# ============================================================
def import_data():
    """将清洗后 CSV 导入数据库"""
    conn = sqlite3.connect(DB_PATH)

    tables_files = {
        "customers": "customers.csv",
        "orders": "orders.csv",
        "order_items": "order_items.csv",
        "products": "products.csv",
        "sellers": "sellers.csv",
        "payments": "payments.csv",
        "reviews": "reviews.csv",
        "product_category_name_translation": "product_category_name_translation.csv",
    }

    for table, filename in tables_files.items():
        filepath = os.path.join(PROCESSED_DIR, filename)
        if not os.path.exists(filepath):
            logger.warning(f"文件不存在，跳过: {filepath}")
            continue

        df = pd.read_csv(filepath)
        df.to_sql(table, conn, if_exists="replace", index=False)
        logger.info(f"导入 {table}: {len(df)} 行")

    conn.commit()
    conn.close()
    logger.info("所有数据导入完成！")

# ============================================================
# 4. 验证
# ============================================================
def verify_database():
    """验证数据库完整性"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    logger.info("\n========== 数据库验证 ==========")

    # 检查所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    logger.info(f"表列表: {[t[0] for t in tables]}")

    # 检查每张表的行数
    for table in tables:
        name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM [{name}]")
        count = cursor.fetchone()[0]
        logger.info(f"  {name}: {count} 行")

    # 执行 5 个示例查询验证数据正确性
    logger.info("\n--- 示例验证查询 ---")

    queries = [
        ("总订单数", "SELECT COUNT(*) FROM orders"),
        ("总客户数", "SELECT COUNT(*) FROM customers"),
        ("总商品数", "SELECT COUNT(*) FROM products"),
        ("订单状态分布", "SELECT order_status, COUNT(*) as cnt FROM orders GROUP BY order_status ORDER BY cnt DESC"),
        ("支付方式分布", "SELECT payment_type, COUNT(*) as cnt FROM payments GROUP BY payment_type ORDER BY cnt DESC"),
    ]

    for label, query in queries:
        cursor.execute(query)
        result = cursor.fetchall()
        logger.info(f"[{label}] {query}")
        for row in result[:5]:
            logger.info(f"    {row}")

    conn.close()
    logger.info("\n数据库验证完成！")

# ============================================================
# Main
# ============================================================
def main():
    logger.info("=" * 60)
    logger.info("Olist 数据库建库开始")
    logger.info("=" * 60)

    create_database()
    import_data()
    verify_database()

    logger.info("\n" + "=" * 60)
    logger.info(f"数据库创建完成！路径: {DB_PATH}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
