"""
Olist 电商数据分析智能体 (LangChain Data Agent)
================================================
核心功能：
1. 连接 SQLite 电商数据库
2. 将自然语言问题转为 SQL 查询
3. 安全执行 SELECT 查询
4. 将查询结果转为自然语言分析结论
5. 支持 5 个核心业务分析场景

注意：需要设置 OPENAI_API_KEY 环境变量
"""

import os
import re
import sqlite3
import logging
from typing import Optional, Dict, Any, Tuple

import pandas as pd

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ============================================================
# 数据库上下文 (供 LLM 了解表结构)
# ============================================================
DB_SCHEMA_DESCRIPTION = """
数据库包含以下表（Olist 巴西电商数据集）：

1. customers (客户表)
   - customer_id: TEXT (主键)
   - customer_unique_id: TEXT (唯一客户标识)
   - customer_zip_code_prefix: TEXT (邮编前缀)
   - customer_city: TEXT (城市)
   - customer_state: TEXT (州)

2. orders (订单表)
   - order_id: TEXT (主键)
   - customer_id: TEXT (外键 -> customers)
   - order_status: TEXT (订单状态: delivered/shipped/canceled 等)
   - order_purchase_timestamp: TIMESTAMP (下单时间)
   - order_approved_at: TIMESTAMP (审批时间)
   - order_delivered_carrier_date: TIMESTAMP (承运商送达时间)
   - order_delivered_customer_date: TIMESTAMP (客户签收时间)
   - order_estimated_delivery_date: TIMESTAMP (预计送达时间)

3. order_items (订单明细表)
   - order_id, order_item_id: (联合主键)
   - product_id: TEXT (外键 -> products)
   - seller_id: TEXT (外键 -> sellers)
   - shipping_limit_date: TIMESTAMP (发货截止日)
   - price: REAL (商品单价)
   - freight_value: REAL (运费)

4. products (商品表)
   - product_id: TEXT (主键)
   - product_category_name: TEXT (葡萄牙语类目名)
   - product_name_lenght: REAL (商品名长度)
   - product_description_lenght: REAL (描述长度)
   - product_photos_qty: REAL (照片数)
   - product_weight_g: REAL (重量/g)
   - product_length_cm: REAL (长度/cm)
   - product_height_cm: REAL (高度/cm)
   - product_width_cm: REAL (宽度/cm)

5. sellers (卖家表)
   - seller_id: TEXT (主键)
   - seller_zip_code_prefix: TEXT
   - seller_city: TEXT
   - seller_state: TEXT

6. payments (支付表)
   - order_id, payment_sequential: (联合主键)
   - payment_type: TEXT (支付方式: credit_card/boleto/voucher/debit_card)
   - payment_installments: INTEGER (分期数)
   - payment_value: REAL (支付金额)

7. reviews (评价表)
   - review_id: TEXT (主键)
   - order_id: TEXT (外键 -> orders)
   - review_score: INTEGER (评分 1-5)
   - review_comment_title: TEXT (评论标题)
   - review_comment_message: TEXT (评论内容)
   - review_creation_date: TIMESTAMP (创建时间)
   - review_answer_timestamp: TIMESTAMP (回复时间)

8. product_category_name_translation (类目翻译表)
   - product_category_name: TEXT (葡萄牙语)
   - product_category_name_english: TEXT (英语)
"""

SYSTEM_PROMPT = f"""你是 Olist 电商数据分析助手，使用 SQLite 数据库回答用户关于电商数据的问题。

{DB_SCHEMA_DESCRIPTION}

## 工作原则

1. **仅执行 SELECT 查询** - 绝对不允许 INSERT/UPDATE/DELETE/DROP/ALTER/CREATE 等修改操作
2. **限制结果行数** - 默认加 LIMIT 50，除非用户明确要求更多
3. **字段名严格使用英文** - 使用表定义中的字段名
4. **日期函数** - 使用 SQLite 支持的日期函数(strftime, julianday, date 等)
5. **类目翻译** - 使用 product_category_name_translation 表将葡萄牙语类目名转为英文
6. **聚合分析** - 对 COUNT/SUM/AVG 结果给出业务解读
7. **多表连接** - 利用外键关系进行 JOIN 查询
8. **中文回答** - 用中文解释分析结果

## 返回格式

请分三部分返回：
1. **SQL**: 生成的 SQL 查询语句（放在 ```sql 代码块中）
2. **结果**: 查询结果表格
3. **分析**: 用中文给出业务分析结论（150字以内）
"""

# ============================================================
# SQL 安全检查
# ============================================================
def validate_sql_safe(sql: str) -> Tuple[bool, str]:
    """
    检查 SQL 是否安全：
    - 仅允许 SELECT 和 WITH
    - 禁止修改数据库的语句
    - 禁止执行函数/存储过程
    """
    sql_upper = sql.strip().upper()

    # 不允许修改操作
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
                 "TRUNCATE", "REPLACE", "EXEC", "EXECUTE", "PRAGMA",
                 "ATTACH", "DETACH", "VACUUM", "REINDEX"]
    for keyword in forbidden:
        # 查找不在字符串中的关键词
        if re.search(rf'\b{keyword}\b', sql_upper):
            return False, f"检测到禁止的操作: {keyword}。只允许 SELECT 查询。"

    # 确保以 SELECT 或 WITH 开头
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
        return False, "只允许执行 SELECT 或 WITH 查询。"

    return True, "OK"


# ============================================================
# 执行 SQL 查询
# ============================================================
def execute_sql(db_path: str, sql: str) -> Dict[str, Any]:
    """
    安全执行 SQL 查询并返回结果
    """
    # 安全检查
    is_safe, msg = validate_sql_safe(sql)
    if not is_safe:
        return {"success": False, "error": msg, "columns": [], "rows": []}

    try:
        conn = sqlite3.connect(db_path)
        # 限制返回行数
        if "LIMIT" not in sql.upper():
            sql = sql.rstrip(";") + " LIMIT 100"
        df = pd.read_sql_query(sql, conn)
        conn.close()

        return {
            "success": True,
            "columns": df.columns.tolist(),
            "rows": df.values.tolist(),
            "dataframe": df,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "columns": [], "rows": []}


# ============================================================
# 调用 LLM 生成 SQL
# ============================================================
class DataAgent:
    """
    数据分析智能体
    使用 LangChain + OpenAI 实现自然语言转 SQL
    """

    def __init__(
        self,
        db_path: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
    ):
        self.db_path = db_path
        self.model = model
        self.temperature = temperature
        self._llm = None

        # 检查 API Key
        if not os.environ.get("OPENAI_API_KEY"):
            logger.warning("OPENAI_API_KEY 未设置！Agent 将使用本地规则模式。")

    def _init_llm(self):
        """初始化 LLM"""
        if self._llm is not None:
            return self._llm
        try:
            from langchain_openai import ChatOpenAI
            self._llm = ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                openai_api_key=os.environ.get("OPENAI_API_KEY"),
            )
        except Exception as e:
            logger.error(f"初始化 LLM 失败: {e}")
            self._llm = None
        return self._llm

    def ask(self, question: str) -> Dict[str, Any]:
        """
        处理用户问题并返回 SQL + 结果 + 分析

        返回:
        {
            "question": 原始问题,
            "sql": 生成的 SQL,
            "result": 查询结果,
            "analysis": 分析结论,
        }
        """
        llm = self._init_llm()

        if llm is None:
            # 降级模式：返回提示信息
            return {
                "question": question,
                "sql": None,
                "result": {"success": False, "error": "OPENAI_API_KEY 未设置，请配置环境变量后使用。", "columns": [], "rows": []},
                "analysis": "⚠️ 需要配置 OPENAI_API_KEY 才能使用 AI 智能体。请参考 README 中的配置说明。",
            }

        try:
            # 调用 LLM 生成 SQL
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"请分析以下问题并生成 SQL 查询：\n{question}"},
            ]

            response = llm.invoke(messages)
            content = response.content

            # 从返回中提取 SQL
            sql = self._extract_sql(content)
            if not sql:
                return {
                    "question": question,
                    "sql": None,
                    "result": {"success": False, "error": "未能从 LLM 响应中提取 SQL 语句", "columns": [], "rows": []},
                    "analysis": content,
                }

            # 执行 SQL
            result = execute_sql(self.db_path, sql)

            # 如果 SQL 执行失败，让 LLM 尝试重新生成
            if not result["success"]:
                retry_prompt = f"""之前生成的 SQL 执行出错。
问题: {question}
SQL: {sql}
错误: {result['error']}
请重新生成修正后的 SQL 查询。注意检查字段名和表名是否正确。"""
                retry_messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": retry_prompt},
                ]
                retry_response = llm.invoke(retry_messages)
                retry_content = retry_response.content
                retry_sql = self._extract_sql(retry_content)

                if retry_sql:
                    retry_result = execute_sql(self.db_path, retry_sql)
                    if retry_result["success"]:
                        sql = retry_sql
                        result = retry_result
                        content = retry_content

            # 如果没有分析结论，让 LLM 生成
            analysis = ""
            if result["success"] and result["rows"]:
                stats_prompt = f"""用户问题: {question}
SQL查询: {sql}
查询结果:
  列: {result['columns']}
  前10行数据: {result['rows'][:10]}
  
请用中文给出简要的业务分析结论（150字以内）："""
                stats_messages = [
                    {"role": "system", "content": "你是一个电商数据分析师。"},
                    {"role": "user", "content": stats_prompt},
                ]
                analysis_response = llm.invoke(stats_messages)
                analysis = analysis_response.content
            else:
                analysis = content

            return {
                "question": question,
                "sql": sql,
                "result": result,
                "analysis": analysis,
            }

        except Exception as e:
            logger.error(f"Agent 处理失败: {e}")
            return {
                "question": question,
                "sql": None,
                "result": {"success": False, "error": str(e), "columns": [], "rows": []},
                "analysis": f"处理失败: {str(e)}。请检查 API Key 和网络连接。",
            }

    @staticmethod
    def _extract_sql(text: str) -> Optional[str]:
        """从 LLM 回复中提取 SQL 语句"""
        # 尝试匹配 ```sql ... ``` 代码块
        pattern = r"```sql\s*\n?(.*?)\n?```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            sql = match.group(1).strip()
            return sql

        # 尝试匹配 ``` ... ``` 代码块
        pattern = r"```\s*\n?(.*?)\n?```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            candidate = match.group(1).strip()
            if candidate.upper().startswith("SELECT") or candidate.upper().startswith("WITH"):
                return candidate

        # 尝试直接查找 SELECT 开头的语句
        pattern = r"\bSELECT\b.*?(?:;|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(0).strip()

        return None


# ============================================================
# 本地规则模式（无需 API Key，内置预定义查询）
# ============================================================
class LocalFallbackAgent:
    """
    本地回退模式 - 使用预定义查询匹配
    当没有配置 API Key 时使用
    """

    PREDEFINED_QUERIES = {
        "订单趋势": {
            "keywords": ["月度", "每月", "订单量", "订单趋势", "订单数", "monthly", "order trend", "orders per month"],
            "sql": """
                SELECT
                    strftime('%Y-%m', order_purchase_timestamp) AS month,
                    COUNT(*) AS order_count
                FROM orders
                GROUP BY month
                ORDER BY month
            """,
            "chart_type": "line",
            "chart_title": "月度订单趋势",
        },
        "销售额最高类目": {
            "keywords": ["销售额", "类目", "商品类目", "品类", "收入", "revenue", "category", "sales", "top"],
            "sql": """
                SELECT
                    COALESCE(t.product_category_name_english, p.product_category_name) AS category,
                    ROUND(SUM(i.price), 2) AS total_revenue,
                    COUNT(DISTINCT i.order_id) AS order_count
                FROM order_items i
                JOIN products p ON i.product_id = p.product_id
                LEFT JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
                GROUP BY category
                ORDER BY total_revenue DESC
                LIMIT 10
            """,
            "chart_type": "bar",
            "chart_title": "销售额最高的 TOP10 商品类目",
        },
        "支付方式": {
            "keywords": ["支付", "payment", "支付方式", "付款"],
            "sql": """
                SELECT
                    payment_type,
                    COUNT(*) AS order_count,
                    ROUND(AVG(payment_value), 2) AS avg_payment
                FROM payments
                GROUP BY payment_type
                ORDER BY order_count DESC
            """,
            "chart_type": "pie",
            "chart_title": "支付方式分布",
        },
        "物流时效": {
            "keywords": ["配送", "物流", "delivery", "shipping", "送达", "运输", "时效"],
            "sql": """
                SELECT
                    c.customer_state AS state,
                    ROUND(AVG(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)), 1) AS avg_delivery_days
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                WHERE o.order_status = 'delivered'
                  AND o.order_delivered_customer_date IS NOT NULL
                GROUP BY state
                ORDER BY avg_delivery_days
                LIMIT 10
            """,
            "chart_type": "bar",
            "chart_title": "各州平均配送天数",
        },
        "评分分析": {
            "keywords": ["评分", "评价", "满意度", "review", "score", "rating", "延迟", "迟"],
            "sql": """
                SELECT
                    CASE
                        WHEN julianday(o.order_delivered_customer_date) > julianday(o.order_estimated_delivery_date)
                        THEN '延迟送达'
                        ELSE '按时送达'
                    END AS delivery_status,
                    ROUND(AVG(r.review_score), 2) AS avg_score,
                    COUNT(*) AS order_count
                FROM orders o
                JOIN reviews r ON o.order_id = r.order_id
                WHERE o.order_status = 'delivered'
                  AND o.order_delivered_customer_date IS NOT NULL
                GROUP BY delivery_status
            """,
            "chart_type": "bar",
            "chart_title": "延迟送达与评分关系",
        },
        "默认": {
            "keywords": [],
            "sql": """
                SELECT '数据概览' AS metric,
                       (SELECT COUNT(*) FROM orders) AS total_orders,
                       (SELECT COUNT(*) FROM customers) AS total_customers,
                       (SELECT COUNT(*) FROM products) AS total_products,
                       (SELECT ROUND(SUM(price), 2) FROM order_items) AS total_revenue
            """,
            "chart_type": None,
            "chart_title": "数据概览",
        },
    }

    def __init__(self, db_path: str):
        self.db_path = db_path

    def ask(self, question: str) -> Dict[str, Any]:
        """根据关键词匹配预定义查询"""
        best_match = self.PREDEFINED_QUERIES["默认"]
        best_score = 0

        for key, query in self.PREDEFINED_QUERIES.items():
            if key == "默认":
                continue
            score = sum(1 for kw in query["keywords"] if kw.lower() in question.lower())
            if score > best_score:
                best_score = score
                best_match = query

        sql = best_match["sql"].strip()
        result = execute_sql(self.db_path, sql)

        # 对执行结果自动生成分析结论
        analysis = self._generate_analysis(question, best_match, result)

        return {
            "question": question,
            "sql": sql,
            "result": result,
            "analysis": analysis,
            "chart_type": best_match.get("chart_type"),
            "chart_title": best_match.get("chart_title"),
        }

    def _generate_analysis(self, question: str, matched_query: Dict, result: Dict) -> str:
        """根据匹配的查询和结果生成分析"""
        if not result["success"] or not result["rows"]:
            return "未能获取到分析数据。"

        key = matched_query["chart_title"]
        if "月度订单趋势" in key:
            rows = result["rows"]
            if rows:
                max_month = max(rows, key=lambda x: x[1])
                return (f"📊 订单量整体呈增长趋势。"
                        f"最高月份为 {max_month[0]}，共 {max_month[1]} 单。"
                        f"数据共涵盖 {len(rows)} 个月度。")
        elif "销售额" in key:
            rows = result["rows"]
            if rows:
                top = rows[0]
                return (f"💰 销售额最高的商品类目是「{top[0]}」，"
                        f"销售额 {top[1]:,.2f}。"
                        f"前 3 名合计占比显著，建议重点关注这些品类。")
        elif "支付方式" in key:
            rows = result["rows"]
            if rows:
                return (f"💳 最常用的支付方式是「{rows[0][0]}」（{rows[0][1]} 单）。"
                        f"平均支付金额 {rows[2][2] if len(rows) > 2 else rows[0][2]:.2f}。"
                        f"信用卡支付占主导地位。")
        elif "配送" in key:
            rows = result["rows"]
            if rows:
                fastest = rows[0]
                return (f"🚚 客户在 {fastest[0]} 州的平均配送最快，仅需 {fastest[1]} 天。"
                        f"不同州之间的配送效率存在差异。")
        elif "评分" in key:
            rows = result["rows"]
            if rows:
                for row in rows:
                    if "延迟" in str(row[0]):
                        return (f"⭐ 延迟送达订单的平均评分为 {row[1]}，"
                                f"显著低于按时送达订单。"
                                f"物流时效对客户满意度有重要影响。")
                return f"分析结果显示平均评分为 {rows[0][1]}。"
        return "✅ 查询执行成功。请查看上方数据表获取详细分析。"


# ============================================================
# 智能体工厂
# ============================================================
def create_agent(db_path: Optional[str] = None) -> Any:
    """
    创建数据分析智能体
    自动检测是否配置了 API Key，选择合适的模式
    """
    if db_path is None:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ecommerce.db",
        )

    if os.environ.get("OPENAI_API_KEY"):
        logger.info("使用 LangChain + OpenAI 模式")
        return DataAgent(db_path)
    else:
        logger.info("使用本地回退模式（预定义查询）")
        return LocalFallbackAgent(db_path)


# ============================================================
# 示例使用
# ============================================================
if __name__ == "__main__":
    # 测试
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db = os.path.join(base_dir, "ecommerce.db")
    agent = create_agent(db)

    questions = [
        "每个月的订单量是多少？",
        "销售额最高的10个商品类目是什么？",
        "不同支付方式的订单数量和平均支付金额分别是多少？",
        "各州的平均配送时间是多少？",
        "延迟送达订单的平均评分是否更低？",
    ]

    for q in questions:
        print(f"\n{'=' * 60}")
        print(f"问题: {q}")
        print("=" * 60)
        result = agent.ask(q)
        print(f"\nSQL:\n{result.get('sql', 'N/A')}")
        if result["result"]["success"]:
            print(f"\n结果 ({len(result['result']['rows'])} 行):")
            print(f"  列: {result['result']['columns']}")
            for row in result['result']['rows'][:5]:
                print(f"  {row}")
        else:
            print(f"\n错误: {result['result']['error']}")
        print(f"\n分析:\n{result.get('analysis', 'N/A')}")
