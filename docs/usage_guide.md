# Olist 电商数据分析智能体 - 详细使用说明

## 目录

1. [环境配置](#1-环境配置)
2. [数据处理流程](#2-数据处理流程)
3. [启动应用](#3-启动应用)
4. [应用界面指南](#4-应用界面指南)
5. [自然语言查询示例](#5-自然语言查询示例)
6. [API Key 配置](#6-api-key-配置)
7. [自定义与扩展](#7-自定义与扩展)
8. [故障排除](#8-故障排除)

---

## 1. 环境配置

### 1.1 系统要求

- **Python**: 3.9 或更高版本
- **操作系统**: macOS / Linux / Windows
- **磁盘空间**: 至少 200MB（含数据集）

### 1.2 安装依赖

打开终端，进入项目目录：

```bash
cd data-analyzer
pip install -r requirements.txt
```

如果安装较慢，可以使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 1.3 验证安装

```bash
python -c "import pandas; import plotly; import streamlit; print('✅ 所有依赖安装成功')"
```

---

## 2. 数据处理流程

### 2.1 数据清洗（preprocess.py）

脚本功能：
- 读取 9 个原始 CSV 文件
- 统计缺失值并处理（删除关键空值、填充非关键空值）
- 去除重复记录
- 转换时间、金额、评分等字段类型
- 按 30% 比例抽样（保持表间关联）

运行方式：

```bash
python scripts/preprocess.py
```

预期输出示例：

```
[2026-01-15 10:30:00] INFO - 已读取 olist_orders_dataset.csv: 99441 行, 8 列
[2026-01-15 10:30:01] INFO - [orders] 删除 order_approved_at 为空: 99441 -> 99281
[2026-01-15 10:30:02] INFO - [orders] 抽样: 99281 -> 29784
[2026-01-15 10:30:05] INFO - 数据预处理完成！
```

处理后输出到 `data/processed/` 目录。

### 2.2 建库（build_database.py）

脚本功能：
- 创建 SQLite 数据库 `ecommerce.db`
- 创建 8 张关系表（含主键、外键、索引）
- 导入清洗后数据
- 执行验证查询

运行方式：

```bash
python scripts/build_database.py
```

预期输出示例：

```
[2026-01-15 10:31:00] INFO - 导入 orders: 29784 行
[2026-01-15 10:31:02] INFO - 数据库创建完成！路径: /path/to/data-analyzer/ecommerce.db
```

### 2.3 验证数据完整性

建库脚本会自动执行验证查询，包括：
- 总订单数、总客户数、总商品数
- 订单状态分布
- 支付方式分布

---

## 3. 启动应用

### 3.1 一键启动（推荐）

```bash
python run.py
```

该命令会自动：
1. 检查并安装依赖
2. 检查数据库是否存在，不存在则自动创建
3. 启动 Streamlit Web 应用

### 3.2 分步启动

```bash
# 步骤 1：数据清洗
python scripts/preprocess.py

# 步骤 2：建库
python scripts/build_database.py

# 步骤 3：启动应用
streamlit run app/streamlit_app.py
```

### 3.3 启动参数

Streamlit 支持以下常用参数：

```bash
# 指定端口
streamlit run app/streamlit_app.py --server.port 8888

# 禁止自动打开浏览器
streamlit run app/streamlit_app.py --server.headless true

# 开发模式（自动重载）
streamlit run app/streamlit_app.py --runner.fastReruns true
```

---

## 4. 应用界面指南

### 4.1 界面布局

```
┌──────────────────────────────────────────────────────────────┐
│  📊 Olist 电商数据分析智能体                    [清空对话]    │
│  基于 LangChain + SQLite 的智能数据分析助手                  │
├───────────┬──────────────────────────────────────────────────┤
│           │  💡 试试这些问题                                 │
│  ⚙️ 配置  │  [📈 月度订单] [💰 销售额 TOP10] [💳 支付方式]   │
│           │  [🚚 物流时效] [⭐ 评分分析] [📦 数据概览]        │
│  API 状态 │──────────────────────────────────────────────────│
│           │  🔍 [________________________________] [🚀 查询]  │
│  数据库   │──────────────────────────────────────────────────│
│           │  👤 你: 每个月的订单量是多少？                    │
│  数据集   │  🤖 Agent:                                      │
│           │  📝 生成的 SQL                                   │
│  表结构   │  📋 查询结果                                     │
│           │  📊 可视化图表                                   │
│           │  💡 业务分析                                     │
└───────────┴──────────────────────────────────────────────────┘
```

### 4.2 侧边栏信息

- **API 状态**：显示 OpenAI API Key 是否配置
- **数据库信息**：显示数据库文件和大小
- **数据集信息**：显示数据规模概览
- **表结构参考**：可展开查看各表的字段定义

### 4.3 查询方式

#### 方式 1：点击推荐问题

点击上方的推荐问题按钮，一键执行分析查询。

#### 方式 2：输入自定义问题

在输入框中输入自然语言问题，点击「查询」按钮。

### 4.4 查询结果展示

每次查询结果包含：

1. **SQL 语句**：AI 生成的 SQL（深色代码块）
2. **数据表格**：查询结果的可滚动表格
3. **可视化图表**：
   - 时间序列数据 → 折线图
   - 分类比较数据 → 柱状图
   - 占比数据 → 饼图
4. **业务分析结论**：蓝色高亮框中的自然语言分析

---

## 5. 自然语言查询示例

### 5.1 OpenAI 模式（完整功能）

| 问题类型 | 示例 |
|---------|------|
| 订单趋势 | "每月订单趋势如何？同比增长多少？" |
| 商品分析 | "哪些类目的商品平均价格最高？" |
| 客户分析 | "哪个城市的客户数量最多？" |
| 物流分析 | "平均配送时间最长的州是哪个？" |
| 卖家分析 | "哪个卖家的销售额最高？" |
| 复杂查询 | "2017年第四季度，信用支付的订单占比是多少？" |
| 关联分析 | "商品评分和配送时间有关系吗？" |

### 5.2 本地模式（预定义问题）

| 问题 | 对应分析 |
|------|---------|
| "每个月的订单量是多少？" | 月度订单趋势折线图 |
| "销售额最高的商品类目" | TOP10 销售额柱状图 |
| "各种支付方式的情况" | 支付方式饼图 |
| "各州配送时间" | 物流时效柱状图 |
| "延迟配送和评分的关系" | 评分对比柱状图 |

---

## 6. API Key 配置

### 6.1 获取 API Key

1. 前往 [OpenAI Platform](https://platform.openai.com/api-keys)
2. 注册 / 登录账号
3. 创建新的 API Key
4. 复制密钥（以 `sk-` 开头）

### 6.2 配置方式

#### 方式 A：环境变量（推荐）

```bash
# macOS / Linux
export OPENAI_API_KEY="sk-your-key-here"

# Windows (CMD)
set OPENAI_API_KEY=sk-your-key-here

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-your-key-here"
```

#### 方式 B：配置 .env 文件

在项目根目录创建 `.env` 文件：

```
OPENAI_API_KEY=sk-your-key-here
```

然后修改 `agent/data_agent.py` 使用 python-dotenv 加载。

#### 方式 C：永久配置

将 `export` 命令添加到 Shell 配置文件：

```bash
# macOS / Linux
echo 'export OPENAI_API_KEY="sk-your-key-here"' >> ~/.zshrc  # 或 ~/.bashrc
source ~/.zshrc
```

### 6.3 验证配置

```bash
echo $OPENAI_API_KEY
# 应输出 sk-... 格式的密钥
```

---

## 7. 自定义与扩展

### 7.1 修改 AI 模型

编辑 `agent/data_agent.py`：

```python
# 修改默认模型（第 108 行附近）
class DataAgent:
    def __init__(
        self,
        db_path: str,
        model: str = "gpt-4o",         # 改为 gpt-4o
        temperature: float = 0.1,       # 改为 0.1 让输出更稳定
    ):
```

支持的模型：
- `gpt-4o-mini`（默认，快速经济）
- `gpt-4o`（更强推理能力）
- `gpt-4-turbo`（兼容旧模型）

### 7.2 调整抽样比例

编辑 `scripts/preprocess.py`，修改第 12 行附近：

```python
def main():
    # ...
    data = sample_data(data, sample_ratio=0.5)  # 改为 50%
```

### 7.3 添加新的预定义查询（本地模式）

编辑 `agent/data_agent.py` 中的 `LocalFallbackAgent.PREDEFINED_QUERIES`：

```python
PREDEFINED_QUERIES = {
    "卖家销售额排行": {
        "keywords": ["卖家", "seller", "销售排行", "哪个卖家"],
        "sql": """
            SELECT s.seller_id, s.seller_city, s.seller_state,
                   ROUND(SUM(oi.price), 2) AS total_sales,
                   COUNT(DISTINCT oi.order_id) AS order_count
            FROM order_items oi
            JOIN sellers s ON oi.seller_id = s.seller_id
            GROUP BY s.seller_id
            ORDER BY total_sales DESC
            LIMIT 10
        """,
        "chart_type": "bar",
        "chart_title": "卖家销售额 TOP10",
    },
}
```

### 7.4 切换数据库类型

要将 SQLite 改为 MySQL 或 PostgreSQL：

1. 修改 `scripts/build_database.py` 使用对应的数据库驱动
2. 修改 `agent/data_agent.py` 中的 `execute_sql` 函数
3. 修改 `app/streamlit_app.py` 中的数据库连接路径

---

## 8. 故障排除

### 问题 1：ModuleNotFoundError

```
ModuleNotFoundError: No module named 'pandas'
```

**解决方案**：

```bash
pip install pandas
# 或完整安装
pip install -r requirements.txt
```

### 问题 2：OpenAI API 错误

```
openai.RateLimitError: Rate limit exceeded
```

**原因**：API 调用频率超限或余额不足

**解决方案**：
- 检查 API Key 余额
- 降低 `max_turns` 参数
- 使用代理（如需要）

### 问题 3：Streamlit 端口占用

```
Port 8501 is already in use
```

**解决方案**：

```bash
# 使用其他端口
streamlit run app/streamlit_app.py --server.port 8502

# 或终止占用进程
lsof -ti:8501 | xargs kill -9
```

### 问题 4：数据库文件损坏

```
sqlite3.DatabaseError: database disk image is malformed
```

**解决方案**：删除旧数据库重新创建

```bash
rm ecommerce.db
python scripts/build_database.py
```

### 问题 5：中文乱码

如果图表或界面出现乱码：

```python
# 在 streamlit_app.py 开头添加
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # macOS
# 或 ['SimHei']  # Windows
# 或 ['WenQuanYi Micro Hei']  # Linux
```

### 问题 6：启动后页面空白

- 检查终端是否有错误输出
- 确认浏览器版本兼容（推荐 Chrome / Edge 最新版）
- 尝试使用 `--server.headless false` 参数

---

## 附录：数据处理统计

### 原始数据规模

| 表名 | 原始行数 | 清洗后行数 | 说明 |
|------|---------|-----------|------|
| customers | 99,441 | 29,784 | 抽样 30% |
| orders | 99,441 | 29,784 | 抽样 30% |
| order_items | 112,650 | 33,840 | 关联过滤 |
| products | 32,951 | 14,912 | 关联过滤 |
| sellers | 3,095 | 2,353 | 关联过滤 |
| payments | 103,886 | 31,031 | 关联过滤 |
| reviews | 99,224 | 29,717 | 关联过滤 |

### 关键字段分布

- **订单状态**：delivered (97.1%)、shipped (1.2%)、canceled (0.5%)
- **支付方式**：credit_card (74.4%)、boleto (19.0%)、voucher (5.2%)、debit_card (1.5%)
- **评分范围**：1-5（整数），平均约 4.0

---

> 如遇到其他问题，请检查终端输出日志或在项目中提交 Issue。
