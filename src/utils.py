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

def log_execution(log, category, status, message, **kwargs):
    """
    记录执行日志
    :param log: 日志字典
    :param category: 日志类别
    :param status: 状态 (success/warning/error)
    :param message: 消息内容
    :param kwargs: 额外参数，如 chart_path
    """
    task = {
        'timestamp': datetime.now().isoformat(),
        'category': category,
        'status': status,
        'message': message
    }
    
    # ✅ 处理额外参数
    if 'chart_path' in kwargs:
        task['chart_path'] = kwargs['chart_path']
    
    log['tasks'].append(task)
    
    # 根据状态记录到不同列表
    if status == 'warning':
        log['warnings'].append(f"{category}: {message}")
    elif status == 'error':
        log['errors'].append(f"{category}: {message}")

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
from config import FONT_CANDIDATES

def setup_matplotlib_fonts():
    """设置matplotlib字体（增强版，确保配置持久化）"""
    # 使用config.py中定义的字体候选列表
    font_candidates = FONT_CANDIDATES
    
    available_font = None
    
    # 1. 首先检查simhei.ttf文件是否存在（GitHub Actions会下载到项目根目录）
    # 检查多个可能的位置
    possible_font_paths = [
        os.path.join(os.path.dirname(__file__), '../simhei.ttf'),  # 项目根目录
        os.path.join(os.path.expanduser('~'), '.local/share/fonts/simhei.ttf'),  # 用户字体目录
        'simhei.ttf'  # 当前目录
    ]
    
    simhei_path = None
    for path in possible_font_paths:
        if os.path.exists(path):
            simhei_path = path
            break
    
    if simhei_path:
        try:
            # 直接加载字体文件到fontManager
            fm.fontManager.addfont(simhei_path)
            # 立即强制设置字体配置
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['axes.unicode_minus'] = False
            
            # 测试能否创建文本
            fig = plt.figure(figsize=(1, 1))
            plt.text(0.5, 0.5, '测试中文', fontfamily='SimHei')
            plt.close(fig)
            available_font = 'SimHei'
            print(f"✅ 直接加载字体文件: simhei.ttf")
            print(f"📝 当前font.sans-serif: {plt.rcParams['font.sans-serif']}")
        except Exception as e:
            print(f"⚠️  加载simhei.ttf失败: {e}")
    else:
        print(f"⚠️  simhei.ttf文件不存在: {simhei_path}")
    
    # 如果直接加载失败，再尝试系统字体
    if not available_font:
        print(f"🔍 尝试从系统字体中查找: {font_candidates}")
        
        # 遍历字体候选列表，尝试找到可用的中文字体
        for font in font_candidates:
            try:
                # 立即设置字体配置
                plt.rcParams['font.sans-serif'] = [font]
                plt.rcParams['font.family'] = 'sans-serif'
                plt.rcParams['axes.unicode_minus'] = False
                
                # 测试能否创建文本
                fig = plt.figure(figsize=(1, 1))
                plt.text(0.5, 0.5, '测试中文', fontfamily=font)
                plt.close(fig)
                available_font = font
                print(f"✅ 使用系统字体: {font}")
                print(f"📝 当前font.sans-serif: {plt.rcParams['font.sans-serif']}")
                break
            except Exception as e:
                print(f"⚠️  测试字体 {font} 失败: {e}")
                continue
    
    if not available_font:
        print("⚠️  未找到中文字体，使用默认字体")
        available_font = 'sans-serif'
        plt.rcParams['font.sans-serif'] = [available_font]
    
    # 2. 强制设置所有字体相关配置，确保它们不会被覆盖
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': [available_font],
        'axes.unicode_minus': False
    })
    
    # 额外强制设置一次，确保字体配置不会被覆盖
    plt.rcParams['font.sans-serif'] = [available_font]
    
    # 3. 额外设置其他字体相关参数
    plt.rc('font', size=9)
    plt.rc('axes', titlesize=13, labelsize=10)
    plt.rc('xtick', labelsize=8)
    plt.rc('ytick', labelsize=8)
    plt.rc('legend', fontsize=8)
    plt.rc('figure', titlesize=14)
    
    # 4. 验证字体确实被使用
    test_text = "中文测试 123 ABC"
    fig, ax = plt.subplots(figsize=(3, 1), facecolor='black')
    text_obj = ax.text(0.5, 0.5, test_text, ha='center', va='center', fontsize=12, color='white')
    fig.canvas.draw()  # 强制渲染
    
    # 检查实际使用的字体
    used_font = text_obj.get_fontname()
    print(f"✅ 实际使用字体: {used_font}")
    print(f"📝 最终font.sans-serif: {plt.rcParams['font.sans-serif']}")
    print(f"📝 最终font.family: {plt.rcParams['font.family']}")
    
    plt.close(fig)
    
    return available_font

def check_available_fonts():
    """检查系统可用字体并生成测试图"""
    fonts = fm.findSystemFonts()
    chinese_fonts = [f for f in fonts if 'wqy' in f.lower() or 'noto' in f.lower() or 'cjk' in f.lower()]
    print(f"系统找到 {len(chinese_fonts)} 个中文字体:")
    for f in chinese_fonts[:3]:
        print(f"  - {os.path.basename(f)}")
    
    test_path = os.path.join(OUTPUT_DIR, "font_test.png")
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
