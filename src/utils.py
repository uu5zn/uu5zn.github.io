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
    """设置matplotlib字体（增强版）"""
    available_font = None
    available_font_path = None
    
    # 直接查找系统中已安装的中文字体文件
    system_fonts = fm.findSystemFonts()
    
    # 优先匹配GitHub Actions中已安装的中文字体文件
    font_patterns = [
        r'wqy-microhei',   # WenQuanYi Micro Hei
        r'wqy-zenhei',     # WenQuanYi Zen Hei
        r'noto-cjk',       # Noto Sans CJK
        r'simhei',         # SimHei
        r'uming',          # uming
        r'ukai'            # ukai
    ]
    
    import re
    for font_file in system_fonts:
        font_path_lower = font_file.lower()
        for pattern in font_patterns:
            if re.search(pattern, font_path_lower):
                try:
                    # 直接获取字体名称（不依赖fontproperties）
                    font_name = os.path.basename(font_file)
                    print(f"🔍 发现中文字体文件: {font_name}")
                    
                    # 直接测试创建文本，使用fontpath
                    fig = plt.figure(figsize=(1, 1))
                    plt.text(0.5, 0.5, '测试中文', 
                            fontproperties=fm.FontProperties(fname=font_file),
                            fontsize=12)
                    plt.close(fig)
                    
                    available_font_path = font_file
                    # 提取字体名称，优先使用文件名（更可靠）
                    if 'wqy-microhei' in font_path_lower:
                        available_font = 'WenQuanYi Micro Hei'
                    elif 'wqy-zenhei' in font_path_lower:
                        available_font = 'WenQuanYi Zen Hei'
                    elif 'noto-cjk' in font_path_lower or 'noto' in font_path_lower:
                        available_font = 'Noto Sans CJK SC'
                    else:
                        available_font = font_name.split('.')[0]
                    
                    print(f"✅ 找到可用中文字体: {available_font} ({os.path.basename(font_file)})")
                    break
                except Exception as e:
                    print(f"⚠️  字体文件 {font_file} 加载失败: {e}")
                    continue
        if available_font:
            break
    
    if not available_font:
        # 如果没有找到指定字体，尝试使用系统默认的sans-serif字体
        print("⚠️  未找到中文字体，使用默认字体")
        available_font = 'sans-serif'
    
    # 强制设置所有字体相关配置
    # 注意：我们直接使用字体路径而非字体名称，确保matplotlib能找到字体
    font_config = {
        'font.family': 'sans-serif',
        'font.sans-serif': [available_font, 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK SC'],
        'font.size': 9,
        'axes.titlesize': 13,
        'axes.labelsize': 10,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'legend.fontsize': 8,
        'figure.titlesize': 14,
        'axes.unicode_minus': False,  # 正确显示负号
        'savefig.dpi': 150,
        'savefig.transparent': False,
        # 额外设置：确保所有文本元素都使用指定字体
        'mathtext.fontset': 'stixsans',
        'mathtext.default': 'regular',
    }
    
    # 应用字体配置
    plt.rcParams.update(font_config)
    
    # 关键修复：直接使用字体路径设置，不依赖字体名称
    if available_font_path:
        # 1. 将字体添加到fontManager
        fm.fontManager.addfont(available_font_path)
        print(f"✅ 字体已添加到Matplotlib: {available_font_path}")
        
        # 2. 确保字体被优先使用
        # 将字体路径作为第一个字体选项
        plt.rcParams['font.sans-serif'].insert(0, available_font_path)
        print(f"✅ 字体路径已添加到字体列表: {available_font_path}")
    
    # 3. 强制设置所有文本元素的默认字体
    # 创建一个全局字体属性对象
    global_font_props = fm.FontProperties(fname=available_font_path if available_font_path else available_font)
    
    # 验证字体确实被使用
    test_text = "中文测试 123 ABC"
    fig, ax = plt.subplots(figsize=(3, 1), facecolor='black')
    
    # 测试多种文本元素
    # 1. 标题
    ax.set_title("中文标题测试", fontproperties=global_font_props, fontsize=12, color='white')
    
    # 2. 轴标签
    ax.set_xlabel("中文X轴", fontproperties=global_font_props, color='white')
    ax.set_ylabel("中文Y轴", fontproperties=global_font_props, color='white')
    
    # 3. 文本
    text_obj = ax.text(0.5, 0.5, test_text, ha='center', va='center', 
                      fontsize=12, color='white',
                      fontproperties=global_font_props)
    
    # 4. 图例
    ax.plot([0, 1], [0, 1], label="中文图例", color='white')
    legend = ax.legend(fontsize=10)
    for text in legend.get_texts():
        text.set_fontproperties(global_font_props)
    
    # 5. 刻度标签
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(global_font_props)
    
    fig.canvas.draw()  # 强制渲染
    
    # 检查实际使用的字体
    used_font = text_obj.get_fontname()
    print(f"✅ 实际使用字体: {used_font}")
    
    # 检查字体列表
    print(f"✅ 当前字体列表: {plt.rcParams['font.sans-serif']}")
    
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
