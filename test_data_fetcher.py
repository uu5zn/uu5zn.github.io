# -*- coding: utf-8 -*-
"""
测试data_fetcher.py中的DataFetcher类
"""
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

try:
    from data_fetcher import DataFetcher
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"当前Python路径: {sys.path}")
    sys.exit(1)

def test_logger(message_type, status, message):
    """测试用的日志回调函数"""
    print(f"[{status}] {message_type}: {message}")


def main():
    """测试主函数"""
    print("开始测试DataFetcher...")
    
    # 创建DataFetcher实例
    fetcher = DataFetcher(logger_callback=test_logger)
    
    # 测试fetch_all_data方法
    print("\n测试fetch_all_data方法...")
    fetcher.fetch_all_data(force_refresh=True)
    
    # 检查关键数据是否存在
    key_data = ['中美国债收益率', 'US_BOND', '中国国债收益率10年']
    print("\n检查关键数据是否存在:")
    for key in key_data:
        if key in fetcher.all_data:
            data = fetcher.all_data[key]
            print(f"✓ {key}: 存在, 数据长度: {len(data)}")
            if len(data) > 0:
                print(f"  最新数据: {data.iloc[-1]:.4f}")
        else:
            print(f"✗ {key}: 不存在")
    
    print("\n测试完成!")


if __name__ == "__main__":
    main()
