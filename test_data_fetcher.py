# -*- coding: utf-8 -*-
"""
测试data_fetcher.py的修改是否有效
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from data_fetcher import DataFetcher

# 简单的日志回调函数
def logger_callback(category, level, message):
    print(f"[{level}] {category}: {message}")

# 测试DataFetcher
if __name__ == "__main__":
    print("测试DataFetcher...")
    
    # 创建DataFetcher实例
    fetcher = DataFetcher(logger_callback)
    
    # 测试fetch_all_data方法
    print("\n1. 测试fetch_all_data方法...")
    fetcher.fetch_all_data(force_refresh=True)
    
    # 测试get_cached_data方法
    print("\n2. 测试get_cached_data方法...")
    # 测试获取已有数据
    us_bond = fetcher.get_cached_data('US_BOND')
    print(f"   US_BOND数据类型: {type(us_bond)}")
    print(f"   US_BOND数据形状: {us_bond.shape}")
    print(f"   US_BOND索引类型: {type(us_bond.index)}")
    
    # 测试获取新数据
    new_data = fetcher.get_cached_data('^N225')
    print(f"   ^N225数据类型: {type(new_data)}")
    print(f"   ^N225数据形状: {new_data.shape}")
    print(f"   ^N225索引类型: {type(new_data.index)}")
    
    # 检查数据格式是否正确
    print("\n3. 检查数据格式...")
    for key, data in fetcher.all_data.items():
        if key == '行业ETF':
            # 特殊处理行业ETF数据
            print(f"   {key}: {type(data)}, 索引类型: {type(data.index)}")
        else:
            print(f"   {key}: {type(data)}, 索引类型: {type(data.index)}")
    
    print("\n测试完成!")
