"""
Olist 电商数据分析智能体 - Streamlit Web 应用
==============================================
功能：
1. 自然语言查询输入
2. SQL 生成与执行
3. 查询结果表格展示
4. 可视化图表（折线图、柱状图、饼图）
5. 业务分析结论
6. 推荐问题快速入口
"""

import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.data_agent import create_agent

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="Olist 电商数据分析智能体",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 应用状态初始化
# ============================================================
if "agent" not in st.session_state:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "ecommerce.db")
    st.session_state.agent = create_agent(db_path)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ============================================================
# CSS 样式
# ============================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #6B7B8D;
        margin-bottom: 2rem;
    }
    .sql-block {
        background-color: #1E1E1E;
        color: #D4D4D4;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'SF Mono', 'Fira Code', monospace;
        font-size: 0.85rem;
        overflow-x: auto;
        margin: 0.5rem 0;
    }
    .analysis-box {
        background-color: #F0F9FF;
        border-left: 4px solid #1890FF;
        padding: 1rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
        font-size: 1rem;
        line-height: 1.6;
    }
    .error-box {
        background-color: #FFF2F0;
        border-left: 4px solid #FF4D4F;
        padding: 1rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    .recommend-btn {
        margin: 0.25rem;
        padding: 0.4rem 1rem;
        background-color: #F5F5F5;
        border: 1px solid #D9D9D9;
        border-radius: 20px;
        cursor: pointer;
        font-size: 0.85rem;
        transition: all 0.2s;
    }
    .recommend-btn:hover {
        background-color: #E6F7FF;
        border-color: #1890FF;
        color: #1890FF;
    }
    .chat-message-user {
        background-color: #E6F7FF;
        padding: 0.8rem 1.2rem;
        border-radius: 12px 12px 4px 12px;
        margin: 0.5rem 0;
        text-align: right;
    }
    .chat-message-agent {
        background-color: #F5F5F5;
        padding: 0.8rem 1.2rem;
        border-radius: 12px 12px 12px 4px;
        margin: 0.5rem 0;
    }
    .kpi-card {
        background-color: white;
        border: 1px solid #F0F0F0;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E3A5F;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #8C8C8C;
        margin-top: 0.3rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .badge-success {
        background: #F6FFED;
        color: #52C41A;
        border: 1px solid #B7EB8F;
    }
    .badge-warning {
        background: #FFFBE6;
        color: #FAAD14;
        border: 1px solid #FFE58F;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ 配置与信息")

    # API Key 状态
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        st.markdown(
            f'<span class="status-badge badge-success">✅ OpenAI API 已配置</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<span class="status-badge badge-warning">⚠️ 未配置 API Key（使用本地模式）</span>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 数据库信息
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "ecommerce.db")
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path) / (1024 * 1024)
        st.markdown(f"**数据库**: `ecommerce.db` ({db_size:.1f} MB)")
    else:
        st.markdown("**数据库**: ❌ 未找到，请先运行建库脚本")

    st.markdown("---")

    # 数据集信息
    st.markdown("### 📦 数据集")
    st.markdown("""
    - **Olist 巴西电商**
    - 约 99K 订单 (抽样 30%)
    - 8 张关系表
    - 客户 / 商品 / 卖家 / 支付 / 评价
    """)

    st.markdown("---")

    # 表结构参考
    st.markdown("### 📋 表结构快速参考")
    with st.expander("查看表结构"):
        st.markdown("""
        **customers** (客户)
        - customer_id, customer_city, customer_state

        **orders** (订单)
        - order_id, customer_id, order_status
        - order_purchase_timestamp
        - order_delivered_customer_date

        **order_items** (明细)
        - order_id, product_id, seller_id
        - price, freight_value

        **products** (商品)
        - product_id, product_category_name

        **payments** (支付)
        - order_id, payment_type, payment_value

        **reviews** (评价)
        - order_id, review_score

        **sellers** (卖家)
        - seller_id, seller_city, seller_state

        **product_category_name_translation** (类目翻译)
        """)

# ============================================================
# 主页面
# ============================================================
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="main-header">📊 Olist 电商数据分析智能体</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">基于 LangChain + SQLite 的智能数据分析助手，支持自然语言查询电商数据</div>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 清空对话", use_container_width=True):
        st.session_state.chat_history = []

# ============================================================
# 推荐问题
# ============================================================
st.markdown("### 💡 试试这些问题")

recommended_questions = [
    "📈 每个月的订单量是多少？订单量最高的月份？",
    "💰 销售额最高的 10 个商品类目是什么？",
    "💳 不同支付方式的订单数量和平均支付金额分别是多少？",
    "🚚 各州的平均配送时间是多少天？",
    "⭐ 延迟送达订单的平均评分是否更低？",
    "📦 总订单数、总客户数、总商品数、总收入各是多少？",
]

cols = st.columns(3)
for i, question in enumerate(recommended_questions):
    with cols[i % 3]:
        if st.button(question, key=f"recommend_{i}", use_container_width=True):
            # 处理问题
            with st.spinner("🤔 正在分析..."):
                result = st.session_state.agent.ask(question)
                st.session_state.chat_history.append({
                    "question": question,
                    "result": result,
                })
            st.rerun()

st.markdown("---")

# ============================================================
# 查询输入
# ============================================================
with st.form(key="query_form", clear_on_submit=True):
    query_col1, query_col2 = st.columns([5, 1])
    with query_col1:
        user_question = st.text_input(
            "🔍 输入你的数据分析问题",
            placeholder="例如：哪个州的客户最多？",
            label_visibility="collapsed",
        )
    with query_col2:
        submitted = st.form_submit_button("🚀 查询", use_container_width=True)

if submitted and user_question:
    with st.spinner("🤔 AI 智能体正在思考..."):
        result = st.session_state.agent.ask(user_question)
        st.session_state.chat_history.append({
            "question": user_question,
            "result": result,
        })
    st.rerun()

# ============================================================
# 对话历史展示
# ============================================================
for chat in reversed(st.session_state.chat_history):
    question = chat["question"]
    result = chat["result"]

    # 用户问题
    st.markdown(f'<div class="chat-message-user"><strong>👤 你</strong><br>{question}</div>', unsafe_allow_html=True)

    # Agent 回复
    with st.container():
        st.markdown('<div class="chat-message-agent">', unsafe_allow_html=True)

        if result["result"]["success"]:
            # --- SQL 展示 ---
            if result.get("sql"):
                st.markdown("**📝 生成的 SQL**")
                st.markdown(f'<div class="sql-block">{result["sql"]}</div>', unsafe_allow_html=True)

            show_data = result["result"]
            df = pd.DataFrame(show_data["rows"], columns=show_data["columns"])

            # --- 数据展示 ---
            if not df.empty:
                st.markdown("**📋 查询结果**")

                # 数据表格（可滚动）
                st.dataframe(df, use_container_width=True, height=min(280, 35 * len(df) + 40))

                # --- 可视化图表 ---
                st.markdown("**📊 可视化图表**")

                # 检测最佳图表类型
                numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                text_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()

                if len(numeric_cols) >= 1 and len(text_cols) >= 1:
                    x_col = text_cols[0]
                    y_col = numeric_cols[0]

                    # 根据数据特征选择图表类型
                    if len(set(df[x_col])) <= 5:
                        # 少量分类 -> 饼图
                        if len(numeric_cols) >= 1:
                            fig = px.pie(
                                df,
                                names=x_col,
                                values=y_col,
                                title=f"{y_col} 分布",
                                color_discrete_sequence=px.colors.qualitative.Set2,
                            )
                            fig.update_traces(textposition="inside", textinfo="percent+label")
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        # 多分类 -> 柱状图
                        fig = px.bar(
                            df,
                            x=x_col,
                            y=y_col,
                            title=f"{x_col} vs {y_col}",
                            color=y_col,
                            color_continuous_scale="Blues",
                            text_auto=".2s" if df[y_col].max() < 1e6 else ".2s",
                        )
                        fig.update_layout(
                            xaxis_tickangle=-45,
                            xaxis_title=x_col,
                            yaxis_title=y_col,
                        )
                        fig.update_traces(textposition="outside")
                        st.plotly_chart(fig, use_container_width=True)

                elif len(numeric_cols) >= 2:
                    # 多数值列 -> 折线图或组合图
                    if len(df) > 1:
                        fig = go.Figure()
                        for col in numeric_cols[:3]:
                            fig.add_trace(go.Scatter(
                                x=list(range(len(df))),
                                y=df[col],
                                mode="lines+markers",
                                name=col,
                            ))
                        fig.update_layout(
                            title="数值趋势",
                            xaxis_title="序号",
                            yaxis_title="值",
                            hovermode="x unified",
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    elif len(numeric_cols) >= 1:
                        # 单行数据 -> 指标卡片（仅展示数值列）
                        row = df.iloc[0]
                        numeric_row = {k: row[k] for k in numeric_cols}
                        metric_cols = st.columns(len(numeric_row))
                        for j, (col_name, value) in enumerate(numeric_row.items()):
                            with metric_cols[j]:
                                if isinstance(value, (int, float)):
                                    formatted = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
                                else:
                                    formatted = str(value)
                                st.markdown(f"""
                                <div class="kpi-card">
                                    <div class="kpi-value">{formatted}</div>
                                    <div class="kpi-label">{col_name}</div>
                                </div>
                                """, unsafe_allow_html=True)

                # 额外图表：如果有2个数值列，做散点图
                if len(numeric_cols) >= 2 and len(df) > 3:
                    with st.expander("📈 查看其他图表"):
                        fig = px.scatter(
                            df,
                            x=numeric_cols[0],
                            y=numeric_cols[1],
                            title=f"{numeric_cols[1]} vs {numeric_cols[0]}",
                            labels={numeric_cols[0]: numeric_cols[0], numeric_cols[1]: numeric_cols[1]},
                        )
                        st.plotly_chart(fig, use_container_width=True)

            # --- 分析结论 ---
            if result.get("analysis"):
                st.markdown("**💡 业务分析**")
                st.markdown(f'<div class="analysis-box">{result["analysis"]}</div>', unsafe_allow_html=True)

        else:
            # 错误展示
            st.markdown(f'<div class="error-box">❌ {result["result"]["error"]}</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# 空状态提示
# ============================================================
if not st.session_state.chat_history:
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem; color: #BFBFBF;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🔍</div>
        <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">输入你的数据分析问题，或点击上方推荐问题开始探索</div>
        <div style="font-size: 0.9rem;">本智能体支持：订单趋势、商品分析、支付分析、物流分析、评分分析等场景</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# 页脚
# ============================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #BFBFBF; font-size: 0.8rem;'>"
    "基于 LangChain + SQLite + Streamlit + Plotly 构建 | "
    "数据来源: Olist Brazilian E-Commerce Dataset"
    "</div>",
    unsafe_allow_html=True,
)
