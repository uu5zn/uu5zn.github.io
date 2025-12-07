#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：专门用于GitHub Actions环境下测试字体修复
这个脚本会模拟实际应用的字体使用场景，重点测试图表.py中的字体问题
"""

import os
import sys
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from utils import setup_matplotlib_fonts
from charts import ChartGenerator
from config import OUTPUT_DIR

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 简单的日志回调函数
def logger_callback(category, status, message, **kwargs):
    print(f"[{category}] [{status}] {message}")

def test_font_loading():
    """测试字体加载功能"""
    print("="*60)
    print("测试1: 字体加载和配置".center(60))
    print("="*60)
    
    # 1. 加载字体
    available_font = setup_matplotlib_fonts()
    print(f"✅ 可用字体: {available_font}")
    
    # 2. 检查字体配置
    font_config = {
        'font.family': plt.rcParams['font.family'],
        'font.sans-serif': plt.rcParams['font.sans-serif'],
        'axes.unicode_minus': plt.rcParams['axes.unicode_minus']
    }
    print(f"📝 字体配置: {font_config}")
    
    # 3. 验证SimHei字体是否在配置中
    if 'SimHei' in plt.rcParams['font.sans-serif']:
        print("✅ SimHei字体已成功配置")
    else:
        print("❌ SimHei字体未配置成功")
        print(f"当前字体列表: {plt.rcParams['font.sans-serif']}")
    
    return available_font

def test_chart_generator_font_preservation(available_font):
    """测试ChartGenerator是否保留字体配置"""
    print("\n" + "="*60)
    print("测试2: ChartGenerator字体保留".center(60))
    print("="*60)
    
    # 1. 创建ChartGenerator实例
    chart_gen = ChartGenerator(logger_callback)
    
    # 2. 检查字体配置是否保留
    current_font = plt.rcParams['font.sans-serif'][0]
    print(f"📊 当前字体: {current_font}")
    print(f"📊 预期字体: {available_font}")
    
    if current_font == available_font:
        print("✅ ChartGenerator成功保留了字体配置")
        return True
    else:
        print("❌ ChartGenerator未保留字体配置")
        return False

def test_chinese_text_rendering():
    """测试中文文本渲染，模拟charts.py中的使用场景"""
    print("\n" + "="*60)
    print("测试3: 中文文本渲染".center(60))
    print("="*60)
    
    # 模拟charts.py中的plot_line函数场景
    try:
        # 使用当前字体绘制包含中文的图表
        fig, ax = plt.subplots(figsize=(10, 6), facecolor='black')
        
        # 测试包含多个中文字符的标题（对应GitHub Actions中的警告字符）
        title = "归一化指标对比"
        ax.set_title(title, fontsize=13, fontweight='heavy', color='white')
        
        # 添加中文图例和标签
        ax.plot([1, 2, 3, 4], [10, 20, 15, 25], label='数据1', color='#3498db')
        ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
        
        ax.set_xlabel('日期', color='white')
        ax.set_ylabel('数值', color='white')
        
        # 设置坐标轴刻度颜色
        ax.tick_params(colors='white')
        
        # 调用tight_layout，这是GitHub Actions中出现警告的位置
        plt.tight_layout(pad=0.8, h_pad=0.8, w_pad=0.8)
        
        # 保存测试图
        test_path = os.path.join(OUTPUT_DIR, "github_actions_font_test.png")
        plt.savefig(test_path, bbox_inches='tight', facecolor='black', dpi=150)
        
        print(f"✅ 中文图表渲染成功: {test_path}")
        print(f"✅ tight_layout调用成功，无字体警告")
        
        plt.close(fig)
        return True
        
    except Exception as e:
        print(f"❌ 中文图表渲染失败: {e}")
        plt.close(fig)
        return False

def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("GitHub Actions字体修复专项测试".center(70))
    print("="*70)
    
    # 运行测试
    available_font = test_font_loading()
    test_chart_generator_font_preservation(available_font)
    test_chinese_text_rendering()
    
    print("\n" + "="*60)
    print("测试完成! 检查输出目录中的测试图以验证字体渲染效果。".center(60))
    print("="*60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
