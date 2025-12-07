# -*- coding: utf-8 -*-
"""
测试mplfinance的savefig参数格式是否正确
"""
import os
import sys
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from datetime import datetime, timedelta
from src.config import OUTPUT_DIR

print("=== 测试mplfinance savefig参数格式 ===")
print(f"当前工作目录: {os.getcwd()}")
print(f"OUTPUT_DIR: {OUTPUT_DIR}")

# 创建测试数据
date_rng = pd.date_range(start='2023-01-01', end='2023-01-10', freq='D')
stock_data = pd.DataFrame({
    'Open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
    'High': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
    'Low': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
    'Close': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
    'Volume': [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
}, index=date_rng)

print(f"测试数据创建成功: {len(stock_data)} 行")

# 测试1: 使用字符串路径格式（旧格式）
print("\n=== 测试1: 使用字符串路径格式（旧格式） ===")
test_filename1 = 'test_kline_old_format.png'
test_path1 = os.path.join(OUTPUT_DIR, test_filename1)
try:
    mpf.plot(
        stock_data, type='candle', volume=False,
        savefig=test_path1, datetime_format='%m-%d',
        title='Test Kline (Old Format)', tight_layout=True
    )
    print(f"✅ 旧格式保存成功: {test_filename1}")
    if os.path.exists(test_path1):
        print(f"✅ 文件确实存在")
        file_size = os.path.getsize(test_path1)
        print(f"✅ 文件大小: {file_size} bytes")
    else:
        print(f"❌ 文件不存在")
except Exception as e:
    print(f"❌ 旧格式保存失败: {e}")

# 测试2: 使用字典格式（新格式）
print("\n=== 测试2: 使用字典格式（新格式） ===")
test_filename2 = 'test_kline_new_format.png'
test_path2 = os.path.join(OUTPUT_DIR, test_filename2)
try:
    mpf.plot(
        stock_data, type='candle', volume=False,
        savefig=dict(fname=test_path2, dpi=150, bbox_inches='tight'),
        datetime_format='%m-%d',
        title='Test Kline (New Format)', tight_layout=True
    )
    print(f"✅ 新格式保存成功: {test_filename2}")
    if os.path.exists(test_path2):
        print(f"✅ 文件确实存在")
        file_size = os.path.getsize(test_path2)
        print(f"✅ 文件大小: {file_size} bytes")
    else:
        print(f"❌ 文件不存在")
except Exception as e:
    print(f"❌ 新格式保存失败: {e}")

# 测试3: 测试创建目录权限
print("\n=== 测试3: 测试创建目录权限 ===")
test_dir = os.path.join(OUTPUT_DIR, 'test_subdir')
try:
    os.makedirs(test_dir, exist_ok=True)
    print(f"✅ 成功创建子目录: {test_dir}")
    # 在子目录中保存文件
    test_filename3 = os.path.join(test_dir, 'test_subdir_chart.png')
    plt.figure(figsize=(6, 4))
    plt.plot([1, 2, 3, 4], [1, 4, 2, 3])
    plt.savefig(test_filename3)
    plt.close()
    if os.path.exists(test_filename3):
        print(f"✅ 成功在子目录中保存文件")
    else:
        print(f"❌ 无法在子目录中保存文件")
except Exception as e:
    print(f"❌ 创建目录或保存文件失败: {e}")

print("\n=== 测试结束 ===")
