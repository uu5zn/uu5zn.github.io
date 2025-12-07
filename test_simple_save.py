# -*- coding: utf-8 -*-
"""
简单测试脚本：生成一个图片并保存到output目录
"""
import os
import matplotlib.pyplot as plt
from src.config import OUTPUT_DIR

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"输出目录: {OUTPUT_DIR}")

# 创建一个简单的图表
plt.figure(figsize=(6, 4))
plt.plot([1, 2, 3, 4], [1, 4, 2, 3])
plt.title('简单测试图')
plt.xlabel('X轴')
plt.ylabel('Y轴')

# 保存图片到output目录
test_path = os.path.join(OUTPUT_DIR, 'simple_test.png')
plt.savefig(test_path, dpi=150, bbox_inches='tight')
plt.close()

# 验证图片是否保存成功
if os.path.exists(test_path):
    file_size = os.path.getsize(test_path)
    print(f"✅ 图片保存成功!")
    print(f"   文件路径: {test_path}")
    print(f"   文件大小: {file_size} 字节")
else:
    print(f"❌ 图片保存失败!")
    print(f"   文件路径: {test_path}")
    print(f"   目录内容: {os.listdir(OUTPUT_DIR)}")

# 查看当前目录结构
print(f"\n当前目录结构:")
os.system(f'dir "{OUTPUT_DIR}"')
