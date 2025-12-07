# -*- coding: utf-8 -*-
import sys
import os
import pandas as pd
import numpy as np

# 添加src到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from charts import ChartGenerator
from config import OUTPUT_DIR

# 创建模拟K线数据
def create_mock_kline_data():
    dates = pd.date_range('2025-01-01', periods=30, freq='D')
    
    # 创建模拟数据
    data = {
        'Open': np.random.randint(100, 120, size=30) + np.random.rand(30),
        'High': np.random.randint(115, 130, size=30) + np.random.rand(30),
        'Low': np.random.randint(90, 105, size=30) + np.random.rand(30),
        'Close': np.random.randint(100, 120, size=30) + np.random.rand(30),
        'Volume': np.random.randint(1000000, 5000000, size=30)
    }
    
    df = pd.DataFrame(data, index=dates)
    return df

# 创建空数据
def create_empty_data():
    dates = pd.date_range('2025-01-01', periods=0, freq='D')
    df = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'], index=dates)
    return df

# 创建数据不足的情况
def create_insufficient_data():
    dates = pd.date_range('2025-01-01', periods=3, freq='D')
    data = {
        'Open': [100, 101, 102],
        'High': [103, 104, 105],
        'Low': [99, 100, 101],
        'Close': [102, 103, 104],
        'Volume': [1000000, 2000000, 3000000]
    }
    df = pd.DataFrame(data, index=dates)
    return df

# 创建只有NaN收盘价的数据
def create_nan_data():
    dates = pd.date_range('2025-01-01', periods=30, freq='D')
    data = {
        'Open': np.random.randint(100, 120, size=30) + np.random.rand(30),
        'High': np.random.randint(115, 130, size=30) + np.random.rand(30),
        'Low': np.random.randint(90, 105, size=30) + np.random.rand(30),
        'Close': np.full(30, np.nan),  # 全为NaN
        'Volume': np.random.randint(1000000, 5000000, size=30)
    }
    df = pd.DataFrame(data, index=dates)
    return df

# 模拟日志回调函数
def mock_logger(category, status, message, **kwargs):
    print(f"📝 日志: [{category}] [{status}] {message} {kwargs}")

# 测试修改后的plot_kline方法
def test_plot_kline():
    print("=== 测试修改后的plot_kline方法 ===")
    
    # 初始化ChartGenerator
    chart_gen = ChartGenerator(mock_logger)
    
    # 测试1: 使用模拟数据（应该成功）
    print("\n测试1 - 使用模拟数据")
    result = chart_gen.plot_kline("TEST", "test_kline_mock.png")
    print(f"测试1结果: {result}")
    
    # 检查文件是否生成
    test_file1 = os.path.join(OUTPUT_DIR, "test_kline_mock.png")
    if os.path.exists(test_file1):
        print(f"✅ 文件生成成功: {test_file1}")
        print(f"   文件大小: {os.path.getsize(test_file1)} 字节")
    else:
        print(f"❌ 文件生成失败: {test_file1}")

if __name__ == "__main__":
    test_plot_kline()