# -*- coding: utf-8 -*-
import os
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd 

# ==================== 路径配置 ====================
# 输出目录 - 指向主目录下的output文件夹
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 日志文件路径
LOG_PATH = os.path.join(OUTPUT_DIR, 'execution.log')

# ==================== 分析参数 ====================
# 数据周期
PERIOD_3MO = "3mo"
PERIOD_1MO = "1mo"
PERIOD_2MO = "2mo"

# 最小数据点
MIN_DATA_POINTS = 30
MIN_CORRELATION_POINTS = 50

# ==================== 指数配置 ====================
# 指数K线图列表：(ticker, 文件名, [周期])
INDICES = [
    ("^TNX", "tenbond.png"),          # 10年期国债
    ("^VIX", "vix.png", "2mo"),       # VIX恐慌指数
    ("^GSPC", "sp500.png"),           # 标普500
    ("^IXIC", "nasdaq.png"),          # 纳斯达克100
    ("^RUT", "rs2000.png"),           # 罗素2000
    ("VNQ", "vnq.png"),               # 房地产信托
    ("^N225", "nikkei225.png"),       # 日经225
    ("^HSI", "hsi.png"),              # 恒生指数
    ("CNY=X", "rmb.png")              # 人民币汇率
]

# ==================== 行业ETF映射 ====================
# 行业轮动分析用ETF
SECTOR_ETFS = {
    '美股科技': 'QQQ', '美股金融': 'XLF', '美股医药': 'XLV',
    '美股消费': 'XLY', '美股能源': 'XLE', '美股工业': 'XLI',
    #'A股科技': '515000.SH', 'A股医药': '512010.SH', 
    #'A股消费': '159928.SZ', 'A股金融': '512800.SH'
}

# ==================== 字体配置 ====================
# 中文字体候选列表
FONT_CANDIDATES = [
    'SimHei',               # 黑体（Windows默认）
    'WenQuanYi Micro Hei',  # CI环境可用字体
    'WenQuanYi Zen Hei',    # CI环境可用字体
    'Noto Sans CJK SC',     # CI环境可用字体
    'DejaVu Sans',          # 回退字体
]

# ==================== 可视化样式 ====================
# matplotlib样式配置
MPL_STYLE = {
    'figure.figsize': (12, 8), 'figure.dpi': 100, 'savefig.dpi': 150,
    'figure.facecolor': 'black', 'axes.facecolor': 'black', 
    'savefig.facecolor': 'black', 'savefig.transparent': False,
    'axes.labelcolor': 'white', 'xtick.color': 'white', 'ytick.color': 'white',
    'text.color': 'white', 'axes.titlecolor': 'white', 'legend.labelcolor': 'white',
    'font.family': 'sans-serif', 'font.size': 9, 'axes.titlesize': 13,
    'legend.fontsize': 8, 'xtick.labelsize': 8, 'ytick.labelsize': 8,
    'lines.linewidth': 1.5, 'lines.markersize': 4,
    'axes.prop_cycle': plt.cycler(color=['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6']),
    'axes.grid': True, 'grid.color': '#666666', 'grid.alpha': 0.5, 'grid.linestyle': '--',
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.spines.left': True, 'axes.spines.bottom': True,
    'xtick.direction': 'in', 'ytick.direction': 'in',
    'legend.frameon': True, 'legend.facecolor': '#333333',
    'legend.edgecolor': 'white', 'legend.framealpha': 0.8,
    'figure.subplot.left': 0.06, 'figure.subplot.right': 0.96,
    'figure.subplot.top': 0.94, 'figure.subplot.bottom': 0.08,
    'figure.subplot.wspace': 0.1, 'figure.subplot.hspace': 0.1,
    'axes.unicode_minus': False, 'figure.constrained_layout.use': False,
}

# ==================== 报告模板 ====================
MARKDOWN_TEMPLATE = """
# 📊 每日市场分析报告

**生成时间**: {timestamp}  
**数据来源**: yfinance, akshare, 新浪财经  
**分析周期**: 3个月滚动窗口  
**执行状态**: {status}

---

## 🎯 执行摘要

- **总任务数**: {total_tasks}
- **成功任务**: {success_tasks}
- **警告数量**: {warnings}
- **错误数量**: {errors}
- **生成图表**: {charts} 张
- **总耗时**: {duration}

---
"""

# ==================== API配置 ====================
# yfinance下载超时设置
YF_TIMEOUT = 30

# 请求头
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# ==================== 风险阈值 ====================
VIX_HIGH = 25
VIX_EXTREME = 35
VIX_LOW = 15

BOND_HIGH = 4.5
BOND_EXTREME = 5.0
BOND_LOW = 3.0

# ==================== 执行日志模板 ====================
EXECUTION_LOG = {
    'start_time': None,
    'end_time': None,
    'tasks': [],
    'errors': [],
    'warnings': [],
    'charts': [],
    'insights': [],
    'market_signals': {}
}
