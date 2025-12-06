# -*- coding: utf-8 -*-
import mplfinance as mpf
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
import warnings
import os
import sys
import requests
from io import StringIO
from tqdm import tqdm
from bs4 import BeautifulSoup
import numpy as np
import time
import json

warnings.filterwarnings('ignore')

# 创建输出目录
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 执行日志
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

def log_execution(task, status='success', details='', chart_path=None):
    """记录执行日志"""
    EXECUTION_LOG['tasks'].append({
        'task': task,
        'status': status,
        'details': details,
        'chart_path': chart_path,
        'timestamp': datetime.now().isoformat()
    })
    if status == 'error':
        EXECUTION_LOG['errors'].append(details)
    elif status == 'warning':
        EXECUTION_LOG['warnings'].append(details)

def save_execution_report():
    """保存执行报告"""
    report_path = os.path.join(OUTPUT_DIR, '执行报告.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(EXECUTION_LOG, f, ensure_ascii=False, indent=2)
    print(f"\n📋 执行报告已保存: {report_path}")

def generate_markdown_report():
    """生成Markdown格式的综合报告"""
    print("\n" + "📝 生成Markdown报告".center(70, "="))
    
    report_path = os.path.join(OUTPUT_DIR, '市场分析报告.md')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"""# 📊 每日市场分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**数据来源**: yfinance, akshare, 新浪财经  
**分析周期**: 3个月滚动窗口  
**执行状态**: {'✅ 全部成功' if len(EXECUTION_LOG['errors']) == 0 else '⚠️ 部分失败'}

---

## 🎯 执行摘要

- **总任务数**: {len(EXECUTION_LOG['tasks'])}
- **成功任务**: {len([t for t in EXECUTION_LOG['tasks'] if t['status'] == 'success'])}
- **警告数量**: {len(EXECUTION_LOG['warnings'])}
- **错误数量**: {len(EXECUTION_LOG['errors'])}
- **生成图表**: {len([t for t in EXECUTION_LOG['tasks'] if t['chart_path']])} 张
- **总耗时**: {EXECUTION_LOG.get('total_time', 'N/A')}

---

## 💡 核心市场洞察
""")

        # 提取关键洞察
        for category, insight in EXECUTION_LOG['insights']:
            f.write(f"\n### {category}\n")
            f.write(f"{insight}\n")

        f.write("""
---

## 📈 图表分析
""")

        # 图表展示部分
        chart_sections = [
            ("### 🔷 全球核心指数", [
                ('sp500.png', '标普500指数'),
                ('nasdaq.png', '纳斯达克100指数'),
                ('rs2000.png', '罗素2000小盘股'),
                ('hsi.png', '恒生指数'),
                ('rmb.png', '人民币汇率')
            ]),
            ("### 🔷 风险与利率指标", [
                ('tenbond.png', '美国10年期国债收益率'),
                ('vix.png', 'VIX恐慌指数'),
                ('jyb_gz.png', '油金比 vs 美债收益率')
            ]),
            ("### 🔷 中国市场流动性", [
                ('rongziyue_ma.png', '融资余额与10日均线'),
                ('rongziyue_1.png', '多指标归一化对比'),
                ('rongziyue_2.png', '融资余额与ETF对比'),
                ('liudongxing.png', '流动性指标')
            ]),
            ("### 🔷 股债性价比分析", [
                ('guzhaixicha.png', '上证50股债利差'),
                ('hsi_rut_comparison.png', '恒生指数 vs Russell 2000')
            ])
        ]
        
        for section_title, charts in chart_sections:
            f.write(f"\n{section_title}\n")
            for chart_file, title in charts:
                if os.path.exists(os.path.join(OUTPUT_DIR, chart_file)):
                    f.write(f"""
#### {title}
![{title}](./{chart_file})

""")
                else:
                    f.write(f"#### {title}\n❌ 图表生成失败\n\n")

        f.write("""

---

## 💼 资产配置建议

### 股票/债券/现金配置比例
| 资产类别 | 建议比例 | 说明 |
|----------|----------|------|
| **股票** | 50% | 根据风险环境动态调整 |
| **债券** | 40% | 作为稳定器，对冲风险 |
| **现金** | 10% | 保持机动性 |

---

## ⚠️  风险警示

### 当前需重点关注的风险
""")
        # 从日志中提取风险
        for warning in EXECUTION_LOG['warnings']:
            f.write(f"- {warning}\n")
        
        if len(EXECUTION_LOG['warnings']) == 0:
            f.write("- 暂无显著系统性风险\n")

        f.write("""
---

*本报告由GitHub Actions自动生成于 {}*  
*版本: v1.0 | 算法更新: 2024-12*  
*免责声明: 报告仅供参考，不构成投资建议。*
""".format(datetime.now().strftime('%Y-%m-%d %H:%M')))

    print(f"✅ Markdown报告已生成: {report_path}")
    log_execution('Markdown报告', 'success', f'报告路径: {report_path}', '市场分析报告.md')

def check_available_fonts():
    """检查系统可用字体"""
    import matplotlib.font_manager as fm
    fonts = fm.findSystemFonts()
    chinese_fonts = [f for f in fonts if 'wqy' in f.lower() or 'noto' in f.lower() or 'cjk' in f.lower()]
    print(f"系统找到 {len(chinese_fonts)} 个中文字体:")
    for f in chinese_fonts[:3]:
        print(f"  - {os.path.basename(f)}")
    log_execution('字体检查', 'success', f'找到 {len(chinese_fonts)} 个中文字体')
    return len(chinese_fonts) > 0

def setup_matplotlib_fonts():
    """设置matplotlib字体（服务器环境优化）"""
    font_candidates = [
        'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 
        'Noto Sans CJK SC', 'Noto Sans SC', 'DejaVu Sans',
    ]
    
    available_font = None
    for font in font_candidates:
        try:
            fig = plt.figure(figsize=(1, 1))
            plt.text(0.5, 0.5, '测试', fontfamily=font)
            plt.close(fig)
            available_font = font
            print(f"✅ 使用字体: {font}")
            log_execution('字体设置', 'success', f'使用字体: {font}')
            break
        except:
            continue
    
    if not available_font:
        print("⚠️  未找到中文字体，使用默认字体")
        available_font = 'sans-serif'
        log_execution('字体设置', 'warning', '未找到中文字体')
    
    plt.rcParams.update({
        'figure.figsize': (12, 8), 'figure.dpi': 100, 'savefig.dpi': 150,
        'figure.facecolor': 'black', 'axes.facecolor': 'black', 
        'savefig.facecolor': 'black', 'savefig.transparent': False,
        'axes.labelcolor': 'white', 'xtick.color': 'white', 'ytick.color': 'white',
        'text.color': 'white', 'axes.titlecolor': 'white', 'legend.labelcolor': 'white',
        'font.family': 'sans-serif', 'font.sans-serif': [available_font],
        'font.size': 9, 'axes.titlesize': 13, 'legend.fontsize': 8,
        'xtick.labelsize': 8, 'ytick.labelsize': 8,
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
    })

setup_matplotlib_fonts()
check_available_fonts()

def fix_currency_boc_sina(symbol: str = "美元", start_date: str = "20230304", end_date: str = "20231110") -> pd.DataFrame:
    """修复版新浪财经-中行人民币牌价数据"""
    url = "http://biz.finance.sina.com.cn/forex/forex.php"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        params = {
            "startdate": "-".join([start_date[:4], start_date[4:6], start_date[6:]]),
            "enddate": "-".join([end_date[:4], end_date[4:6], end_date[6:]]),
            "money_code": "EUR", "type": "0",
        }
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.encoding = "gbk"
        soup = BeautifulSoup(r.text, "lxml")
        
        money_code_element = soup.find(attrs={"id": "money_code"})
        if money_code_element is None:
            log_execution('汇率数据', 'warning', '无法获取货币代码映射')
            return pd.DataFrame()
        
        data_dict = dict(
            zip(
                [item.text for item in money_code_element.find_all("option")],
                [item["value"] for item in money_code_element.find_all("option")]
            )
        )
        
        if symbol not in data_dict:
            log_execution('汇率数据', 'warning', f'不支持的货币: {symbol}')
            return pd.DataFrame()
        
        money_code = data_dict[symbol]
        params = {
            "money_code": money_code, "type": "0",
            "startdate": "-".join([start_date[:4], start_date[4:6], start_date[6:]]),
            "enddate": "-".join([end_date[:4], end_date[4:6], end_date[6:]]),
            "page": "1", "call_type": "ajax",
        }
        
        big_df = pd.DataFrame()
        r = requests.get(url, params=params, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        page_element_list = soup.find_all("a", attrs={"class": "page"})
        page_num = int(page_element_list[-2].text) if len(page_element_list) != 0 else 1
        
        for page in tqdm(range(1, page_num + 1), leave=False, desc=f"获取{symbol}数据"):
            params.update({"page": page})
            r = requests.get(url, params=params, headers=headers, timeout=10)
            temp_df = pd.read_html(StringIO(r.text), header=0)[0]
            big_df = pd.concat([big_df, temp_df], ignore_index=True)
        
        if len(big_df.columns) == 6:
            big_df.columns = ["日期", "中行汇买价", "中行钞买价", "中行钞卖价", "中行汇卖价", "央行中间价"]
        elif len(big_df.columns) == 5:
            big_df.columns = ["日期", "中行汇买价", "中行钞买价", "中行钞卖价/汇卖价", "央行中间价"]
        else:
            log_execution('汇率数据', 'warning', f'未知列数: {len(big_df.columns)}')
            return pd.DataFrame()
        
        big_df["日期"] = pd.to_datetime(big_df["日期"], errors="coerce").dt.date
        for col in big_df.columns[1:]:
            big_df[col] = pd.to_numeric(big_df[col], errors="coerce")
        
        big_df.sort_values(by=["日期"], inplace=True, ignore_index=True)
        log_execution('汇率数据', 'success', f'获取 {len(big_df)} 条记录')
        return big_df
    except Exception as e:
        log_execution('汇率数据', 'error', str(e))
        return pd.DataFrame()

def safe_get_data(func, *args, **kwargs):
    """安全获取数据"""
    try:
        data = func(*args, **kwargs)
        if data is None or (hasattr(data, 'empty') and data.empty):
            return pd.DataFrame()
        return data
    except Exception as e:
        log_execution('数据获取', 'warning', f'{func.__name__}: {str(e)[:100]}')
        return pd.DataFrame()

def validate_data(data, min_points=10):
    """验证数据有效性"""
    # 修复: 正确处理DataFrame和Series的判断
    if data is None:
        return False
    if isinstance(data, (pd.DataFrame, pd.Series)):
        if data.empty or len(data) < min_points:
            return False
    elif hasattr(data, '__len__') and len(data) < min_points:
        return False
    return True

def generate_and_save_plot(ticker, filename, period="1mo"):
    """生成K线图"""
    try:
        data = yf.Ticker(ticker).history(period=period)
        if validate_data(data, 5):
            filepath = os.path.join(OUTPUT_DIR, filename)
            style = mpf.make_mpf_style(
                base_mpf_style='charles',
                marketcolors=mpf.make_marketcolors(up='#e74c3c', down='#2ecc71', edge='inherit'),
                facecolor='black', edgecolor='white', figcolor='black',
                gridcolor='#666666', gridstyle='--', rc={'font.size': 8}
            )
            
            mpf.plot(
                data, type='candle', figscale=0.35, volume=False,
                savefig=filepath, datetime_format='%m-%d', style=style,
                title=ticker, tight_layout=True,
                warn_too_much_data=1000
            )
            print(f"✅ K线图: {filename}")
            log_execution('K线图', 'success', f'{ticker} -> {filename}', chart_path=filename)
        else:
            print(f"❌ 数据不足: {ticker}")
            log_execution('K线图', 'warning', f'{ticker} 数据不足')
    except Exception as e:
        print(f"❌ K线图失败 {ticker}: {e}")
        log_execution('K线图', 'error', f'{ticker}: {str(e)}')

def get_data(symbol, start_date, end_date):
    """获取数据"""
    try:
        if symbol == '美元':
            data = fix_currency_boc_sina(symbol=symbol, start_date=start_date, end_date=end_date)
            if not data.empty and '央行中间价' in data.columns:
                return data.set_index("日期")['央行中间价']
        
        elif symbol == '融资余额':
            data = safe_get_data(ak.stock_margin_sse, start_date=start_date, end_date=end_date)
            if not data.empty and len(data.columns) >= 2:
                data = data.iloc[:, [0, 1]].iloc[::-1]
                data['信用交易日期'] = pd.to_datetime(data['信用交易日期'], errors='coerce', format='%Y%m%d')
                return data.dropna().set_index('信用交易日期')
        
        elif symbol == 'Shibor 1M':
            data = safe_get_data(ak.macro_china_shibor_all)
            if not data.empty and '日期' in data.columns and '1M-定价' in data.columns:
                data['日期'] = pd.to_datetime(data['日期'], errors='coerce')
                return data.dropna().set_index('日期')['1M-定价']
        
        elif symbol == '中美国债收益率':
            data = safe_get_data(ak.bond_zh_us_rate)
            if not data.empty and '日期' in data.columns:
                data['日期'] = pd.to_datetime(data['日期'], errors='coerce')
                data = data.dropna().set_index('日期')
                data = data.ffill(axis=0)
                if '中国国债收益率10年' in data.columns and '美国国债收益率10年' in data.columns:
                    data['spread'] = data['中国国债收益率10年'] - data['美国国债收益率10年']
                    return data
        
        elif symbol.startswith('ETF_'):
            etf_code = symbol.split('_')[1]
            data = safe_get_data(ak.fund_etf_hist_em, symbol=etf_code)
            if not data.empty and '日期' in data.columns and '收盘' in data.columns:
                data = data.iloc[-220:] if len(data) > 220 else data
                data['日期'] = pd.to_datetime(data['日期'], errors='coerce')
                return data.dropna().set_index('日期')['收盘']
        
        elif symbol in ['CL', 'GC']:
            data = safe_get_data(ak.futures_foreign_hist, symbol=symbol)
            if not data.empty and 'date' in data.columns and 'close' in data.columns:
                return data.set_index('date')['close']
        
        elif symbol == 'US_BOND':
            data = safe_get_data(ak.bond_zh_us_rate)
            if not data.empty and '日期' in data.columns and '美国国债收益率10年' in data.columns:
                bond_df = data.copy()
                bond_df['日期'] = pd.to_datetime(bond_df['日期'], errors='coerce')
                us_bond = bond_df.dropna().sort_values('日期').set_index('日期')
                return us_bond['美国国债收益率10年'].ffill()
    except Exception as e:
        log_execution('数据处理', 'error', f'{symbol}: {str(e)}')
    
    return pd.Series(dtype=float)

def normalize(data):
    """归一化处理"""
    try:
        if validate_data(data, 2):
            return (data - data.min()) / (data.max() - data.min())
    except:
        pass
    return pd.Series(dtype=float)

def calculate_trend(series, period=10):
    """计算趋势方向"""
    if not validate_data(series, period * 2):
        return 'unknown'
    recent = series.iloc[-period:].mean()
    previous = series.iloc[-period*2:-period].mean()
    return 'up' if recent > previous else 'down'

def analyze_index_divergence():
    """分析指数差异（纳指、标普、罗素2000）"""
    print("\n" + "="*70)
    print("【市场结构解读】")
    print("="*70)
    
    try:
        nasdaq = yf.download('^IXIC', period='3mo', interval='1d', progress=False)['Close']
        sp500 = yf.download('^GSPC', period='3mo', interval='1d', progress=False)['Close']
        russell = yf.download('^RUT', period='3mo', interval='1d', progress=False)['Close']
        
        # 修复: 正确处理DataFrame验证
        if not (validate_data(nasdaq, 30) and validate_data(sp500, 30) and validate_data(russell, 30)):
            print("⚠️  指数数据不足，无法分析")
            log_execution('指数差异分析', 'warning', '数据不足')
            return
        
        # 计算收益率
        nasdaq_ret = (nasdaq.iloc[-1] / nasdaq.iloc[-30] - 1) * 100
        sp500_ret = (sp500.iloc[-1] / sp500.iloc[-30] - 1) * 100
        russell_ret = (russell.iloc[-1] / russell.iloc[-30] - 1) * 100
        
        # 计算波动性
        nasdaq_vol = nasdaq.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
        sp500_vol = sp500.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
        russell_vol = russell.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
        
        # 计算相关性
        df = pd.concat([
            nasdaq.pct_change().dropna(),
            sp500.pct_change().dropna(),
            russell.pct_change().dropna()
        ], axis=1, keys=['纳指', '标普', '罗素']).dropna()
        
        corr_nasdaq_sp500 = df['纳指'].corr(df['标普'])
        corr_nasdaq_russell = df['纳指'].corr(df['罗素'])
        corr_sp500_russell = df['标普'].corr(df['罗素'])
        
        print(f"\n📊 近30日涨跌幅:")
        print(f"  纳斯达克100: {nasdaq_ret:+.2f}% (波动率: {nasdaq_vol:.1f}%)")
        print(f"  标普500:     {sp500_ret:+.2f}% (波动率: {sp500_vol:.1f}%)")
        print(f"  罗素2000:    {russell_ret:+.2f}% (波动率: {russell_vol:.1f}%)")
        
        print(f"\n🔗 日收益率相关性:")
        print(f"  纳指-标普:   {corr_nasdaq_sp500:.3f}")
        print(f"  纳指-罗素:   {corr_nasdaq_russell:.3f}")
        print(f"  标普-罗素:   {corr_sp500_russell:.3f}")
        
        # 趋势分析
        nasdaq_trend = calculate_trend(nasdaq)
        sp500_trend = calculate_trend(sp500)
        russell_trend = calculate_trend(russell)
        
        print(f"\n📈 近期趋势:")
        print(f"  纳指: {'上涨' if nasdaq_trend == 'up' else '下跌'}趋势")
        print(f"  标普: {'上涨' if sp500_trend == 'up' else '下跌'}趋势")
        print(f"  罗素: {'上涨' if russell_trend == 'up' else '下跌'}趋势")
        
        # 解读市场风格
        if nasdaq_ret > sp500_ret > russell_ret:
            style_signal = "🔼 科技股主导，大盘蓝筹跟随，小盘股落后 → 典型的风险偏好上升，集中追逐成长性"
            market_regime = "成长风格"
        elif russell_ret > sp500_ret > nasdaq_ret:
            style_signal = "🔽 小盘股领涨，价值周期风格占优，科技股落后 → 经济复苏预期或通胀交易"
            market_regime = "价值风格"
        elif abs(nasdaq_ret - sp500_ret) < 2 and abs(sp500_ret - russell_ret) < 2:
            style_signal = "➡️  全面上涨/下跌，缺乏明显风格 → 流动性驱动或系统性风险"
            market_regime = "普涨普跌"
        elif nasdaq_ret < 0 and sp500_ret < 0 and russell_ret < 0:
            style_signal = "🔴 全面下跌，风险规避 → 关注VIX和避险资产"
            market_regime = "风险规避"
        else:
            style_signal = "🔄 风格轮动，结构分化 → 关注行业/个股机会"
            market_regime = "结构分化"
        
        print(f"\n💡 风格解读: {style_signal}")
        
        # 波动性解读
        avg_vol = np.mean([nasdaq_vol, sp500_vol, russell_vol])
        if russell_vol > avg_vol * 1.2:
            print("⚠️  小盘股波动率异常放大 → 市场不确定性集中在小盘")
        
        # 相关性解读
        if corr_nasdaq_russell < 0.6:
            print("⚠️  纳指与罗素相关性显著下降 → 大小盘走势分化，市场结构不健康")
        
        # 记录洞察
        insight_msg = f"纳指{nasdaq_ret:+.2f}% 标普{sp500_ret:+.2f}% 罗素{russell_ret:+.2f}% {market_regime}"
        EXECUTION_LOG['insights'].append(('指数差异', insight_msg))
        
    except Exception as e:
        print(f"❌ 指数差异分析失败: {e}")
        log_execution('指数差异分析', 'error', str(e))

def analyze_risk_regime():
    """分析风险环境（国债+VIX）"""
    print("\n" + "="*70)
    print("【风险环境解读】")
    print("="*70)
    
    try:
        vix = yf.download('^VIX', period='3mo', interval='1d', progress=False)['Close']
        ten_year = yf.download('^TNX', period='3mo', interval='1d', progress=False)['Close']
        sp500 = yf.download('^GSPC', period='3mo', interval='1d', progress=False)['Close']
        
        if not (validate_data(vix, 30) and validate_data(ten_year, 30) and validate_data(sp500, 30)):
            print("⚠️  风险指标数据不足")
            log_execution('风险环境分析', 'warning', '数据不足')
            return
        
        # 修复: 确保转换为标量
        current_vix = float(vix.iloc[-1]) if len(vix) > 0 else 0
        current_bond = float(ten_year.iloc[-1]) if len(ten_year) > 0 else 0
        vix_change = (vix.iloc[-1] / vix.iloc[-5] - 1) * 100 if len(vix) > 5 else 0
        bond_change = (ten_year.iloc[-1] / ten_year.iloc[-5] - 1) * 100 if len(ten_year) > 5 else 0
        
        # 历史分位数
        vix_percentile = (vix <= current_vix).sum() / len(vix) * 100 if len(vix) > 0 else 0
        bond_percentile = (ten_year <= current_bond).sum() / len(ten_year) * 100 if len(ten_year) > 0 else 0
        
        print(f"\n📊 当前风险指标:")
        print(f"  VIX:        {current_vix:.2f} ({vix_percentile:.0f}分位) 5日变化: {vix_change:+.2f}%")
        print(f"  10Y国债:    {current_bond:.2f}% ({bond_percentile:.0f}分位) 5日变化: {bond_change:+.2f}%")
        
        # VIX解读
        if current_vix > 35:
            vix_signal = "🚨 恐慌极值区，市场极度避险"
        elif current_vix > 25:
            vix_signal = "⚠️  恐慌升温区，风险偏好下降"
        elif current_vix < 15:
            vix_signal = "😌 恐慌低迷区，市场过度乐观"
        else:
            vix_signal = "✅ 正常波动区"
        print(f"\n🎯 VIX解读: {vix_signal}")
        
        # 国债收益率解读
        if current_bond > 5.0:
            bond_signal = "📈 极高利率区，严重压制资产估值"
        elif current_bond > 4.0:
            bond_signal = "📊 高利率区，不利长久期资产"
        elif current_bond < 2.5:
            bond_signal = "📉 极低利率区，资产估值泡沫化"
        elif current_bond < 3.5:
            bond_signal = "📉 低利率区，利好成长股"
        else:
            bond_signal = "🔄 利率中性区"
        print(f"🎯 国债解读: {bond_signal}")
        
        # 趋势判断
        vix_trend = calculate_trend(vix)
        bond_trend = calculate_trend(ten_year)
        print(f"\n📈 近期趋势:")
        print(f"  VIX: 五日{'上升' if vix_trend == 'up' else '下降'} ({vix_change:+.2f}%)")
        print(f"  国债: 五日{'上升' if bond_trend == 'up' else '下降'} ({bond_change:+.2f}%)")
        
        # 股债相关性
        recent_corr = sp500.pct_change().iloc[-30:].corr(ten_year.diff().iloc[-30:])
        print(f"\n🔗 股债30日相关性: {recent_corr:.3f}")
        if recent_corr > 0.3:
            corr_signal = "正相关 → 传统股债配置失效，宏观驱动主导"
        elif recent_corr < -0.3:
            corr_signal = "负相关 → 分散化有效，对冲功能正常"
        else:
            corr_signal = "弱相关 → 独立驱动因素"
        print(f"💡 相关性解读: {corr_signal}")
        
        # 综合风险评分
        risk_score = 0
        if current_vix > 25: risk_score += 2
        elif current_vix < 15: risk_score -= 1
        
        if current_bond > 4.5: risk_score += 1
        elif current_bond < 3.0: risk_score -= 1
        
        if vix_trend == 'up': risk_score += 1
        
        print(f"\n🌡️  综合风险评分: {risk_score}/4")
        if risk_score >= 3:
            risk_level = "🔴 高风险"
            action = "降低权益仓位，买入VIX看涨期权，增加现金/黄金"
        elif risk_score >= 1:
            risk_level = "🟡 中风险"
            action = "保持中性仓位，对冲尾部风险"
        elif risk_score <= -1:
            risk_level = "🟢 低风险"
            action = "增加风险敞口，卖出看跌期权，加杠杆"
        else:
            risk_level = "⚪ 中等风险"
            action = "平衡配置，动态调整"
        
        print(f"🎯 风险等级: {risk_level}")
        print(f"💼 建议操作: {action}")
        
        # 记录洞察
        EXECUTION_LOG['market_signals']['risk_level'] = risk_level
        EXECUTION_LOG['insights'].append(('风险环境', f'VIX{current_vix:.2f} 国债{current_bond:.2f}% {risk_level}'))
        
    except Exception as e:
        print(f"❌ 风险环境分析失败: {e}")
        log_execution('风险环境分析', 'error', str(e))

def analyze_china_us_linkage():
    """分析中美市场联动"""
    print("\n" + "="*70)
    print("【中美市场联动解读】")
    print("="*70)
    
    try:
        hsi = yf.download('^HSI', period='3mo', interval='1d', progress=False)['Close']
        usdcny = yf.download('CNY=X', period='3mo', interval='1d', progress=False)['Close']
        sp500 = yf.download('^GSPC', period='3mo', interval='1d', progress=False)['Close']
        
        if not (validate_data(hsi, 30) and validate_data(usdcny, 30) and validate_data(sp500, 30)):
            print("⚠️  中美市场数据不足")
            log_execution('中美联动分析', 'warning', '数据不足')
            return
        
        # 修复: 确保转换为标量
        current_cny = float(usdcny.iloc[-1]) if len(usdcny) > 0 else 0
        cny_change_5d = (usdcny.iloc[-1] / usdcny.iloc[-5] - 1) * 100 if len(usdcny) > 5 else 0
        cny_change_30d = (usdcny.iloc[-1] / usdcny.iloc[-30] - 1) * 100 if len(usdcny) > 30 else 0
        
        hsi_ret = (hsi.iloc[-1] / hsi.iloc[-30] - 1) * 100 if len(hsi) > 30 else 0
        sp500_ret = (sp500.iloc[-1] / sp500.iloc[-30] - 1) * 100 if len(sp500) > 30 else 0
        
        print(f"\n📊 市场表现 (30日):")
        print(f"  恒生指数:    {hsi_ret:+.2f}%")
        print(f"  标普500:     {sp500_ret:+.2f}%")
        print(f"  人民币汇率:  {current_cny:.4f} (5日: {cny_change_5d:+.2f}%, 30日: {cny_change_30d:+.2f}%)")
        
        # 汇率解读
        if cny_change_5d > 0.5:
            cny_signal = "📉 快速贬值 → 资本外流压力，港股承压"
            cny_regime = "贬值压力"
        elif cny_change_5d < -0.5:
            cny_signal = "📈 快速升值 → 外资流入，港股受益"
            cny_regime = "升值趋势"
        else:
            cny_signal = "🔄 相对稳定 → 汇率不是主要矛盾"
            cny_regime = "平稳"
        print(f"\n🎯 汇率信号: {cny_signal}")
        
        # 计算相关性
        df = pd.concat([
            hsi.pct_change().dropna(),
            usdcny.pct_change().dropna(),
            sp500.pct_change().dropna()
        ], axis=1, keys=['恒指', '人民币', '标普']).dropna()
        
        corr_hsi_sp500 = df['恒指'].corr(df['标普'])
        corr_hsi_cny = df['恒指'].corr(-df['人民币'])  # 贬值应利好港股
        corr_sp500_cny = df['标普'].corr(-df['人民币'])
        
        print(f"\n🔗 相关性分析:")
        print(f"  恒指-标普:   {corr_hsi_sp500:.3f} {'🔒强联动' if corr_hsi_sp500 > 0.7 else '🔓弱联动' if corr_hsi_sp500 < 0.3 else '🔄中等'}")
        print(f"  恒指-人民币: {corr_hsi_cny:.3f} ({'✅正常' if corr_hsi_cny > 0 else '⚠️异常'})")
        print(f"  标普-人民币: {corr_sp500_cny:.3f}")
        
        # 联动性解读
        if corr_hsi_sp500 > 0.7:
            linkage = "🔒 强联动"
            linkage_desc = "港股完全跟随美股，基本面独立定价弱"
        elif corr_hsi_sp500 < 0.3:
            linkage = "🔓 弱联动"
            linkage_desc = "港股独立行情，受A股或政策影响更大"
        else:
            linkage = "🔄 中等联动"
            linkage_desc = "混合影响，需关注美股但不可完全参照"
        print(f"\n🎯 联动强度: {linkage}")
        print(f"💡 解读: {linkage_desc}")
        
        # 相对强弱
        relative_strength = hsi_ret - sp500_ret
        strength_threshold = 5
        
        if relative_strength > strength_threshold:
            strength_signal = "💪 港股显著跑赢"
            strength_reason = "可能原因: 估值修复、政策利好、南向资金流入"
        elif relative_strength < -strength_threshold:
            strength_signal = "😞 港股显著跑输"
            strength_reason = "可能原因: 汇率贬值、监管担忧、外资流出"
        else:
            strength_signal = "🤝 基本同步"
            strength_reason = "港股与美股相关性主导"
        
        print(f"\n📈 相对强弱: {strength_signal} (差值: {relative_strength:+.2f}%)")
        print(f"💡 原因推断: {strength_reason}")
        
        # 记录洞察
        EXECUTION_LOG['insights'].append(('中美联动', f'恒指{hsi_ret:+.2f}% 汇率{cny_change_5d:+.2f}% {linkage}'))
        
    except Exception as e:
        print(f"❌ 中美联动分析失败: {e}")
        log_execution('中美联动分析', 'error', str(e))

def analyze_liquidity_conditions():
    """分析流动性环境"""
    print("\n" + "="*70)
    print("【流动性环境解读】")
    print("="*70)
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=300)
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        
        margin_data = get_data('融资余额', start_date_str, end_date_str)
        shibor_data = get_data('Shibor 1M', start_date_str, end_date_str)
        bond_data = get_data('中美国债收益率', start_date_str, end_date_str)
        
        if not (validate_data(margin_data, 50) and validate_data(shibor_data, 30)):
            print("⚠️  流动性数据不足")
            log_execution('流动性分析', 'warning', '数据不足')
            return
        
        current_margin = float(margin_data['融资余额'].iloc[-1]) / 100000000
        margin_change_5d = margin_data['融资余额'].pct_change(5).iloc[-1] * 100
        margin_change_30d = margin_data['融资余额'].pct_change(30).iloc[-1] * 100
        
        current_shibor = float(shibor_data.iloc[-1]) if len(shibor_data) > 0 else np.nan
        shibor_change = shibor_data.pct_change().iloc[-1] * 100 if len(shibor_data) > 1 else 0
        
        print(f"\n📊 流动性指标:")
        print(f"  融资余额: {current_margin:.0f}亿")
        print(f"    └─5日变化: {margin_change_5d:+.2f}%")
        print(f"    └─30日变化: {margin_change_30d:+.2f}%")
        print(f"  Shibor 1M: {current_shibor:.2f}%")
        print(f"    └─日变化: {shibor_change:+.2f}%")
        
        if validate_data(bond_data) and 'spread' in bond_data.columns:
            current_spread = float(bond_data['spread'].iloc[-1])
            spread_change_5d = bond_data['spread'].diff(5).iloc[-1]
            print(f"  中美利差: {current_spread:.2f}bp (5日变化: {spread_change_5d:+.0f}bp)")
        
        # 融资余额解读
        if margin_change_5d > 2:
            margin_signal = "🔼 加速入场"
            margin_desc = "杠杆资金快速入场，市场情绪亢奋，风险偏好提升"
        elif margin_change_5d < -2:
            margin_signal = "🔽 加速撤离"
            margin_desc = "杠杆资金恐慌离场，市场信心不足，风险偏好下降"
        elif margin_change_30d > 5:
            margin_signal = "📈 持续流入"
            margin_desc = "杠杆资金持续加仓，趋势向好"
        elif margin_change_30d < -5:
            margin_signal = "📉 持续流出"
            margin_desc = "杠杆资金持续撤离，趋势承压"
        else:
            margin_signal = "🔄 平稳波动"
            margin_desc = "杠杆资金保持平稳，市场情绪中性"
        
        print(f"\n🎯 融资余额: {margin_signal}")
        print(f"💡 解读: {margin_desc}")
        
        # Shibor解读
        if current_shibor > 3.0:
            shibor_signal = "📈 利率高位"
            shibor_desc = "银行间流动性紧张，可能收紧"
        elif current_shibor < 2.0:
            shibor_signal = "📉 利率低位"
            shibor_desc = "银行间流动性充裕，政策宽松"
        else:
            shibor_signal = "🔄 利率中性"
            shibor_desc = "银行间流动性中性"
        
        print(f"\n🎯 Shibor: {shibor_signal}")
        print(f"💡 解读: {shibor_desc}")
        
        # 股债性价比
        if validate_data(bond_data) and 'spread' in bond_data.columns:
            if current_spread > 50:
                spread_signal = "🔼 利差走阔"
                spread_desc = "中国相对吸引力下降，资本外流压力"
            elif current_spread < 0:
                spread_signal = "🔽 利差收窄"
                spread_desc = "中国相对吸引力上升，资金流入"
            else:
                spread_signal = "🔄 利差正常"
                spread_desc = "相对吸引力中性"
            
            print(f"\n🎯 中美利差: {spread_signal}")
            print(f"💡 解读: {spread_desc}")
        
        # 技术形态
        etf_500 = get_data('ETF_510500', start_date_str, end_date_str)
        if validate_data(etf_500, 30):
            margin_ma10 = margin_data['融资余额'].rolling(10).mean()
            etf_ma10 = etf_500.rolling(10).mean()
            
            margin_above_ma = margin_data['融资余额'].iloc[-1] > margin_ma10.iloc[-1]
            etf_above_ma = etf_500.iloc[-1] > etf_ma10.iloc[-1]
            
            print(f"\n📈 技术形态:")
            print(f"  融资余额 vs MA10: {'✅上方' if margin_above_ma else '❌下方'}")
            print(f"  500ETF vs MA10:   {'✅上方' if etf_above_ma else '❌下方'}")
            
            if margin_above_ma and etf_above_ma:
                status = "✅ 量价齐升"
                desc = "趋势健康，资金和市场同步向上"
            elif margin_above_ma and not etf_above_ma:
                status = "💡 资金领先"
                desc = "融资资金逆势加仓，可能筑底信号"
            elif not margin_above_ma and etf_above_ma:
                status = "⚠️  背离信号"
                desc = "市场上涨但资金流出，动能不足"
            else:
                status = "🔴 同步下行"
                desc = "趋势偏弱，等待企稳"
            
            print(f"🎯 综合判断: {status}")
            print(f"💡 含义: {desc}")
        
        # 流动性评分
        liquidity_score = 0
        if margin_change_5d > 1: liquidity_score += 1
        elif margin_change_5d < -1: liquidity_score -= 1
        
        if current_shibor < 2.5: liquidity_score += 1
        elif current_shibor > 3.0: liquidity_score -= 1
        
        if validate_data(bond_data) and 'spread' in bond_data.columns:
            if bond_data['spread'].iloc[-1] > 50: liquidity_score -= 1
        
        print(f"\n💧 流动性评分: {liquidity_score}/2")
        if liquidity_score >= 1:
            liquidity_env = "🟢 宽松环境"
            liquidity_desc = "流动性充裕，利好风险资产"
        elif liquidity_score <= -1:
            liquidity_env = "🔴 紧张环境"
            liquidity_desc = "流动性紧张，压制风险资产"
        else:
            liquidity_env = "🟡 中性环境"
            liquidity_desc = "流动性中性，市场分化"
        
        print(f"🎯 综合环境: {liquidity_env}")
        print(f"💡 资产影响: {liquidity_desc}")
        
        # 记录洞察
        EXECUTION_LOG['market_signals']['liquidity_env'] = liquidity_env
        EXECUTION_LOG['insights'].append(('流动性', f'融资{current_margin:.0f}亿 Shibor{current_shibor:.2f}% {liquidity_env}'))
        
    except Exception as e:
        print(f"❌ 流动性分析失败: {e}")
        log_execution('流动性分析', 'error', str(e))

def plot_data(data_dict, title, labels, colors, linewidths=None, save_path=None):
    """绘制数据图表"""
    start_time = time.time()
    try:
        valid_data = {k: v for k, v in data_dict.items() if validate_data(v, 5)}
        if not valid_data:
            print(f"❌ 无有效数据: {title}")
            log_execution('绘图', 'warning', f'{title} 无有效数据')
            return
        
        fig, ax = plt.subplots(figsize=(20, 12), facecolor='black')
        
        for i, (key, values) in enumerate(valid_data.items()):
            linewidth = linewidths[i] if linewidths else 1.5
            ax.plot(values.index, values, color=colors[i], 
                   label=labels[i], linewidth=linewidth)
        
        ax.set_title(title, fontsize=13, fontweight='heavy', pad=8, color='white')
        ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
        ax.grid(True, alpha=0.3, color='#666666')
        
        plt.gcf().autofmt_xdate(rotation=45, ha='right')
        plt.tight_layout(pad=0.8, h_pad=0.8, w_pad=0.8)
        
        if save_path:
            filepath = os.path.join(OUTPUT_DIR, save_path)
            plt.savefig(filepath, bbox_inches='tight', pad_inches=0.1, 
                       facecolor='black', dpi=150)
            print(f"✅ 图表: {save_path}")
            log_execution('绘图', 'success', f'{title} -> {save_path}', chart_path=save_path)
        
        plt.close(fig)
        log_execution('绘图', 'success', f'{title} 耗时 {time.time()-start_time:.2f}s')
        
    except Exception as e:
        print(f"❌ 绘图失败 {title}: {e}")
        log_execution('绘图', 'error', f'{title}: {str(e)}')
        plt.close('all')

def plot_oil_gold_bond():
    """油金比分析"""
    start_time = time.time()
    try:
        oil_prices = get_data("CL", None, None)
        gold_prices = get_data("GC", None, None)
        
        if not (validate_data(oil_prices, 50) and validate_data(gold_prices, 50)):
            print("❌ 原油或黄金数据不足")
            return
        
        oil_prices, gold_prices = oil_prices.align(gold_prices, join='inner')
        if not validate_data(oil_prices, 30):
            print("❌ 数据对齐后不足")
            return
        
        oil_gold_ratio = oil_prices / gold_prices
        us_bond = get_data('US_BOND', None, None)
        
        if not validate_data(us_bond, 30):
            print("❌ 美债数据不足")
            return
        
        us_bond = us_bond.iloc[-300:] if len(us_bond) > 300 else us_bond
        oil_gold_ratio = oil_gold_ratio.iloc[-300:] if len(oil_gold_ratio) > 300 else oil_gold_ratio
        
        fig, ax1 = plt.subplots(figsize=(20, 12), facecolor='black')
        ax2 = ax1.twinx()
        
        line1 = ax1.plot(oil_gold_ratio, 'r-', label='Oil/Gold Ratio', linewidth=1.5)
        ax1.set_ylabel('Oil/Gold Ratio', color='r', fontsize=10)
        
        line2 = ax2.plot(us_bond, 'b-', label='US 10Y Yield', linewidth=1.5)
        ax2.set_ylabel('US 10Y Yield (%)', color='b', fontsize=10)
        
        plt.title('Oil/Gold Ratio vs US 10Y Treasury Yield Trend', 
                 fontsize=13, fontweight='heavy', pad=8)
        
        ax1.grid(True, alpha=0.3, color='#666666')
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left', fontsize=8)
        
        plt.gcf().autofmt_xdate(rotation=45, ha='right')
        plt.tight_layout(pad=0.8)
        
        filepath = os.path.join(OUTPUT_DIR, 'jyb_gz.png')
        plt.savefig(filepath, bbox_inches='tight', pad_inches=0.1, 
                   facecolor='black', dpi=150)
        print("✅ 图表: jyb_gz.png")
        log_execution('油金比', 'success', f'耗时 {time.time()-start_time:.2f}s', 'jyb_gz.png')
        plt.close(fig)
        
    except Exception as e:
        print(f"❌ 油金比图表失败: {e}")
        log_execution('油金比', 'error', str(e))
        plt.close('all')

def plot_pe_bond_spread():
    """股债利差分析"""
    start_time = time.time()
    try:
        bond_df = safe_get_data(ak.bond_zh_us_rate, start_date="20121219")
        pe_df = safe_get_data(ak.stock_index_pe_lg, symbol="上证50")
        
        if bond_df.empty or pe_df.empty:
            print("❌ 债券或PE数据获取失败")
            return
        
        required_cols = {'债券': ['日期', '中国国债收益率10年'], 'PE': ['日期', '滚动市盈率']}
        if not all(col in bond_df.columns for col in required_cols['债券']):
            print("❌ 债券数据缺少必要列")
            return
        if not all(col in pe_df.columns for col in required_cols['PE']):
            print("❌ PE数据缺少必要列")
            return
        
        bond_df['日期'] = pd.to_datetime(bond_df['日期'], errors='coerce')
        pe_df['日期'] = pd.to_datetime(pe_df['日期'], errors='coerce')
        
        bond_10y = bond_df.dropna().set_index('日期')['中国国债收益率10年']
        pe_ratio = pe_df.dropna().set_index('日期')['滚动市盈率']
        
        # 修复: 确保有足够的交集数据
        common_idx = bond_10y.index.intersection(pe_ratio.index)
        if len(common_idx) < 50:  # 降低要求到50
            print(f"⚠️  日期交集数据不足: {len(common_idx)} < 50")
            # 尝试使用最近的数据
            bond_10y = bond_10y.tail(200)
            pe_ratio = pe_ratio.tail(200)
            common_idx = bond_10y.index.intersection(pe_ratio.index)
            if len(common_idx) < 30:
                log_execution('股债利差', 'warning', '日期交集不足')
                return
        
        spread = bond_10y.loc[common_idx] - 100 / pe_ratio.loc[common_idx]
        spread = spread.ffill().dropna()
        
        if len(spread) < 30:
            print("⚠️  股债利差数据不足")
            return
        
        fig, ax = plt.subplots(figsize=(20, 12), facecolor='black')
        spread.plot(ax=ax, color='white', linewidth=1.5, title='股债利差')
        
        for y, color, label in [
            (-2.6, 'red', '高息'), (-5.5, 'green', '正常'), 
            (-7.8, 'blue', '低息'), (-4.5, 'gray', ''), (-6.8, 'gray', '')
        ]:
            plt.axhline(y=y, ls=":", c=color, label=label if label else None, alpha=0.7)
        
        plt.legend(fontsize=8, loc='upper left')
        plt.grid(True, alpha=0.3, color='#666666')
        plt.title('股债利差', fontsize=13, fontweight='heavy', pad=8)
        
        plt.gcf().autofmt_xdate(rotation=45, ha='right')
        plt.tight_layout(pad=0.8)
        
        filepath = os.path.join(OUTPUT_DIR, 'guzhaixicha.png')
        plt.savefig(filepath, bbox_inches='tight', pad_inches=0.1, 
                   facecolor='black', dpi=150)
        print("✅ 图表: guzhaixicha.png")
        log_execution('股债利差', 'success', f'耗时 {time.time()-start_time:.2f}s', 'guzhaixicha.png')
        plt.close(fig)
        
        # 解读
        current_spread = float(spread.iloc[-1])
        spread_percentile = (spread <= current_spread).sum() / len(spread) * 100
        
        print(f"\n【股债利差解读】")
        print(f"当前利差: {current_spread:.2f}% (历史{spread_percentile:.0f}分位)")
        
        if current_spread < -7:
            equity_signal = "🔴 股票性价比极低"
            bond_signal = "🟢 债券吸引力极高"
        elif current_spread > -3:
            equity_signal = "🟢 股票性价比高"
            bond_signal = "🔴 债券吸引力弱"
        else:
            equity_signal = "🟡 股票性价比中性"
            bond_signal = "🟡 债券吸引力中性"
        
        print(f"💡 股票: {equity_signal}")
        print(f"💡 债券: {bond_signal}")
        
        # 记录洞察
        EXECUTION_LOG['market_signals']['equity_signal'] = equity_signal
        EXECUTION_LOG['insights'].append(('股债利差', f'{current_spread:.2f}% {equity_signal.split()[1]}'))
        
    except Exception as e:
        print(f"❌ 股债利差图表失败: {e}")
        log_execution('股债利差', 'error', str(e))
        plt.close('all')

def main():
    """主执行函数"""
    EXECUTION_LOG['start_time'] = datetime.now().isoformat()
    print("\n" + "="*70)
    print("金融数据分析程序启动")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print("="*70)
    
    start_time = time.time()
    success_count = 0
    total_tasks = 0
    start_date_str = ""
    end_date_str = ""
    
    # === 任务1: 指数K线图 ===
    print("\n【任务1】生成指数K线图...")
    indices = [
        ("^TNX", "tenbond.png"), ("^VIX", "vix.png", "2mo"),
        ("^GSPC", "sp500.png"), ("^IXIC", "nasdaq.png"),
        ("^RUT", "rs2000.png"), ("VNQ", "vnq.png"),
        ("^N225", "nikkei225.png"), ("^HSI", "hsi.png"),
        ("CNY=X", "rmb.png")
    ]
    
    for item in indices:
        total_tasks += 1
        try:
            ticker, filename = item[0], item[1]
            period = item[2] if len(item) > 2 else "1mo"
            generate_and_save_plot(ticker, filename, period)
            success_count += 1
        except Exception as e:
            print(f"❌ 任务失败 {item[0]}: {e}")
    
    # === 任务2: 融资余额分析 ===
    print("\n【任务2】融资余额分析...")
    total_tasks += 1
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=300)
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        
        margin_data = get_data('融资余额', start_date_str, end_date_str)
        if validate_data(margin_data, 50):
            margin_data['ma10'] = margin_data['融资余额'].rolling(10).mean()
            plot_data(
                {'融资余额': margin_data['融资余额'].iloc[-50:], 
                 'ma10': margin_data['ma10'].iloc[-50:]},
                '融资余额与MA10', ['融资余额', 'MA10'], ['r', 'b'],
                save_path='rongziyue_ma.png'
            )
            
            last_margin = margin_data[['融资余额', 'ma10']].iloc[-1:].fillna(0)
            last_margin_m = (last_margin / 1000000).round(1)
            print(f"最新融资余额: {last_margin_m['融资余额'].iloc[0]}M")
            
            if last_margin['融资余额'].iloc[0] < last_margin['ma10'].iloc[-1]:
                print("⚠️  \x1b[31m注意：风险偏好下资金流出!!!\x1b[0m")
            
            success_count += 1
            log_execution('融资余额', 'success', f'最新: {last_margin_m["融资余额"].iloc[0]}M')
        else:
            print("❌ 融资余额数据不足")
            log_execution('融资余额', 'warning', '数据不足')
    except Exception as e:
        print(f"❌ 融资余额分析失败: {e}")
    
    # === 任务3: 多指标对比 ===
    print("\n【任务3】多指标对比...")
    total_tasks += 1
    try:
        exchange_rate = get_data('美元', start_date_str, end_date_str)
        shibor_data = get_data('Shibor 1M', start_date_str, end_date_str)
        bond_data = get_data('中美国债收益率', start_date_str, end_date_str)
        etf_300 = get_data('ETF_510300', start_date_str, end_date_str)
        etf_1000 = get_data('ETF_159845', start_date_str, end_date_str)
        etf_500 = get_data('ETF_510500', start_date_str, end_date_str)
        
        plot_data(
            {'融资余额': normalize(margin_data['融资余额'] if validate_data(margin_data) else pd.Series()),
             '汇率': normalize(-exchange_rate),
             '中美利差': normalize(bond_data['spread'] if validate_data(bond_data) and 'spread' in bond_data.columns else pd.Series()),
             '500ETF': normalize(etf_500)},
            '归一化指标对比', ['融资余额', '汇率', '中美利差', '500ETF'],
            ['g', 'c', 'k', 'r'], save_path='rongziyue_1.png'
        )
        
        plot_data(
            {'融资余额': normalize(margin_data['融资余额'] if validate_data(margin_data) else pd.Series()),
             '300ETF': normalize(etf_300),
             '1000ETF': normalize(etf_1000)},
            '融资余额与ETF对比', ['融资余额', '300ETF', '1000ETF'],
            ['g', 'r', 'b'], save_path='rongziyue_2.png'
        )
        
        plot_data(
            {'Shibor 1M': normalize(shibor_data.iloc[-200:] if validate_data(shibor_data) else pd.Series()),
             '中美国债收益率差': normalize(bond_data['spread'].iloc[-200:] if validate_data(bond_data) and 'spread' in bond_data.columns else pd.Series())},
            '流动性指标', ['Shibor 1M', '中美国债利差'], ['k', 'g'],
            save_path='liudongxing.png'
        )
        
        if validate_data(bond_data) and validate_data(shibor_data):
            if 'spread' in bond_data.columns and len(shibor_data) > 1:
                bond_diff = bond_data['spread'].diff().iloc[-1] if len(bond_data) > 1 else 0
                shibor_diff = shibor_data.diff().iloc[-1] if len(shibor_data) > 1 else 0
                if bond_diff > 0 and shibor_diff < 0:
                    print("\n⚠️  \x1b[31m注意：国内剩余流动性激增，股市预受损\x1b[0m")
        
        success_count += 1
        log_execution('多指标对比', 'success', '完成3张图表')
    except Exception as e:
        print(f"❌ 多指标对比失败: {e}")
    
    # === 任务4: 油金比分析 ===
    print("\n【任务4】油金比分析...")
    total_tasks += 1
    try:
        plot_oil_gold_bond()
        success_count += 1
    except Exception as e:
        print(f"❌ 油金比分析失败: {e}")
    
    # === 任务5: 相关性分析 ===
    print("\n【任务5】相关性分析...")
    total_tasks += 1
    try:
        hsi_df = yf.download('^HSI', period='300d', interval='1d', progress=False)
        rut_df = yf.download('^RUT', period='300d', interval='1d', progress=False)
        
        # 修复: 正确处理DataFrame判断
        if validate_data(hsi_df, 50) and validate_data(rut_df, 50):
            hsi_close = hsi_df[['Close']].rename(columns={'Close': 'HSI'})
            rut_close = rut_df[['Close']].rename(columns={'Close': 'RUT'})
            
            df = pd.concat([hsi_close, rut_close], axis=1, join='inner').dropna()
            
            if len(df) > 30:
                correlation = df['HSI'].corr(df['RUT'])
                print(f"恒生指数与Russell 2000相关性: {correlation:.4f}")
                
                fig, ax = plt.subplots(figsize=(20, 12), facecolor='black')
                ax.plot(df.index, df['HSI']/df['HSI'].iloc[0], label='HSI (归一化)', color='#3498db', linewidth=1.5)
                ax.plot(df.index, df['RUT']/df['RUT'].iloc[0], label='RUT (归一化)', color='#e74c3c', linewidth=1.5)
                ax.set_title('恒生指数与Russell 2000走势对比', fontsize=13, fontweight='heavy', pad=8)
                ax.legend(fontsize=8)
                ax.grid(alpha=0.3, color='#666666')
                
                plt.gcf().autofmt_xdate(rotation=45, ha='right')
                plt.tight_layout(pad=0.8)
                
                filepath = os.path.join(OUTPUT_DIR, 'hsi_rut_comparison.png')
                plt.savefig(filepath, bbox_inches='tight', pad_inches=0.1, 
                           facecolor='black', dpi=150)
                print("✅ 图表: hsi_rut_comparison.png")
                plt.close(fig)
                
                success_count += 1
                log_execution('相关性分析', 'success', f'相关系数: {correlation:.4f}')
            else:
                print("❌ 相关性数据不足")
                log_execution('相关性分析', 'warning', '数据不足')
        else:
            print("❌ 指数数据下载失败")
            log_execution('相关性分析', 'warning', '下载失败')
    except Exception as e:
        print(f"❌ 相关性分析失败: {e}")
    
    # === 任务6: 股债利差 ===
    print("\n【任务6】股债利差分析...")
    total_tasks += 1
    try:
        plot_pe_bond_spread()
        success_count += 1
    except Exception as e:
        print(f"❌ 股债利差分析失败: {e}")
    
    # === 综合解读（核心） ===
    print("\n" + "📈 开始生成市场解读".center(70, "="))
    try:
        analyze_index_divergence()
        analyze_risk_regime()
        analyze_china_us_linkage()
        analyze_liquidity_conditions()
        print("\n" + "📊 市场解读完成".center(70, "="))
        log_execution('市场解读', 'success', '完成全部维度分析')
    except Exception as e:
        print(f"❌ 市场解读失败: {e}")
        log_execution('市场解读', 'error', str(e))
    
    # 生成报告
    save_execution_report()
    generate_markdown_report()
    
    # 总结
    EXECUTION_LOG['end_time'] = datetime.now().isoformat()
    EXECUTION_LOG['total_time'] = f"{time.time() - start_time:.2f}s"
    
    print("\n" + "="*70)
    print(f"执行完成: {success_count}/{total_tasks} 任务成功")
    print(f"总耗时: {time.time() - start_time:.2f}秒")
    print(f"图表输出: {len([t for t in EXECUTION_LOG['tasks'] if t['chart_path']])} 张")
    print(f"风险提示: {len(EXECUTION_LOG['warnings'])} 个")
    print(f"查看输出: ls -lh {os.path.abspath(OUTPUT_DIR)}")
    print("="*70)
    
    return success_count, total_tasks

if __name__ == "__main__":
    success, total = main()
    sys.exit(0)

