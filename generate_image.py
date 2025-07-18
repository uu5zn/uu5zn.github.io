# -*- coding: utf-8 -*-
import mplfinance as mpf
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta

# 设置全局字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False



# 生成并保存图片的函数
def generate_and_save_plot(ticker, filename, period="1mo"):
    data = yf.Ticker(ticker).history(period=period)
    mpf.plot(data, type='candle', figscale=0.4, volume=False, savefig=filename,datetime_format='%m-%d')




# 数据获取函数
def get_data(symbol, start_date, end_date):
    """
    获取指定符号的历史数据
    """
    if symbol == '美元':
        data = ak.currency_boc_sina(symbol=symbol, start_date=start_date, end_date=end_date)
        data.set_index("日期", inplace=True)
        return data['央行中间价']
    elif symbol == '融资余额':
        data = ak.stock_margin_sse(start_date=start_date, end_date=end_date)
        data = data.iloc[:, [0, 1]].iloc[::-1]
        data['信用交易日期'] = pd.to_datetime(data['信用交易日期'], format='%Y%m%d')
        data.set_index('信用交易日期', inplace=True)
        return data
    elif symbol == 'Shibor 1M':
        data = ak.macro_china_shibor_all()
        data['日期'] = pd.to_datetime(data['日期'], format='%Y-%m-%d')
        data.set_index('日期', inplace=True)
        return data[['1M-定价']]
    elif symbol == '中美国债收益率':
        data = ak.bond_zh_us_rate().tail(220)
        data['日期'] = pd.to_datetime(data['日期'], format='%Y-%m-%d')
        data.set_index('日期', inplace=True)
        data = data.ffill(axis=0)
        data['spread'] = data['中国国债收益率10年'] - data['美国国债收益率10年']
        return data
    elif symbol.startswith('ETF'):
        etf_code = symbol.split('_')[1]
        data = ak.fund_etf_hist_em(symbol=etf_code).iloc[-220:]
        data['日期'] = pd.to_datetime(data['日期'], format='%Y-%m-%d')
        data.set_index('日期', inplace=True)
        return data['收盘']
    elif symbol in ['CL', 'GC']:
        df = ak.futures_foreign_hist(symbol=symbol)
        return df.set_index('date')['close']
    elif symbol == 'US_BOND':
        bond_df = ak.bond_zh_us_rate()
        bond_df['日期'] = pd.to_datetime(bond_df['日期'])
        us_bond = bond_df.sort_values('日期').set_index('日期')['美国国债收益率10年'].ffill()
        return us_bond
    else:
        raise ValueError("不支持的数据类型")

# 归一化函数
def normalize(data):
    """
    对数据进行归一化处理
    """
    return (data - data.min()) / (data.max() - data.min())

# 绘图函数
def plot_data(data, title, labels, colors, linewidths=None, save_path=None):
    """
    绘制数据图表
    """
    fig = plt.figure(figsize=(20, 15))
    ax = fig.subplots()
    if linewidths is None:
        linewidths = [2.0] * len(data)
    for i, (key, values) in enumerate(data.items()):
        ax.plot(values.index, values, colors[i], label=labels[i], linewidth=linewidths[i])
    ax.set_title(title, fontsize='xx-large', fontweight='heavy')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    plt.gcf().autofmt_xdate()
    if save_path:
        plt.savefig(save_path)
    plt.show()
    plt.clf()

# 绘制油金比和美债收益率图表
def plot_oil_gold_bond():
    # 获取并处理原油和黄金数据
    oil_prices = get_data("CL", None, None).iloc[-300:]
    gold_prices = get_data("GC", None, None).iloc[-300:]
    oil_prices, gold_prices = oil_prices.align(gold_prices, join='inner')  # 确保日期对齐
    oil_gold_ratio = oil_prices / gold_prices

    # 获取并处理美债数据
    us_bond = get_data('US_BOND', None, None).iloc[-300:]

    # 创建未来25天的预测数据（带日期偏移）
    us_bond_shifted = us_bond.shift(-25, freq='D')

    # 创建图表
    fig, ax1 = plt.subplots(figsize=(20, 15))
    ax2 = ax1.twinx()

    # 绘制油金比
    ax1.plot(oil_gold_ratio, 'r-', label='Oil/Gold Ratio')
    ax1.set_ylabel('Oil/Gold Ratio', color='r')

    # 绘制美债收益率
    ax2.plot(us_bond, 'b-', label='US 10Y Yield')
    ax2.plot(us_bond_shifted, 'b:', label='Future US 10Y Yield')
    ax2.set_ylabel('US 10Y Yield (%)', color='b')

    # 设置图形属性
    plt.title('Oil/Gold Ratio vs US 10Y Treasury Yield Trend', pad=20)
    ax1.grid(True, alpha=0.3)
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left')

    # 自动调整日期显示格式
    plt.gcf().autofmt_xdate()
    plt.savefig('jyb_gz.png')

    plt.show()

# 主程序
if __name__ == "__main__":
    # 设置时间范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=300)
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    # 生成图片
    generate_and_save_plot("^TNX", "tenbond.png")
    generate_and_save_plot("^VIX", "vix.png", period="2mo")
    generate_and_save_plot("^GSPC", "sp500.png")
    generate_and_save_plot("^IXIC", "nasdaq.png")
    generate_and_save_plot("^RUT", "rs2000.png")
    generate_and_save_plot("VNQ", "vnq.png")
    generate_and_save_plot("^N225", "nikkei225.png")
    generate_and_save_plot("^HSI", "hsi.png")
    generate_and_save_plot("CNY=X", "rmb.png")


    # 获取数据
    exchange_rate = get_data('美元', start_date_str, end_date_str)
    margin_data = get_data('融资余额', start_date_str, end_date_str)
    shibor_data = get_data('Shibor 1M', start_date_str, end_date_str)
    bond_data = get_data('中美国债收益率', start_date_str, end_date_str)
    etf_300 = get_data('ETF_510300', start_date_str, end_date_str)
    etf_1000 = get_data('ETF_159845', start_date_str, end_date_str)
    etf_500 = get_data('ETF_510500', start_date_str, end_date_str)

    # 计算指标
    margin_data['ma10'] = margin_data['融资余额'].rolling(10).mean()

    # 归一化处理
    margin_normalized = normalize(margin_data['融资余额'])
    exchange_rate_normalized = normalize(-exchange_rate)
    bond_spread_normalized = normalize(bond_data['spread'])
    etf_300_normalized = normalize(etf_300)
    etf_1000_normalized = normalize(etf_1000)
    etf_500_normalized = normalize(etf_500)

    # 绘制第一张图表
    plot_data(
        {
            '融资余额': margin_normalized,
            '汇率': exchange_rate_normalized,
            '中美利差': bond_spread_normalized,
            '500ETF': etf_500_normalized
        },
        '归一化后的融资余额、汇率、中美利差和500ETF收盘价',
        ['rzye', 'huilv', 'cnUS', '500ETF'],
        ['g', 'c', 'k', 'r'],
        save_path='rongziyue_1.png'
    )

    # 绘制第二张图表
    plot_data(
        {
            '融资余额': margin_normalized,
            '300ETF': etf_300_normalized,
            '1000ETF': etf_1000_normalized
        },
        'rzye、300&1000ETF',
        ['rzye', '300ETF', '1000ETF'],
        ['g', 'r', 'b'],
        save_path='rongziyue_2.png'
    )

    # 绘制第三张图表
    plot_data(
        {
            'Shibor 1M': normalize(shibor_data['1M-定价'].iloc[-200:]),
            '中美国债收益率差': normalize(bond_data['spread'].iloc[-200:])
        },
        'rate',
        ['Shibor 1M', 'cnUS'],
        ['k', 'g'],
        save_path='liudongxing.png'
    )

    # 绘制第四张图表
    plot_data(
        {
            '融资余额': margin_data['融资余额'].iloc[-50:],
            'ma10': margin_data['ma10'].iloc[-50:]
        },
        'rzye',
        ['rzye', 'MA10'],
        ['r', 'b'],
        save_path='rongziyue_ma.png'
    )

    # 绘制油金比和美债收益率图表
    plot_oil_gold_bond()

    # 判断条件并发出警告
    if bond_data['spread'].diff().iloc[-1] > 0 and shibor_data['1M-定价'].diff().iloc[-1] < 0:
        print("\x1b[31m注意：国内剩余流动性激增，股市预受损\x1b[0m")

    # 获取最新数据
    last_margin = round(margin_data.iloc[-1:] / 1000000)
    print("最新融资余额:", last_margin)

    # 判断融资余额是否低于10日移动平均线
    if last_margin['融资余额'].iloc[-1] < last_margin['ma10'].iloc[-1]:
        print("\x1b[31m注意：风险偏好下资金流出!!!\x1b[0m")

    hsi_df = yf.download('^HSI', period='300d', interval='1d')
    rsi2000_df = yf.download('^RUT', period='300d', interval='1d')
    
    # 统一索引为日期
    hsi_df = hsi_df[['Close']].copy()
    rsi2000_df = rsi2000_df[['Close']].copy()
    hsi_df.index = pd.to_datetime(hsi_df.index)
    rsi2000_df.index = pd.to_datetime(rsi2000_df.index)
    
    # 对齐日期
    df = pd.concat([hsi_df, rsi2000_df], axis=1, join='inner', keys=['HSI', 'RUT'])
    df.columns = ['HSI_Close', 'RUT_Close']
    
    # 计算相关性
    correlation = df['HSI_Close'].corr(df['RUT_Close'])
    print(f"恒生指数与Russell 2000指数的相关性: {correlation:.4f}")
    
    
    # 可视化两个指数走势
    plt.figure(figsize=(14,5))
    plt.plot(df.index, df['HSI_Close']/df['HSI_Close'].iloc[0], label='HSI (归一化)')
    plt.plot(df.index, df['RUT_Close']/df['RUT_Close'].iloc[0], label='RUT (归一化)')
    plt.title('恒生指数与Russell 2000指数走势对比')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig('hsi_rut_comparison.png', dpi=300, bbox_inches='tight')




