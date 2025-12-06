# -*- coding: utf-8 -*-
import os
import sys
import pandas as pd
import json
from datetime import datetime
from contextlib import redirect_stdout
from io import StringIO
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from config import OUTPUT_DIR, FONT_CANDIDATES, MPL_STYLE

def setup_logging():
    """初始化执行日志"""
    return {
        'start_time': None,
        'end_time': None,
        'tasks': [],
        'errors': [],
        'warnings': [],
        'charts': [],
        'insights': [],
        'market_signals': {}
    }

def log_execution(log_dict, task, status='success', details='', chart_path=None):
    """记录执行日志"""
    log_dict['tasks'].append({
        'task': task,
        'status': status,
        'details': details,
        'chart_path': chart_path,
        'timestamp': datetime.now().isoformat()
    })
    if status == 'error':
        log_dict['errors'].append(details)
    elif status == 'warning':
        log_dict['warnings'].append(details)

def capture_print(func, *args, **kwargs):
    """捕获函数的所有print输出"""
    buffer = StringIO()
    with redirect_stdout(buffer):
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            print(f"❌ 错误: {e}")
            result = None
            success = False
    
    output = buffer.getvalue()
    return success, result, output

# -*- coding: utf-8 -*-
import os
import sys
import json
from datetime import datetime
from contextlib import redirect_stdout
from io import StringIO
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

def setup_matplotlib_fonts():
    """设置matplotlib字体（增强版）"""
    # 优先使用的中文字体
    font_candidates = [
        'WenQuanYi Micro Hei',  # 文泉驿微米黑
        'WenQuanYi Zen Hei',    # 文泉驿正黑
        'Noto Sans CJK SC',     # Noto Sans CJK
        'Noto Sans SC',         # Noto Sans SC
        'SimHei',               # 黑体 (Windows)
        'Microsoft YaHei',      # 微软雅黑 (Windows)
        'DejaVu Sans',          # 回退字体
    ]
    
    available_font = None
    
    # 检查并验证每个字体
    for font in font_candidates:
        try:
            # 检查字体是否存在于系统中
            font_files = fm.findfont(font, fallback_to_default=False)
            if font_files:
                # 测试能否创建文本
                fig = plt.figure(figsize=(1, 1))
                plt.text(0.5, 0.5, '测试中文', fontfamily=font)
                plt.close(fig)
                available_font = font
                print(f"✅ 使用字体: {font}")
                break
        except:
            continue
    
    if not available_font:
        print("⚠️  未找到中文字体，使用默认字体")
        available_font = 'sans-serif'
    
    # 强制设置所有字体相关配置
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': [available_font],
        'axes.unicode_minus': False,  # 正确显示负号
        'font.size': 9,
        'axes.titlesize': 13,
        'axes.labelsize': 10,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'legend.fontsize': 8,
        'figure.titlesize': 14,
        # 确保中文文件名也能正确处理
        'savefig.dpi': 150,
        'savefig.transparent': False,
    })
    
    # 验证字体确实被使用
    test_text = "中文测试 123 ABC"
    fig, ax = plt.subplots(figsize=(3, 1), facecolor='black')
    text_obj = ax.text(0.5, 0.5, test_text, ha='center', va='center', fontsize=12, color='white')
    fig.canvas.draw()  # 强制渲染
    
    # 检查实际使用的字体
    used_font = text_obj.get_fontname()
    print(f"✅ 实际使用字体: {used_font}")
    
    plt.close(fig)
    
    return available_font

def check_available_fonts():
    """检查系统可用字体并生成测试图"""
    fonts = fm.findSystemFonts()
    chinese_fonts = [f for f in fonts if 'wqy' in f.lower() or 'noto' in f.lower() or 'cjk' in f.lower()]
    print(f"系统找到 {len(chinese_fonts)} 个中文字体:")
    for f in chinese_fonts[:3]:
        print(f"  - {os.path.basename(f)}")
    
    test_path = "output/font_test.png"
    try:
        fig, ax = plt.subplots(figsize=(4, 2), facecolor='black')
        ax.text(0.5, 0.5, '中文测试 123 ABC', ha='center', va='center', 
                fontsize=12, color='white')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        plt.tight_layout(pad=0.1)
        plt.savefig(test_path, bbox_inches='tight', facecolor='black', dpi=150)
        print(f"✅ 字体测试图已生成: {test_path}")
        plt.close(fig)
    except Exception as e:
        print(f"⚠️ 字体测试失败: {e}")
    
    return len(chinese_fonts) > 0

def validate_data(data, min_points=10):
    """验证数据有效性"""
    if data is None:
        return False
    if isinstance(data, pd.DataFrame):
        if data.empty or len(data) < min_points:
            return False
    elif isinstance(data, pd.Series):
        if data.empty or len(data) < min_points:
            return False
    elif hasattr(data, '__len__') and len(data) < min_points:
        return False
    return True

def normalize(data):
    """归一化处理"""
    try:
        if validate_data(data, 2):
            return (data - data.min()) / (data.max() - data.min())
    except:
        pass
    return pd.Series(dtype=float)

def calculate_percentile(series, value):
    """计算百分位"""
    try:
        return (series <= value).sum() / len(series) * 100
    except:
        return 0

def format_date(date_str, fmt='%Y%m%d'):
    """转换日期格式"""
    try:
        return datetime.strptime(date_str, fmt)
    except:
        return datetime.now()

def get_date_range(days=300):
    """获取日期范围"""
    end = datetime.now()
    start = end - timedelta(days=days)
    return start.strftime('%Y%m%d'), end.strftime('%Y%m%d')
