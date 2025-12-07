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

# 直接测试mplfinance.plot()函数
def test_mplfinance_direct():
    print("=== 直接测试mplfinance.plot()函数 ===")
    
    # 确保输出目录存在
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"创建输出目录: {OUTPUT_DIR}")
    
    # 创建模拟数据
    stock_data = create_mock_kline_data()
    print(f"模拟数据行数: {len(stock_data)}")
    print(f"模拟数据是否为空: {stock_data.empty}")
    
    # 设置输出路径
    test_path = os.path.join(OUTPUT_DIR, "test_kline_direct.png")
    print(f"输出路径: {test_path}")
    
    # 直接使用mplfinance.plot()函数
    try:
        # 设置字体
        plt.rcParams.update({
            'font.size': 8,
            'font.family': 'sans-serif',
            'font.sans-serif': ['SimHei', 'DejaVu Sans', 'Arial'],
            'axes.unicode_minus': False,
            'figure.facecolor': 'black',
            'axes.facecolor': 'black',
            'savefig.facecolor': 'black',
        })
        
        # 创建样式
        style = mpf.make_mpf_style(
            base_mpf_style='charles',
            marketcolors=mpf.make_marketcolors(up='#e74c3c', down='#2ecc71', edge='inherit'),
            facecolor='black', edgecolor='white', figcolor='black',
            gridcolor='#666666', gridstyle='--',
            rc={
                'font.size': 8,
                'font.family': 'sans-serif',
                'font.sans-serif': ['SimHei', 'DejaVu Sans', 'Arial'],
                'axes.unicode_minus': False,
                'figure.facecolor': 'black',
                'axes.facecolor': 'black',
                'savefig.facecolor': 'black',
            }
        )
        
        # 调用mplfinance.plot()函数
        print("调用mplfinance.plot()函数...")
        mpf.plot(
            stock_data, 
            type='candle', 
            volume=False,
            savefig=dict(fname=test_path, dpi=150, bbox_inches='tight'),
            datetime_format='%m-%d',
            style=style,
            title='TEST', 
            tight_layout=True,
            warn_too_much_data=1000
        )
        
        # 检查文件是否生成
        if os.path.exists(test_path):
            file_size = os.path.getsize(test_path)
            print(f"✅ 文件生成成功！")
            print(f"   路径: {test_path}")
            print(f"   大小: {file_size} 字节")
            return True
        else:
            print(f"❌ 文件生成失败！")
            print(f"   路径: {test_path}")
            # 打印目录内容
            print(f"   输出目录内容: {os.listdir(OUTPUT_DIR)}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_mplfinance_direct()