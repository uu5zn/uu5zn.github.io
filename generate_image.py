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

warnings.filterwarnings('ignore')

# 创建输出目录
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def check_available_fonts():
    """检查系统可用字体（调试用）"""
    import matplotlib.font_manager as fm
    fonts = fm.findSystemFonts()
    chinese_fonts = [f for f in fonts if 'wqy' in f.lower() or 'noto' in f.lower() or 'cjk' in f.lower()]
    print(f"系统找到 {len(chinese_fonts)} 个中文字体:")
    for f in chinese_fonts[:3]:
        print(f"  - {os.path.basename(f)}")
    
    # 测试实际渲染
    test_path = os.path.join(OUTPUT_DIR, "font_test.png")
    try:
        fig, ax = plt.subplots(figsize=(4, 2), facecolor='black')
        ax.text(0.5, 0.5, '中文测试 123', ha='center', va='center', 
                fontsize=12, color='white')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        plt.tight_layout(pad=0.1)
        plt.savefig(test_path, bbox_inches='tight', facecolor='black')
        plt.close()
        print(f"✅ 字体测试图已生成: {test_path}")
    except Exception as e:
        print(f"⚠️  字体测试失败: {e}")
    
    return len(chinese_fonts) > 0

def setup_matplotlib_fonts():
    """设置matplotlib字体（服务器环境优化）"""
    # 优先使用的中文字体列表（从轻到重）
    font_candidates = [
        'WenQuanYi Micro Hei',  # 最轻量
        'WenQuanYi Zen Hei',
        'Noto Sans CJK SC',
        'Noto Sans SC',
        'DejaVu Sans',
    ]
    
    # 检查哪个字体可用
    available_font = None
    for font in font_candidates:
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
        print("⚠️  未找到中文字体，使用默认字体")
        available_font = 'sans-serif'
    
    # 核心设置：优化边距和字体
    plt.rcParams.update({
        # 基础尺寸
        'figure.figsize': (12, 8),
        'figure.dpi': 100,
        'savefig.dpi': 150,  # 降低DPI减少文件大小
        
        # 颜色主题（黑底白字）
        'figure.facecolor': 'black',
        'axes.facecolor': 'black',
        'savefig.facecolor': 'black',
        'savefig.transparent': False,
        'axes.labelcolor': 'white',
        'xtick.color': 'white',
        'ytick.color': 'white',
        'text.color': 'white',
        'axes.titlecolor': 'white',
        'legend.labelcolor': 'white',
        
        # 字体设置（关键）
        'font.family': 'sans-serif',
        'font.sans-serif': [available_font],
        'font.size': 9,  # 减小字体
        'axes.titlesize': 13,
        'legend.fontsize': 8,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        
        # 线条样式
        'lines.linewidth': 1.5,
        'lines.markersize': 4,
        'axes.prop_cycle': plt.cycler(color=['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6']),
        
        # 网格
        'axes.grid': True,
        'grid.color': '#666666',
        'grid.alpha': 0.5,
        'grid.linestyle': '--',
        
        # 边框
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.spines.left': True,
        'axes.spines.bottom': True,
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        
        # 图例
        'legend.frameon': True,
        'legend.facecolor': '#333333',
        'legend.edgecolor': 'white',
        'legend.framealpha': 0.8,
        'legend.loc': 'upper left',
        
        # 关键：大幅减小边距
        'figure.subplot.left': 0.06,
        'figure.subplot.right': 0.96,
        'figure.subplot.top': 0.94,
        'figure.subplot.bottom': 0.08,
        'figure.subplot.wspace': 0.1,
        'figure.subplot.hspace': 0.1,
        
        # 其他
        'axes.unicode_minus': False,
        'figure.constrained_layout.use': False,  # 禁用自动布局
    })

# 初始化字体设置
setup_matplotlib_fonts()
check_available_fonts()

def fix_currency_boc_sina(symbol: str = "美元", start_date: str = "20230304", end_date: str = "20231110") -> pd.DataFrame:
    """修复版新浪财经-中行人民币牌价数据"""
    url = "http://biz.finance.sina.com.cn/forex/forex.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # 获取货币代码映射
        params = {
            "startdate": "-".join([start_date[:4], start_date[4:6], start_date[6:]]),
            "enddate": "-".join([end_date[:4], end_date[4:6], end_date[6:]]),
            "money_code": "EUR",
            "type": "0",
        }
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.encoding = "gbk"
        soup = BeautifulSoup(r.text, "lxml")
        
        money_code_element = soup.find(attrs={"id": "money_code"})
        if money_code_element is None:
            print(f"⚠️ 无法获取货币代码映射")
            return pd.DataFrame()
        
        data_dict = dict(
            zip(
                [item.text for item in money_code_element.find_all("option")],
                [item["value"] for item in money_code_element.find_all("option")]
            )
        )
        
        if symbol not in data_dict:
            print(f"⚠️ 不支持的货币: {symbol}")
            return pd.DataFrame()
        
        money_code = data_dict[symbol]
        
        # 获取数据
        params = {
            "money_code": money_code,
            "type": "0",
            "startdate": "-".join([start_date[:4], start_date[4:6], start_date[6:]]),
            "enddate": "-".join([end_date[:4], end_date[4:6], end_date[6:]]),
            "page": "1",
            "call_type": "ajax",
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
        
        # 动态处理列名
        if len(big_df.columns) == 6:
            big_df.columns = ["日期", "中行汇买价", "中行钞买价", "中行钞卖价", "中行汇卖价", "央行中间价"]
        elif len(big_df.columns) == 5:
            big_df.columns = ["日期", "中行汇买价", "中行钞买价", "中行钞卖价/汇卖价", "央行中间价"]
        else:
            print(f"⚠️ 未知列数: {len(big_df.columns)}")
            return pd.DataFrame()
        
        # 数据类型转换
        big_df["日期"] = pd.to_datetime(big_df["日期"], errors="coerce").dt.date
        for col in big_df.columns[1:]:
            big_df[col] = pd.to_numeric(big_df[col], errors="coerce")
        
        big_df.sort_values(by=["日期"], inplace=True, ignore_index=True)
        return big_df
    except Exception as e:
        print(f"⚠️ 获取汇率数据失败: {e}")
        return pd.DataFrame()

def safe_get_data(func, *args, **kwargs):
    """安全获取数据"""
    try:
        data = func(*args, **kwargs)
        if data is None or (hasattr(data, 'empty') and data.empty):
            print(f"⚠️ 数据获取失败: {func.__name__}")
            return pd.DataFrame()
        return data
    except Exception as e:
        print(f"⚠️ 数据获取异常 {func.__name__}: {str(e)[:100]}")
        return pd.DataFrame()

def validate_data(data, min_points=10):
    """验证数据有效性"""
    if data is None or (hasattr(data, 'empty') and data.empty) or len(data) < min_points:
        return False
    return True

def generate_and_save_plot(ticker, filename, period="1mo"):
    """生成K线图（优化版）"""
    try:
        data = yf.Ticker(ticker).history(period=period)
        if validate_data(data, 5):
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            # 创建自定义样式
            style = mpf.make_mpf_style(
                base_mpf_style='charles',
                marketcolors=mpf.make_marketcolors(
                    up='#e74c3c', down='#2ecc71',
                    edge='inherit',
                    wick={'up':'#e74c3c', 'down':'#2ecc71'},
                    volume='in'
                ),
                facecolor='black',
                edgecolor='white',
                figcolor='black',
                gridcolor='#666666',
                gridstyle='--',
                rc={'font.size': 8}
            )
            
            # 绘制K线图
            mpf.plot(
                data, 
                type='candle', 
                figscale=0.35,
                volume=False,
                savefig=filepath,
                datetime_format='%m-%d',
                style=style,
                title=ticker,
                tight_layout=True,
                bbox_inches='tight',
                warn_too_much_data=1000  # 抑制数据过多警告
            )
            print(f"✅ K线图: {filename}")
        else:
            print(f"❌ 数据不足: {ticker}")
    except Exception as e:
        print(f"❌ K线图失败 {ticker}: {e}")

def get_data(symbol, start_date, end_date):
    """获取数据（主函数）"""
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
        print(f"❌ 数据处理失败 {symbol}: {e}")
    
    return pd.Series(dtype=float)

def normalize(data):
    """归一化处理"""
    try:
        if validate_data(data, 2):
            return (data - data.min()) / (data.max() - data.min())
    except:
        pass
    return pd.Series(dtype=float)

def plot_data(data_dict, title, labels, colors, linewidths=None, save_path=None):
    """绘制数据图表（最终优化版）"""
    try:
        valid_data = {k: v for k, v in data_dict.items() if validate_data(v, 5)}
        if not valid_data:
            print(f"❌ 无有效数据: {title}")
            return
        
        fig, ax = plt.subplots(figsize=(20, 12), facecolor='black')  # 调整比例
        
        # 绘制数据
        for i, (key, values) in enumerate(valid_data.items()):
            linewidth = linewidths[i] if linewidths else 1.5
            ax.plot(values.index, values, color=colors[i], 
                   label=labels[i], linewidth=linewidth)
        
        # 设置标题和标签
        ax.set_title(title, fontsize=13, fontweight='heavy', pad=8, color='white')
        ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
        ax.grid(True, alpha=0.3, color='#666666')
        
        # 日期格式优化
        plt.gcf().autofmt_xdate(rotation=45, ha='right')
        
        # 关键：紧凑布局
        plt.tight_layout(pad=0.8, h_pad=0.8, w_pad=0.8)
        
        if save_path:
            filepath = os.path.join(OUTPUT_DIR, save_path)
            # 关键：bbox_inches='tight'去除白边
            plt.savefig(filepath, bbox_inches='tight', pad_inches=0.1, 
                       facecolor='black', dpi=150)
            print(f"✅ 图表: {save_path}")
        
        plt.close(fig)  # 立即关闭释放内存
        
    except Exception as e:
        print(f"❌ 绘图失败 {title}: {e}")
        plt.close('all')

def plot_oil_gold_bond():
    """油金比分析"""
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
        
        # 限制数据长度
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
        plt.close(fig)
        
    except Exception as e:
        print(f"❌ 油金比图表失败: {e}")
        plt.close('all')

def plot_pe_bond_spread():
    """股债利差分析"""
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
        
        common_idx = bond_10y.index.intersection(pe_ratio.index)
        if len(common_idx) < 100:
            print("❌ 日期交集数据不足")
            return
        
        spread = bond_10y.loc[common_idx] - 100 / pe_ratio.loc[common_idx]
        spread = spread.ffill().dropna()
        
        if not validate_data(spread, 50):
            print("❌ 股债利差数据不足")
            return
        
        fig, ax = plt.subplots(figsize=(20, 12), facecolor='black')
        spread.plot(ax=ax, color='white', linewidth=1.5, title='股债利差')
        
        # 添加参考线
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
        plt.close(fig)
        
    except Exception as e:
        print(f"❌ 股债利差图表失败: {e}")
        plt.close('all')

def main():
    """主执行函数"""
    print("\n" + "="*70)
    print("金融数据分析程序启动")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print("="*70)
    
    success_count = 0
    total_tasks = 0
    start_date_str = ""
    end_date_str = ""
    
    # 任务1: 指数K线图
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
    
    # 任务2: 融资余额分析
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
            
            # 风险提示
            last_margin = margin_data[['融资余额', 'ma10']].iloc[-1:].fillna(0)
            last_margin_m = (last_margin / 1000000).round(1)
            print(f"最新融资余额: {last_margin_m['融资余额'].iloc[0]}M")
            
            if last_margin['融资余额'].iloc[0] < last_margin['ma10'].iloc[0]:
                print("⚠️  \x1b[31m注意：风险偏好下资金流出!!!\x1b[0m")
            
            success_count += 1
        else:
            print("❌ 融资余额数据不足")
    except Exception as e:
        print(f"❌ 融资余额分析失败: {e}")
    
    # 任务3: 多指标对比
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
        
        # 流动性警告
        if validate_data(bond_data) and validate_data(shibor_data):
            if 'spread' in bond_data.columns and len(shibor_data) > 1:
                bond_diff = bond_data['spread'].diff().iloc[-1] if len(bond_data) > 1 else 0
                shibor_diff = shibor_data.diff().iloc[-1] if len(shibor_data) > 1 else 0
                if bond_diff > 0 and shibor_diff < 0:
                    print("\n⚠️  \x1b[31m注意：国内剩余流动性激增，股市预受损\x1b[0m")
        
        success_count += 1
    except Exception as e:
        print(f"❌ 多指标对比失败: {e}")
    
    # 任务4: 油金比分析
    print("\n【任务4】油金比分析...")
    total_tasks += 1
    try:
        plot_oil_gold_bond()
        success_count += 1
    except Exception as e:
        print(f"❌ 油金比分析失败: {e}")
    
    # 任务5: 相关性分析
    print("\n【任务5】相关性分析...")
    total_tasks += 1
    try:
        hsi_df = yf.download('^HSI', period='300d', interval='1d', progress=False)
        rut_df = yf.download('^RUT', period='300d', interval='1d', progress=False)
        
        if validate_data(hsi_df, 50) and validate_data(rut_df, 50):
            hsi_close = hsi_df[['Close']].rename(columns={'Close': 'HSI'})
            rut_close = rut_df[['Close']].rename(columns={'Close': 'RUT'})
            
            df = pd.concat([hsi_close, rut_close], axis=1, join='inner').dropna()
            
            if validate_data(df, 30):
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
            else:
                print("❌ 相关性数据不足")
        else:
            print("❌ 指数数据下载失败")
    except Exception as e:
        print(f"❌ 相关性分析失败: {e}")
    
    # 任务6: 股债利差
    print("\n【任务6】股债利差分析...")
    total_tasks += 1
    try:
        plot_pe_bond_spread()
        success_count += 1
    except Exception as e:
        print(f"❌ 股债利差分析失败: {e}")
    
    # 总结
    print("\n" + "="*70)
    print(f"执行完成: {success_count}/{total_tasks} 任务成功")
    print(f"查看输出: ls -lh {os.path.abspath(OUTPUT_DIR)}")
    print("="*70)
    
    return success_count, total_tasks

if __name__ == "__main__":
    success, total = main()
    # 退出码非零表示有失败任务
    sys.exit(0 if success == total else 1)
