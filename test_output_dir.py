# -*- coding: utf-8 -*-
"""
测试脚本：验证图片是否真的保存到output目录
"""
import os
import sys
import matplotlib.pyplot as plt
from src.config import OUTPUT_DIR

print("=== 测试图片保存到output目录 ===")
print(f"当前工作目录: {os.getcwd()}")
print(f"OUTPUT_DIR: {OUTPUT_DIR}")

# 检查output目录是否存在
if os.path.exists(OUTPUT_DIR):
    print(f"✅ output目录存在: {OUTPUT_DIR}")
    # 列出output目录中的文件
    files = os.listdir(OUTPUT_DIR)
    print(f"output目录中的文件: {files}")
else:
    print(f"❌ output目录不存在: {OUTPUT_DIR}")

# 测试生成一个简单的图表并保存到output目录
try:
    print("\n=== 测试生成并保存图表 ===")
    # 创建一个简单的图表
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
    ax.set_title('测试图表')
    ax.set_xlabel('X轴')
    ax.set_ylabel('Y轴')
    
    # 保存到output目录
    test_filename = 'test_chart.png'
    test_path = os.path.join(OUTPUT_DIR, test_filename)
    plt.savefig(test_path)
    plt.close(fig)
    
    print(f"✅ 测试图表已生成: {test_filename}")
    print(f"✅ 完整路径: {test_path}")
    
    # 验证文件是否真的存在
    if os.path.exists(test_path):
        print(f"✅ 文件确实存在于output目录")
        # 检查文件大小
        file_size = os.path.getsize(test_path)
        print(f"✅ 文件大小: {file_size} bytes")
    else:
        print(f"❌ 文件不存在于output目录")
        
        # 检查当前目录是否有该文件
        current_dir_file = os.path.join(os.getcwd(), test_filename)
        if os.path.exists(current_dir_file):
            print(f"⚠️  文件保存在当前目录而不是output目录: {current_dir_file}")
        
        # 检查src目录是否有该文件
        src_dir_file = os.path.join(os.getcwd(), 'src', test_filename)
        if os.path.exists(src_dir_file):
            print(f"⚠️  文件保存在src目录而不是output目录: {src_dir_file}")
            
except Exception as e:
    print(f"❌ 测试生成图表失败: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试结束 ===")
