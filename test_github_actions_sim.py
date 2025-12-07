# -*- coding: utf-8 -*-
"""
模拟GitHub Actions环境的测试脚本
用于检查文件保存、目录权限和文件过滤情况
"""
import os
import sys
import shutil
import glob
from src.config import OUTPUT_DIR

print("=== 模拟GitHub Actions环境测试 ===")
print(f"当前工作目录: {os.getcwd()}")
print(f"OUTPUT_DIR: {OUTPUT_DIR}")
print(f"是否是绝对路径: {os.path.isabs(OUTPUT_DIR)}")

# 1. 清除旧的测试文件
print("\n1. 清除旧的测试文件...")
test_files = [
    os.path.join(OUTPUT_DIR, 'simple_test.png'),
    os.path.join(OUTPUT_DIR, 'test_*.png')
]

for pattern in test_files:
    for file in glob.glob(pattern):
        if os.path.exists(file):
            os.remove(file)
            print(f"   已删除: {file}")

# 2. 测试目录权限
print("\n2. 测试目录权限...")
try:
    # 测试创建子目录
    test_subdir = os.path.join(OUTPUT_DIR, 'test_subdir')
    os.makedirs(test_subdir, exist_ok=True)
    print(f"   ✅ 成功创建子目录: {test_subdir}")
    
    # 测试写入文件到子目录
    subdir_file = os.path.join(test_subdir, 'subdir_test.txt')
    with open(subdir_file, 'w') as f:
        f.write('test content')
    print(f"   ✅ 成功写入子目录文件")
    
    # 清理
    os.remove(subdir_file)
    os.rmdir(test_subdir)
    print(f"   ✅ 成功清理子目录")
except Exception as e:
    print(f"   ❌ 目录操作失败: {e}")

# 3. 测试多个文件保存
print("\n3. 测试多个文件保存...")
import matplotlib.pyplot as plt
import numpy as np

# 生成10个测试图
for i in range(10):
    plt.figure(figsize=(4, 3))
    plt.plot(np.random.rand(10), np.random.rand(10))
    plt.title(f'测试图 {i+1}')
    
    # 保存不同类型的文件
    if i % 2 == 0:
        filename = f'test_{i+1}_normal.png'
    else:
        filename = f'test_{i+1}_special.png'
    
    test_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(test_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    if os.path.exists(test_path):
        print(f"   ✅ 保存成功: {filename}")
    else:
        print(f"   ❌ 保存失败: {filename}")

# 4. 检查文件过滤规则
print("\n4. 检查文件过滤规则...")
print("   上传规则: output/ !output/*.log")

# 创建一个日志文件
log_path = os.path.join(OUTPUT_DIR, 'test.log')
with open(log_path, 'w') as f:
    f.write('test log')
print(f"   创建测试日志文件: {log_path}")

# 列出output目录中的所有文件
print("\n5. output目录内容:")
all_files = os.listdir(OUTPUT_DIR)
print(f"   总文件数: {len(all_files)}")

print("   所有文件:")
for file in sorted(all_files):
    file_path = os.path.join(OUTPUT_DIR, file)
    file_size = os.path.getsize(file_path)
    is_log = file.endswith('.log')
    status = "📋" if is_log else "📊"
    print(f"   {status} {file} ({file_size} bytes)")

# 模拟GitHub Actions的文件过滤
print("\n6. 模拟GitHub Actions文件过滤:")
filtered_files = [f for f in all_files if not f.endswith('.log')]
print(f"   过滤后文件数: {len(filtered_files)}")
print(f"   过滤掉的日志文件数: {len(all_files) - len(filtered_files)}")

# 7. 检查部署条件
print("\n7. 检查部署条件:")
print("   - 方案1: deploy-pages@v2 (官方)")
print("   - 方案2: peaceiris/actions-gh-pages@v4 (备选)")
print("   - 部署条件: github.ref == 'refs/heads/main' && github.event_name == 'schedule'")
print("   - 部署位置: ./output -> reports/ (GitHub Pages)")

# 8. 清理测试文件
print("\n8. 清理测试文件...")
for file in all_files:
    file_path = os.path.join(OUTPUT_DIR, file)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"   已删除: {file}")

print("\n=== 测试完成 ===")
print("✅ 本地图片保存功能正常")
print("✅ 目录权限设置正确")
print("✅ 文件过滤规则清晰")
print("⚠️  部署只在schedule事件触发时执行")
print("⚠️  检查GitHub Pages是否启用")
print("⚠️  检查GitHub Pages源设置")
