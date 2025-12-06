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

# 设置全局字体（适配Linux服务器环境）
plt.rcParams.update({
    'figure.figsize': (10, 6), 'figure.dpi': 100, 'savefig.dpi': 300,
    'figure.facecolor': 'black', 'axes.facecolor': 'black', 'savefig.facecolor': 'black',
    'savefig.transparent': False, 'font.family': 'WenQuanYi Micro Hei', 'font.size': 12,
    'axes.labelcolor': 'white', 'xtick.color': 'white', 'ytick.color': 'white',
    'text.color': 'white', 'axes.titlesize': 16, 'axes.titlecolor': 'white',
    'legend.fontsize': 11, 'legend.labelcolor': 'white', 'lines.linewidth': 2.0,
    'lines.markersize': 6, 'axes.prop_cycle': plt.cycler(color=['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6']),
    'axes.grid': True, 'grid.color': '#666666', 'grid.alpha': 0.5, 'grid.linestyle': '--',
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': True,
    'axes.spines.bottom': True, 'xtick.direction': 'in', 'ytick.direction': 'in',
    'legend.frameon': True, 'legend.facecolor': '#333333', 'legend.edgecolor': 'white',
    'legend.framealpha': 0.8, 'figure.subplot.left': 0.08, 'figure.subplot.right': 0.95,
    'figure.subplot.top': 0.92, 'figure.subplot.bottom': 0.1, 'axes.unicode_minus': False,
})

def fix_currency_boc_sina(symbol: str = "美元", start_date: str = "20230304", end_date: str = "20231110") -> pd.DataFrame:

    # 获取货币代码映射
    url = "http://biz.finance.sina.com.cn/forex/forex.php "
    params = {
        "startdate": "-".join([start_date[:4], start_date[4:6], start_date[6:]]),
        "enddate": "-".join([end_date[:4], end_date[4:6], end_date[6:]]),
        "money_code": "EUR",
        "type": "0",
    }
    r = requests.get(url, params=params)
    r.encoding = "gbk"
    soup = BeautifulSoup(r.text, "lxml")
    
    # 检查是否能找到货币代码选择器
    money_code_element = soup.find(attrs={"id": "money_code"})
    if money_code_element is None:
        print(f"⚠️ 无法获取货币代码映射，可能网页结构已变化")
        return pd.DataFrame()
    
    data_dict = dict(
        zip(
            [item.text for item in money_code_element.find_all("option")],
            [item["value"] for item in money_code_element.find_all("option")]
        )
    )
    
    if symbol not in data_dict:
        print(f"⚠️  不支持的货币类型: {symbol}，支持的货币: {list(data_dict.keys())}")
        return pd.DataFrame()
    
    money_code = data_dict[symbol]
    
    # 构建请求参数
    params = {
        "money_code": money_code,
        "type": "0",
        "startdate": "-".join([start_date[:4], start_date[4:6], start_date[6:]]),
        "enddate": "-".join([end_date[:4], end_date[4:6], end_date[6:]]),
        "page": "1",
        "call_type": "ajax",
    }
    
    # 获取数据
    big_df = pd.DataFrame()
    try:
        r = requests.get(url, params=params)
        soup = BeautifulSoup(r.text, "lxml")
        page_element_list = soup.find_all("a", attrs={"class": "page"})
        page_num = int(page_element_list[-2].text) if len(page_element_list) != 0 else 1
    except Exception as e:
        print(f"⚠️  获取页码失败: {e}")
        return pd.DataFrame()
    
    for page in tqdm(range(1, page_num + 1), leave=False):
        params.update({"page": page})
        try:
            r = requests.get(url, params=params)
            temp_df = pd.read_html(StringIO(r.text), header=0)[0]
            big_df = pd.concat([big_df, temp_df], ignore_index=True)
        except Exception as e:
            print(f"⚠️  获取第{page}页数据失败: {e}")
            continue
    
    # 动态处理列名，适应可能的列数变化
    if len(big_df.columns) == 6:
        big_df.columns = ["日期", "中行汇买价", "中行钞买价", "中行钞卖价", "中行汇卖价", "央行中间价"]
    elif len(big_df.columns) == 5:
        big_df.columns = ["日期", "中行汇买价", "中行钞买价", "中行钞卖价/汇卖价", "央行中间价"]
    else:
        print(f"⚠️  未知列数: {len(big_df.columns)}，列名: {big_df.columns.tolist()}")
        return pd.DataFrame()
    
    # 数据类型转换
    big_df["日期"] = pd.to_datetime(big_df["日期"], errors="coerce").dt.date
    numeric_columns = big_df.columns[1:]
    for col in numeric_columns:
        big_df[col] = pd.to_numeric(big_df[col], errors="coerce")
    
    big_df.sort_values(by=["日期"], inplace=True, ignore_index=True)
    return big_df

def safe_get_data(func, *args, **kwargs):
    """安全获取数据，失败时返回空DataFrame"""
    try:
        data = func(*args, **kwargs)
        if data is None or (hasattr(data, 'empty') and data.empty):
            print(f"⚠️  数据获取失败: {func.__name__}")
            return pd.DataFrame()
        return data
    except Exception as e:
        print(f"⚠️  数据获取异常 {func.__name__}: {str(e)[:100]}")
        return pd.DataFrame()

def validate_data(data, min_points=10):
    """验证数据有效性"""
    if data is None or (hasattr(data, 'empty') and data.empty) or len(data) < min_points:
        return False
    return True

def generate_and_save_plot(ticker, filename, period="1mo"):
    """生成K线图"""
    try:
        data = yf.Ticker(ticker).history(period=period)
        if validate_data(data, 5):
            filepath = os.path.join(OUTPUT_DIR, filename)
            mpf.plot(data, type='candle', figscale=0.4, volume=False, 
                    savefig=filepath, datetime_format='%m-%d')
            print(f"✅ K线图: {filename}")
        else:
            print(f"❌ 数据不足: {ticker}")
    except Exception as e:
        print(f"❌ K线图失败 {ticker}: {e}")

def get_data(symbol, start_date, end_date):
    """获取指定符号的历史数据（带错误处理）"""
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
    """对数据进行归一化处理"""
    try:
        if validate_data(data, 2):
            return (data - data.min()) / (data.max() - data.min())
    except:
        pass
    return pd.Series(dtype=float)

def plot_data(data_dict, title, labels, colors, linewidths=None, save_path=None):
    """绘制数据图表（带错误处理）"""
    try:
        valid_data = {k: v for k, v in data_dict.items() if validate_data(v, 5)}
        if not valid_data:
            print(f"❌ 无有效数据: {title}")
            return
        
        fig, ax = plt.subplots(figsize=(20, 15))
        for i, (key, values) in enumerate(valid_data.items()):
            linewidth = linewidths[i] if linewidths else 2.0
            ax.plot(values.index, values, color=colors[i], 
                   label=labels[i], linewidth=linewidth)
        
        ax.set_title(title, fontsize='xx-large', fontweight='heavy')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        plt.gcf().autofmt_xdate()
        
        if save_path:
            filepath = os.path.join(OUTPUT_DIR, save_path)
            plt.savefig(filepath)
            print(f"✅ 图表: {save_path}")
        plt.show()
        plt.clf()
    except Exception as e:
        print(f"❌ 绘图失败 {title}: {e}")
        plt.clf()

def plot_oil_gold_bond():
    """绘制油金比和美债收益率图表"""
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
        
        fig, ax1 = plt.subplots(figsize=(20, 15))
        ax2 = ax1.twinx()
        
        ax1.plot(oil_gold_ratio, 'r-', label='Oil/Gold Ratio')
        ax1.set_ylabel('Oil/Gold Ratio', color='r')
        
        ax2.plot(us_bond, 'b-', label='US 10Y Yield')
        ax2.set_ylabel('US 10Y Yield (%)', color='b')
        
        plt.title('Oil/Gold Ratio vs US 10Y Treasury Yield Trend', pad=20)
        ax1.grid(True, alpha=0.3)
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper left')
        plt.gcf().autofmt_xdate()
        
        filepath = os.path.join(OUTPUT_DIR, 'jyb_gz.png')
        plt.savefig(filepath)
        print("✅ 图表: jyb_gz.png")
        plt.show()
        plt.clf()
    except Exception as e:
        print(f"❌ 油金比图表失败: {e}")
        plt.clf()

def plot_pe_bond_spread():
    """绘制股债利差图表"""
    try:
        bond_df = safe_get_data(ak.bond_zh_us_rate, start_date="20121219")
        pe_df = safe_get_data(ak.stock_index_pe_lg, symbol="上证50")
        
        if bond_df.empty or pe_df.empty:
            print("❌ 债券或PE数据获取失败")
            return
        
        if not all(col in bond_df.columns for col in ['日期', '中国国债收益率10年']):
            print("❌ 债券数据缺少必要列")
            return
        
        if not all(col in pe_df.columns for col in ['日期', '滚动市盈率']):
            print("❌ PE数据缺少必要列")
            return
        
        bond_df['日期'] = pd.to_datetime(bond_df['日期'], errors='coerce')
        pe_df['日期'] = pd.to_datetime(pe_df['日期'], errors='coerce')
        
        bond_10y = bond_df.dropna().set_index('日期')['中国国债收益率10年']
        pe_ratio = pe_df.dropna().set_index('日期')['滚动市盈率']
        
        # 对齐日期
        common_idx = bond_10y.index.intersection(pe_ratio.index)
        if len(common_idx) < 100:
            print("❌ 日期交集数据不足")
            return
        
        spread = bond_10y.loc[common_idx] - 100 / pe_ratio.loc[common_idx]
        spread = spread.ffill().dropna()
        
        if not validate_data(spread, 50):
            print("❌ 股债利差数据不足")
            return
        
        fig, ax = plt.subplots(figsize=(20, 15))
        spread.plot(ax=ax, color='white', linewidth=2, title='股债利差')
        
        plt.axhline(y=-2.6, ls=":", c="red", label="高息")
        plt.axhline(y=-5.5, ls=":", c="green", label="正常")
        plt.axhline(y=-7.8, ls=":", c="blue", label="低息")
        plt.axhline(y=-4.5, ls=":", c="gray")
        plt.axhline(y=-6.8, ls=":", c="gray")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        filepath = os.path.join(OUTPUT_DIR, 'guzhaixicha.png')
        plt.savefig(filepath)
        print("✅ 图表: guzhaixicha.png")
        plt.show()
        plt.clf()
    except Exception as e:
        print(f"❌ 股债利差图表失败: {e}")
        plt.clf()

def main():
    """主执行函数"""
    print("="*70)
    print("金融数据分析程序启动")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    success_count = 0
    total_tasks = 0
    
    # 任务1: 生成指数K线图
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
                
                fig, ax = plt.subplots(figsize=(20,15))
                ax.plot(df.index, df['HSI']/df['HSI'].iloc[0], label='HSI (归一化)', color='#3498db')
                ax.plot(df.index, df['RUT']/df['RUT'].iloc[0], label='RUT (归一化)', color='#e74c3c')
                ax.set_title('恒生指数与Russell 2000走势对比', fontsize=16, fontweight='heavy')
                ax.legend()
                ax.grid(alpha=0.3)
                
                filepath = os.path.join(OUTPUT_DIR, 'hsi_rut_comparison.png')
                plt.savefig(filepath, dpi=300, bbox_inches='tight')
                print("✅ 图表: hsi_rut_comparison.png")
                plt.show()
                plt.clf()
                
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
    print(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print("="*70)
    
    return success_count, total_tasks

if __name__ == "__main__":
    main()
