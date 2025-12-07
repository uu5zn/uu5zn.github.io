#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试字体修复是否有效
用于验证setup_matplotlib_fonts()和ChartGenerator的字体配置是否正确
"""

import os
import sys
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from utils import setup_matplotlib_fonts, check_available_fonts
from charts import ChartGenerator
from config import OUTPUT_DIR

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 简单的日志回调函数
def logger_callback(category, status, message, **kwargs):
    print(f"[{category}] [{status}] {message}")

def test_font_setup():
    """测试字体设置是否正确"""
    print("\n" + "="*60)
    print("测试字体设置".center(60))
    print("="*60)
    
    # 1. 设置字体
    print("\n1. 调用 setup_matplotlib_fonts():")
    available_font = setup_matplotlib_fonts()
    print(f"   可用字体: {available_font}")
    
    # 2. 检查当前字体配置
    print("\n2. 当前字体配置:")
    print(f"   font.family: {plt.rcParams['font.family']}")
    print(f"   font.sans-serif: {plt.rcParams['font.sans-serif']}")
    print(f"   axes.unicode_minus: {plt.rcParams['axes.unicode_minus']}")
    
    # 3. 测试直接绘制中文文本
    print("\n3. 测试直接绘制中文文本:")
    fig, ax = plt.subplots(figsize=(6, 4), facecolor='black')
    ax.text(0.5, 0.5, '测试中文标题', ha='center', va='center', fontsize=16, color='white')
    ax.set_title('中文测试图', fontsize=14, color='white')
    ax.set_xlabel('X轴标签', color='white')
    ax.set_ylabel('Y轴标签', color='white')
    
    # 保存测试图
    test_path = os.path.join(OUTPUT_DIR, "font_direct_test.png")
    plt.savefig(test_path, bbox_inches='tight', facecolor='black', dpi=150)
    print(f"   ✅ 直接绘制中文测试图已保存: {test_path}")
    plt.close(fig)
    
    # 4. 检查系统可用字体
    print("\n4. 检查系统可用字体:")
    check_available_fonts()
    
    return True

def test_chart_generator():
    """测试ChartGenerator的字体使用"""
    print("\n" + "="*60)
    print("测试ChartGenerator字体使用".center(60))
    print("="*60)
    
    # 1. 创建ChartGenerator实例
    print("\n1. 创建ChartGenerator实例:")
    chart_gen = ChartGenerator(logger_callback)
    
    # 2. 测试绘制包含中文的折线图
    print("\n2. 测试绘制中文标题折线图:")
    
    # 创建测试数据
    import pandas as pd
    import numpy as np
    
    # 创建日期索引
    dates = pd.date_range(start='2023-01-01', periods=30)
    # 创建随机数据
    data1 = pd.Series(np.random.randn(30).cumsum(), index=dates)
    data2 = pd.Series(np.random.randn(30).cumsum(), index=dates)
    
    # 绘制测试图
    success = chart_gen.plot_line(
        {'数据1': data1, '数据2': data2},
        '中文标题测试图',
        ['数据1', '数据2'],
        ['#3498db', '#e74c3c'],
        save_path='font_chart_test.png'
    )
    
    if success:
        print("   ✅ ChartGenerator中文折线图测试成功")
    else:
        print("   ❌ ChartGenerator中文折线图测试失败")
    
    return success

def test_font_inheritance():
    """测试字体配置在不同组件间的继承"""
    print("\n" + "="*60)
    print("测试字体配置继承".center(60))
    print("="*60)
    
    # 1. 初始字体配置
    initial_font = plt.rcParams['font.sans-serif'][0]
    print(f"\n1. 初始字体: {initial_font}")
    
    # 2. 创建ChartGenerator
    print("\n2. 创建ChartGenerator后:")
    chart_gen = ChartGenerator(logger_callback)
    
    # 3. 检查创建后的字体配置
    after_font = plt.rcParams['font.sans-serif'][0]
    print(f"   字体: {after_font}")
    
    if initial_font == after_font:
        print("   ✅ 字体配置继承成功")
        return True
    else:
        print("   ❌ 字体配置继承失败")
        return False

def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("金融数据分析系统 - 字体修复测试".center(70))
    print("="*70)
    
    # 运行所有测试
    tests = [
        ("字体设置", test_font_setup),
        ("ChartGenerator", test_chart_generator),
        ("字体继承", test_font_inheritance)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 测试失败: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "="*60)
    print("测试结果汇总".center(60))
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总测试数: {len(results)}, 通过: {passed}, 失败: {len(results) - passed}")
    
    if passed == len(results):
        print("\n🎉 所有测试通过! 字体修复有效")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查字体配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())
