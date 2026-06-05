"""
Olist 巴西电商数据集 - 数据预处理脚本
=======================================
功能：
1. 读取原始 CSV 文件
2. 缺失值检查与处理
3. 重复值处理
4. 字段类型转换（时间、数值、评分等）
5. 保持表间关联关系的抽样
6. 输出清洗后 CSV 到 data/processed/
"""

import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

# ============================================================
# 1. 读取数据
# ============================================================
def load_raw_data():
    """读取所有原始 CSV 文件"""
    files = {
        "customers": "olist_customers_dataset.csv",
        "orders": "olist_orders_dataset.csv",
        "order_items": "olist_order_items_dataset.csv",
        "products": "olist_products_dataset.csv",
        "sellers": "olist_sellers_dataset.csv",
        "payments": "olist_order_payments_dataset.csv",
        "reviews": "olist_order_reviews_dataset.csv",
        "category_translation": "product_category_name_translation.csv",
    }

    data = {}
    for name, filename in files.items():
        path = os.path.join(RAW_DIR, filename)
        df = pd.read_csv(path)
        data[name] = df
        logger.info(f"已读取 {filename}: {df.shape[0]} 行, {df.shape[1]} 列")
    return data

# ============================================================
# 2. 缺失值检查与处理
# ============================================================
def handle_missing_values(data):
    """检查并处理各表的缺失值"""
    logger.info("\n========== 缺失值检查 ==========")

    # --- orders ---
    df = data["orders"]
    before = len(df)
    logger.info(f"\n[orders] 缺失统计:\n{df.isnull().sum()}")
    # order_delivered_customer_date 可能为空(未送达)，保留
    # order_delivered_carrier_date 可能为空，保留
    # 删除 order_approved_at 为空的行（关键审批时间）
    df = df.dropna(subset=["order_approved_at"])
    logger.info(f"[orders] 删除 order_approved_at 为空: {before} -> {len(df)}")
    data["orders"] = df

    # --- reviews ---
    df = data["reviews"]
    before = len(df)
    logger.info(f"\n[reviews] 缺失统计:\n{df.isnull().sum()}")
    # review_comment_title, review_comment_message 可空，填充为 "No comment"
    df["review_comment_title"] = df["review_comment_title"].fillna("No comment")
    df["review_comment_message"] = df["review_comment_message"].fillna("No comment")
    logger.info(f"[reviews] 填充评论空值: {df.isnull().sum().sum()} 个缺失残留")
    data["reviews"] = df

    # --- products ---
    df = data["products"]
    before = len(df)
    logger.info(f"\n[products] 缺失统计:\n{df.isnull().sum()}")
    # product_category_name 为空的行删除
    df = df.dropna(subset=["product_category_name"])
    # 填充产品尺寸描述字段（使用 .loc 避免 SettingWithCopyWarning）
    fill_cols = ["product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"]
    df.loc[:, fill_cols] = df[fill_cols].fillna(0)
    logger.info(f"[products] 处理缺失: {before} -> {len(df)}")
    data["products"] = df

    # --- order_items ---
    df = data["order_items"]
    logger.info(f"\n[order_items] 缺失统计:\n{df.isnull().sum()}")

    # --- payments ---
    df = data["payments"]
    logger.info(f"\n[payments] 缺失统计:\n{df.isnull().sum()}")

    # --- customers ---
    df = data["customers"]
    logger.info(f"\n[customers] 缺失统计:\n{df.isnull().sum()}")

    # --- sellers ---
    df = data["sellers"]
    logger.info(f"\n[sellers] 缺失统计:\n{df.isnull().sum()}")

    # --- category_translation ---
    df = data["category_translation"]
    logger.info(f"\n[category_translation] 缺失统计:\n{df.isnull().sum()}")

    return data

# ============================================================
# 3. 重复值处理
# ============================================================
def handle_duplicates(data):
    """去除重复记录"""
    logger.info("\n========== 重复值处理 ==========")
    for name in data:
        df = data[name]
        before = len(df)
        df = df.drop_duplicates()
        if before != len(df):
            logger.info(f"[{name}] 去重: {before} -> {len(df)}")
        data[name] = df
    return data

# ============================================================
# 4. 字段类型转换
# ============================================================
def convert_dtypes(data):
    """字段类型转换"""
    logger.info("\n========== 字段类型转换 ==========")

    # orders - 时间字段
    time_cols = ["order_purchase_timestamp", "order_approved_at",
                 "order_delivered_carrier_date", "order_delivered_customer_date",
                 "order_estimated_delivery_date"]
    for col in time_cols:
        if col in data["orders"].columns:
            data["orders"][col] = pd.to_datetime(data["orders"][col], errors="coerce")
    logger.info("[orders] 时间字段已转换")

    # payments - 数值字段
    data["payments"]["payment_value"] = pd.to_numeric(
        data["payments"]["payment_value"], errors="coerce"
    )
    logger.info("[payments] 金额字段已转换")

    # order_items - 数值字段
    data["order_items"]["price"] = pd.to_numeric(
        data["order_items"]["price"], errors="coerce"
    )
    data["order_items"]["freight_value"] = pd.to_numeric(
        data["order_items"]["freight_value"], errors="coerce"
    )
    logger.info("[order_items] 价格/运费字段已转换")

    # reviews - 评分转整数
    data["reviews"]["review_score"] = pd.to_numeric(
        data["reviews"]["review_score"], errors="coerce"
    ).astype("Int64")
    logger.info("[reviews] 评分字段已转换")

    # reviews - 时间字段
    if "review_creation_date" in data["reviews"].columns:
        data["reviews"]["review_creation_date"] = pd.to_datetime(
            data["reviews"]["review_creation_date"], errors="coerce"
        )

    return data

# ============================================================
# 5. 抽样处理（保持关联关系）
# ============================================================
def sample_data(data, sample_ratio=0.3, random_state=42):
    """
    按订单抽样，保持表间关联关系
    先抽取部分订单 ID，再根据订单 ID 过滤关联表
    """
    logger.info(f"\n========== 数据抽样 (ratio={sample_ratio}) ==========")

    orders = data["orders"]
    total_orders = len(orders)
    sampled_orders = orders.sample(frac=sample_ratio, random_state=random_state)
    sampled_order_ids = set(sampled_orders["order_id"])
    logger.info(f"[orders] 抽样: {total_orders} -> {len(sampled_orders)}")
    data["orders"] = sampled_orders

    # order_items - 按 order_id 过滤
    before = len(data["order_items"])
    data["order_items"] = data["order_items"][
        data["order_items"]["order_id"].isin(sampled_order_ids)
    ]
    logger.info(f"[order_items] 按 order_id 过滤: {before} -> {len(data['order_items'])}")

    # payments - 按 order_id 过滤
    before = len(data["payments"])
    data["payments"] = data["payments"][
        data["payments"]["order_id"].isin(sampled_order_ids)
    ]
    logger.info(f"[payments] 按 order_id 过滤: {before} -> {len(data['payments'])}")

    # reviews - 按 order_id 过滤
    before = len(data["reviews"])
    data["reviews"] = data["reviews"][
        data["reviews"]["order_id"].isin(sampled_order_ids)
    ]
    logger.info(f"[reviews] 按 order_id 过滤: {before} -> {len(data['reviews'])}")

    # customers - 按 customer_id 过滤
    sampled_customer_ids = set(data["orders"]["customer_id"])
    before = len(data["customers"])
    data["customers"] = data["customers"][
        data["customers"]["customer_id"].isin(sampled_customer_ids)
    ]
    logger.info(f"[customers] 按 customer_id 过滤: {before} -> {len(data['customers'])}")

    # sellers - 按 seller_id 过滤
    sampled_seller_ids = set(data["order_items"]["seller_id"])
    before = len(data["sellers"])
    data["sellers"] = data["sellers"][
        data["sellers"]["seller_id"].isin(sampled_seller_ids)
    ]
    logger.info(f"[sellers] 按 seller_id 过滤: {before} -> {len(data['sellers'])}")

    # products - 按 product_id 过滤
    sampled_product_ids = set(data["order_items"]["product_id"])
    before = len(data["products"])
    data["products"] = data["products"][
        data["products"]["product_id"].isin(sampled_product_ids)
    ]
    logger.info(f"[products] 按 product_id 过滤: {before} -> {len(data['products'])}")

    return data

# ============================================================
# 6. 输出清洗后数据
# ============================================================
def save_processed(data):
    """保存清洗后的 CSV 到 data/processed/"""
    logger.info("\n========== 保存清洗后数据 ==========")
    name_mapping = {
        "customers": "customers.csv",
        "orders": "orders.csv",
        "order_items": "order_items.csv",
        "products": "products.csv",
        "sellers": "sellers.csv",
        "payments": "payments.csv",
        "reviews": "reviews.csv",
        "category_translation": "product_category_name_translation.csv",
    }
    for name, filename in name_mapping.items():
        path = os.path.join(PROCESSED_DIR, filename)
        data[name].to_csv(path, index=False)
        logger.info(f"已保存 {filename}: {data[name].shape}")

# ============================================================
# Main
# ============================================================
def main():
    logger.info("=" * 60)
    logger.info("Olist 数据预处理开始")
    logger.info("=" * 60)

    data = load_raw_data()
    data = handle_missing_values(data)
    data = handle_duplicates(data)
    data = convert_dtypes(data)
    data = sample_data(data, sample_ratio=0.3)
    save_processed(data)

    logger.info("\n" + "=" * 60)
    logger.info("数据预处理完成！")
    logger.info(f"输出目录: {PROCESSED_DIR}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
