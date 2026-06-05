#!/usr/bin/env python3
"""
一键运行脚本 - 启动 Olist 电商数据分析智能体
"""

import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def check_database():
    """检查数据库是否存在"""
    db_path = os.path.join(BASE_DIR, "ecommerce.db")
    if not os.path.exists(db_path):
        print("=" * 60)
        print("⚠️  数据库不存在，正在创建...")
        print("=" * 60)
        subprocess.run([sys.executable, "scripts/build_database.py"], cwd=BASE_DIR)
    else:
        print(f"✅ 数据库已存在: {os.path.getsize(db_path) / 1024 / 1024:.1f} MB")


def check_deps():
    """检查依赖"""
    missing = []
    for mod in ["pandas", "plotly", "streamlit", "numpy"]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        print("=" * 60)
        print(f"📦 缺少依赖: {', '.join(missing)}，正在安装...")
        print("=" * 60)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=BASE_DIR,
        )
    else:
        print("✅ 核心依赖已就绪")


def main():
    print("=" * 60)
    print("📊 Olist 电商数据分析智能体")
    print("=" * 60)
    print()

    # 1. 检查依赖
    check_deps()

    # 2. 检查/创建数据库
    check_database()

    # 3. 启动 Streamlit
    print()
    print("=" * 60)
    print("🚀 正在启动 Web 应用...")
    print("   浏览器打开后即可使用")
    print("=" * 60)
    print()

    streamlit_path = os.path.join(BASE_DIR, "app", "streamlit_app.py")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", streamlit_path],
        cwd=BASE_DIR,
    )


if __name__ == "__main__":
    main()
