# -*- coding: utf-8 -*-
"""
运行数据获取器，生成缓存文件
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_fetcher import DataFetcher

def logger_callback(module, level, message):
    """简单的日志回调函数"""
    timestamp = os.popen('date /t').read().strip() if os.name == 'nt' else os.popen('date').read().strip()
    print(f"[{timestamp}] [{level.upper()}] {module}: {message}")

if __name__ == "__main__":
    print("开始运行数据获取器...")
    fetcher = DataFetcher(logger_callback)
    fetcher.fetch_all_data(force_refresh=True)  # 强制刷新缓存
    print("数据获取完成，缓存文件已生成")
