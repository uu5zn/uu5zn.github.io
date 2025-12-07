# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import os
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

# 测试mplfinance的savefig功能
def test_mplfinance_save():
    print("=== 测试mplfinance savefig功能 ===")
    
    # 创建模拟数据
    stock_data = create_mock_kline_data()
    print(f"模拟数据行数: {len(stock_data)}")
    print(f"模拟数据是否为空: {stock_data.empty}")
    
    # 设置输出路径
    output_dir = OUTPUT_DIR
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 测试1: 使用字典格式（推荐）
    test_path1 = os.path.join(output_dir, "test_kline_dict.png")
    print(f"\n测试1 - 使用字典格式保存到: {test_path1}")
    
    try:
        # 先检查目录是否存在
        print(f"输出目录是否存在: {os.path.exists(output_dir)}")
        print(f"输出目录权限: {oct(os.stat(output_dir).st_mode)[-3:]}")
        
        # 使用mplfinance绘制K线图，同时保存
        mpf.plot(
            stock_data, 
            type='candle', 
            volume=False,
            savefig=dict(fname=test_path1, dpi=150, bbox_inches='tight'),
            datetime_format='%m-%d',
            title='Test Kline (Dict Format)', 
            tight_layout=True
        )
        
        # 检查文件是否生成
        if os.path.exists(test_path1):
            file_size = os.path.getsize(test_path1)
            print(f"✅ 文件生成成功！大小: {file_size} 字节")
        else:
            print(f"❌ 文件生成失败！")
            # 打印目录内容
            print(f"输出目录内容: {os.listdir(output_dir)}")
            
    except Exception as e:
        print(f"❌ 测试1失败: {e}")
    
    # 测试2: 不使用savefig，只显示
    print(f"\n测试2 - 只显示图表，不保存")
    try:
        mpf.plot(
            stock_data, 
            type='candle', 
            volume=False,
            datetime_format='%m-%d',
            title='Test Kline (Show Only)', 
            tight_layout=True,
            show=True
        )
        print(f"✅ 图表显示成功！")
    except Exception as e:
        print(f"❌ 测试2失败: {e}")
    
    # 测试3: 使用字典格式保存，并手动显示
    test_path3 = os.path.join(output_dir, "test_kline_dict_show.png")
    print(f"\n测试3 - 使用字典格式保存并手动显示到: {test_path3}")
    
    try:
        # 使用mplfinance绘制K线图，同时保存
        fig, axlist = mpf.plot(
            stock_data, 
            type='candle', 
            volume=False,
            savefig=dict(fname=test_path3, dpi=150, bbox_inches='tight'),
            datetime_format='%m-%d',
            title='Test Kline (Dict Format + Show)', 
            tight_layout=True,
            returnfig=True
        )
        
        # 检查文件是否生成
        if os.path.exists(test_path3):
            file_size = os.path.getsize(test_path3)
            print(f"✅ 文件生成成功！大小: {file_size} 字节")
        else:
            print(f"❌ 文件生成失败！")
        
        # 手动显示
        plt.show()
        print(f"✅ 手动显示成功！")
        
    except Exception as e:
        print(f"❌ 测试3失败: {e}")

if __name__ == "__main__":
    test_mplfinance_save()