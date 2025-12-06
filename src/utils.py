# -*- coding: utf-8 -*-
import os
import sys
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

def setup_matplotlib_fonts():
    """设置matplotlib字体"""
    available_font = None
    for font in FONT_CANDIDATES:
        try:
            fig = plt.figure(figsize=(1, 1))
            plt.text(0.5, 0.5, '测试', fontfamily=font)
            plt.close(fig)
            available_font = font
            print(f"✅ 使用字体: {font}")
            break
        except:
            continue
    
    if not available_font:
        print("⚠️ 未找到中文字体，使用默认字体")
        available_font = 'sans-serif'
    
    # 更新字体配置
    mpl_config = MPL_STYLE.copy()
    mpl_config['font.sans-serif'] = [available_font]
    plt.rcParams.update(mpl_config)
    
    return available_font

def check_available_fonts():
    """检查系统可用字体并测试"""
    fonts = fm.findSystemFonts()
    chinese_fonts = [f for f in fonts if 'wqy' in f.lower() or 'noto' in f.lower() or 'cjk' in f.lower()]
    print(f"系统找到 {len(chinese_fonts)} 个中文字体:")
    for f in chinese_fonts[:3]:
        print(f"  - {os.path.basename(f)}")
    
    # 生成测试图
    test_path = os.path.join(OUTPUT_DIR, "font_test.png")
    try:
        fig, ax = plt.subplots(figsize=(4, 2), facecolor='black')
        ax.text(0.5, 0.5, '中文测试 123 ABC', ha='center', va='center', 
                fontsize=12, color='white', fontweight='bold')
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
