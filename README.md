# 📊 Olist 电商数据分析智能体

基于 **LangChain + SQLite + Streamlit** 的智能数据分析系统，通过自然语言驱动，对 [Olist 巴西电商公开数据集](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 进行交互式分析。

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 🗣️ **自然语言查询** | 用中文提问，自动生成 SQL 并执行 |
| 📋 **SQL 展示** | 展示 LLM 生成的 SQL 语句，方便学习和验证 |
| 📊 **可视化图表** | 自动识别数据类型，展示折线图、柱状图、饼图 |
| 💡 **业务分析** | 查询结果自动转为自然语言分析结论 |
| 🔒 **SQL 安全** | 仅执行 SELECT 查询，禁止修改数据库 |
| 🧩 **双模式运行** | 支持 OpenAI API 模式和本地回退模式 |
| 📌 **推荐问题** | 提供 6 个预置业务分析问题快速入口 |
| 💾 **对话记录** | 保留历史查询，方便对比分析 |

## 🏗️ 项目架构

```
data-analyzer/
├── data/
│   ├── raw/                    # 原始 CSV 数据集
│   └── processed/              # 清洗后 CSV 数据
├── scripts/
│   ├── preprocess.py           # 数据清洗脚本
│   └── build_database.py       # 建库脚本
├── agent/
│   └── data_agent.py           # Data Agent 智能体
├── app/
│   └── streamlit_app.py        # Streamlit Web 界面
├── docs/
│   └── usage_guide.md          # 详细使用说明
├── ecommerce.db                # SQLite 数据库
├── run.py                      # 一键启动脚本
├── requirements.txt            # Python 依赖
└── README.md                   # 本文档
```

### 数据处理流水线

```
原始 CSV → preprocess.py → 清洗后 CSV → build_database.py → SQLite DB → Agent → Streamlit UI
```

## 🚀 快速开始

### 前置条件

- Python 3.9+
- pip 包管理器

### 第一步：安装依赖

```bash
cd data-analyzer
pip install -r requirements.txt
```

### 第二步：数据处理（二选一）

**方式 A：一站启动（推荐）**

```bash
python run.py
```
自动完成：安装依赖 → 创建数据库 → 启动 Web 界面。

**方式 B：分步执行**

```bash
# 步骤 1：数据清洗
python scripts/preprocess.py

# 步骤 2：建库
python scripts/build_database.py

# 步骤 3：启动 Web 界面
streamlit run app/streamlit_app.py
```

### 第三步：配置 API Key（可选）

本智能体支持 **两种运行模式**：

#### 模式 1：OpenAI 模式（推荐，功能完整）

需要 OpenAI API Key 才能使用自然语言生成 SQL 功能：

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
streamlit run app/streamlit_app.py
```

> 支持模型：`gpt-4o-mini`（默认）、`gpt-4o`、`gpt-4` 等

#### 模式 2：本地回退模式（免 API Key）

无需任何配置，直接启动即可使用。系统会通过关键词匹配执行预定义的 5 个核心分析查询：

1. 月度订单趋势
2. 销售额 TOP10 商品类目
3. 支付方式分布
4. 各州物流时效
5. 延迟送达与评分关系

> 该模式适合环境演示和教学场景，但只能回答预定义的问题。

### 第四步：在浏览器中使用

启动后浏览器会自动打开 `http://localhost:8501`，界面如下：

- **左侧侧边栏**：显示 API 状态、数据库信息、表结构参考
- **上方推荐问题**：6 个数据分析问题，一键点击即可查询
- **中部输入框**：支持自定义自然语言问题输入
- **下方对话区**：展示历史查询的 SQL、结果表格、图表和分析结论

## 🎯 核心分析场景

### 场景 1：月度订单趋势

> **问题**：每个月的订单量是多少？

自动生成趋势折线图，展示订单量随时间变化，给出最高月份分析。

### 场景 2：商品类目销售额分析

> **问题**：销售额最高的 10 个商品类目是什么？

多表 JOIN 查询，柱状图展示 TOP10 类目销售额排名。

### 场景 3：支付方式分析

> **问题**：不同支付方式的订单数量和平均支付金额分别是多少？

分组聚合查询，饼图展示支付方式占比分布。

### 场景 4：物流时效分析

> **问题**：各州的平均配送时间是多少天？

日期计算 + 分组聚合，柱状图展示各州配送效率差异。

### 场景 5：客户评分分析

> **问题**：延迟送达订单的平均评分是否更低？

条件判断 CASE WHEN 查询，对比延迟 / 正常配送的评分差异。

## 🛠️ API 参考

### `agent/data_agent.py`

| 类/函数 | 说明 |
|---------|------|
| `DataAgent` | OpenAI 模式智能体，使用 LangChain + ChatOpenAI |
| `LocalFallbackAgent` | 本地回退模式，关键词匹配预定义查询 |
| `create_agent(db_path)` | 智能体工厂，自动检测 API Key 选择模式 |
| `execute_sql(db_path, sql)` | 安全执行 SQL 查询，含安全检查 |
| `validate_sql_safe(sql)` | SQL 安全检查，仅允许 SELECT/WITH |

#### 返回值格式

```python
{
    "question": "用户问题",
    "sql": "生成的 SELECT SQL",
    "result": {
        "success": True/False,
        "columns": ["列名1", "列名2"],
        "rows": [[值1, 值2], [值1, 值2]],
        "error": "错误信息（失败时）"
    },
    "analysis": "自然语言分析结论",
    "chart_type": "line/bar/pie",  # 本地模式特有
    "chart_title": "图表标题"       # 本地模式特有
}
```

### `scripts/preprocess.py`

| 函数 | 功能 |
|------|------|
| `load_raw_data()` | 读取所有原始 CSV |
| `handle_missing_values(data)` | 缺失值检测与处理 |
| `handle_duplicates(data)` | 重复记录去除 |
| `convert_dtypes(data)` | 字段类型转换 |
| `sample_data(data, ratio)` | 关联抽样（默认 30%） |

### `scripts/build_database.py`

| 函数 | 功能 |
|------|------|
| `create_database()` | 创建 SQLite 数据库 & 表结构 |
| `import_data()` | 导入清洗后 CSV 数据 |
| `verify_database()` | 数据完整性验证 |

## 🗄️ 数据库表结构

### customers（客户表）
| 字段 | 类型 | 说明 |
|------|------|------|
| customer_id | TEXT | 客户 ID（主键） |
| customer_unique_id | TEXT | 唯一标识 |
| customer_city | TEXT | 所在城市 |
| customer_state | TEXT | 所在州 |

### orders（订单表）
| 字段 | 类型 | 说明 |
|------|------|------|
| order_id | TEXT | 订单 ID（主键） |
| customer_id | TEXT | 客户 ID（外键） |
| order_status | TEXT | 状态：delivered / shipped / canceled |
| order_purchase_timestamp | TIMESTAMP | 下单时间 |
| order_delivered_customer_date | TIMESTAMP | 客户签收时间 |
| order_estimated_delivery_date | TIMESTAMP | 预计送达时间 |

### order_items（订单明细表）
| 字段 | 类型 | 说明 |
|------|------|------|
| order_id | TEXT | 订单 ID（联合主键） |
| order_item_id | INTEGER | 商品序号（联合主键） |
| product_id | TEXT | 商品 ID（外键） |
| seller_id | TEXT | 卖家 ID（外键） |
| price | REAL | 商品单价 |
| freight_value | REAL | 运费 |

### payments（支付表）
| 字段 | 类型 | 说明 |
|------|------|------|
| order_id | TEXT | 订单 ID（联合主键） |
| payment_sequential | INTEGER | 支付序号（联合主键） |
| payment_type | TEXT | 支付方式：credit_card / boleto / voucher / debit_card |
| payment_value | REAL | 支付金额 |

### reviews（评价表）
| 字段 | 类型 | 说明 |
|------|------|------|
| review_id | TEXT | 评价 ID（主键） |
| order_id | TEXT | 订单 ID（外键） |
| review_score | INTEGER | 评分（1-5） |

> 完整表结构见 `scripts/build_database.py` 中的 `SCHEMA_SQL` 定义。

## 🔧 开发指南

### 添加新的预定义查询（本地模式）

编辑 `agent/data_agent.py` 中的 `LocalFallbackAgent.PREDEFINED_QUERIES`：

```python
PREDEFINED_QUERIES = {
    "你的查询名称": {
        "keywords": ["关键词1", "关键词2"],
        "sql": "YOUR_SQL_QUERY",
        "chart_type": "bar",  # line / bar / pie 或 None
        "chart_title": "图表标题",
    },
}
```

### 修改 AI 模型

在 `agent/data_agent.py` 中修改 `DataAgent.__init__` 的 `model` 参数：

```python
agent = DataAgent(db_path, model="gpt-4o", temperature=0.1)
```

### 调整抽样比例

修改 `scripts/preprocess.py` 中的 `sample_data(data, sample_ratio=0.5)` 参数。

## 📦 文件清单

| 文件 | 说明 |
|------|------|
| `scripts/preprocess.py` | 数据清洗脚本 |
| `scripts/build_database.py` | 数据库建库脚本 |
| `agent/data_agent.py` | 数据分析智能体 |
| `app/streamlit_app.py` | Web 可视化界面 |
| `run.py` | 一键启动脚本 |
| `requirements.txt` | Python 依赖清单 |
| `README.md` | 本文档 |
| `docs/usage_guide.md` | 详细使用说明 |

## 🧪 测试验证

```bash
# 1. 验证数据处理
python scripts/preprocess.py

# 2. 验证建库
python scripts/build_database.py

# 3. 验证 Agent（本地模式）
python -c "from agent.data_agent import create_agent; \
  agent = create_agent('ecommerce.db'); \
  r = agent.ask('每月订单量'); \
  print(r['analysis'])"

# 4. 启动 Web 界面
streamlit run app/streamlit_app.py
```

## ⚠️ 常见问题

### Q：OpenAI API 报错？

- 检查 `OPENAI_API_KEY` 环境变量是否正确设置
- 检查网络代理配置，确保能访问 api.openai.com
- 确保 API Key 有足够余额

### Q：数据库文件被删除了？

重新运行 `python scripts/build_database.py` 即可重建。

### Q：Streamlit 启动报错？

```bash
pip install --upgrade streamlit
```

### Q：数据量太大运行慢？

可调整 `scripts/preprocess.py` 中的抽样比例 `sample_ratio` 为 0.1 或 0.05。

## 📄 许可证

本项目仅供学习和研究使用。数据集来自 [Kaggle Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)。
