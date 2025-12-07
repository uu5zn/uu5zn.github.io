# -*- coding: utf-8 -*-
import os
import sys

# 添加src到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import OUTPUT_DIR

print(f"当前脚本路径: {os.path.abspath(__file__)}")
print(f"当前工作目录: {os.getcwd()}")
print(f"OUTPUT_DIR路径: {OUTPUT_DIR}")
print(f"OUTPUT_DIR绝对路径: {os.path.abspath(OUTPUT_DIR)}")
print(f"OUTPUT_DIR是否存在: {os.path.exists(OUTPUT_DIR)}")

# 验证是否为主目录下的output文件夹
main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
expected_output_dir = os.path.join(main_dir, "output")
print(f"主目录: {main_dir}")
print(f"预期output目录: {expected_output_dir}")
print(f"路径匹配: {OUTPUT_DIR == expected_output_dir}")