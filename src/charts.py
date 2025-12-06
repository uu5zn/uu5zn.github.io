# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import numpy as np
import os
from config import OUTPUT_DIR, MPL_STYLE
from utils import validate_data

class ChartGenerator:
    def __init__(self, logger_callback):
        """
        图表生成器
        :param logger_callback: 日志回调函数
        """
        self.logger = logger_callback
        self.setup_matplotlib()
    
    def setup_matplotlib(self):
        """配置matplotlib"""
        plt.rcParams.update(MPL_STYLE)
    
    def plot_kline(self, ticker, filename, period="1mo"):
        """
        生成K线图
        :param ticker: 股票代码
        :param filename: 输出文件名
        :param period: 周期
        """
        try:
            import yfinance as yf
            
            data = yf.Ticker(ticker).history(period=period)
            if not validate_data(data, 5):
                self.logger('K线图', 'warning', f'{ticker} 数据不足')
                return False
            
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
            self.logger('K线图', 'success', f'{ticker} -> {filename}', chart_path=filename)
            return True
            
        except Exception as e:
            print(f"❌ K线图失败 {ticker}: {e}")
            self.logger('K线图', 'error', f'{ticker}: {str(e)}')
            return False
    
    def plot_line(self, data_dict, title, labels, colors, linewidths=None, save_path=None):
        """
        绘制折线图
        :param data_dict: 数据字典
        :param title: 图表标题
        :param labels: 标签列表
        :param colors: 颜色列表
        :param linewidths: 线宽列表
        :param save_path: 保存路径
        """
        try:
            valid_data = {k: v for k, v in data_dict.items() if validate_data(v, 5)}
            if not valid_data:
                self.logger('绘图', 'warning', f'{title} 无有效数据')
                return False
            
            fig, ax = plt.subplots(figsize=(20, 12), facecolor='black')
            
            for i, (key, values) in enumerate(valid_data.items()):
                linewidth = linewidths[i] if linewidths else 1.5
                ax.plot(values.index, values, color=colors[i], 
                       label=labels[i], linewidth=linewidth)
            
            ax.set_title(title, fontsize=13, fontweight='heavy', pad=8)
            ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
            ax.grid(True, alpha=0.3, color='#666666')
            
            plt.gcf().autofmt_xdate(rotation=45, ha='right')
            plt.tight_layout(pad=0.8, h_pad=0.8, w_pad=0.8)
            
            if save_path:
                filepath = os.path.join(OUTPUT_DIR, save_path)
                plt.savefig(filepath, bbox_inches='tight', pad_inches=0.1, 
                           facecolor='black', dpi=150)
                print(f"✅ 图表: {save_path}")
                self.logger('绘图', 'success', f'{title} -> {save_path}', chart_path=save_path)
            
            plt.close(fig)
            return True
            
        except Exception as e:
            print(f"❌ 绘图失败 {title}: {e}")
            self.logger('绘图', 'error', f'{title}: {str(e)}')
            plt.close('all')
            return False
    
    def plot_sector_rotation(self, sorted_returns):
        """
        绘制行业轮动图
        :param sorted_returns: 排序后的收益率列表
        """
        try:
            if not sorted_returns:
                return False
            
            sectors, rets = zip(*sorted_returns)
            colors = ['#e74c3c' if r > 0 else '#2ecc71' for r in rets]
            
            fig, ax = plt.subplots(figsize=(16, 10), facecolor='black')
            bars = ax.barh(range(len(sectors)), rets, color=colors, alpha=0.8)
            
            ax.set_yticks(range(len(sectors)))
            ax.set_yticklabels(sectors)
            ax.set_xlabel('收益率 (%)', color='white')
            ax.set_title('行业ETF近1月表现', fontsize=14, fontweight='heavy', pad=12)
            ax.grid(axis='x', alpha=0.3, color='#666666')
            
            # 添加数值标签
            for i, ret in enumerate(rets):
                ax.text(ret + (0.2 if ret > 0 else -0.2), i, f'{ret:+.2f}%', 
                       va='center', ha='left' if ret > 0 else 'right', color='white')
            
            plt.tight_layout(pad=0.8)
            
            filepath = os.path.join(OUTPUT_DIR, 'sector_rotation.png')
            plt.savefig(filepath, bbox_inches='tight', pad_inches=0.1, 
                       facecolor='black', dpi=150)
            print("✅ 图表: sector_rotation.png")
            plt.close(fig)
            
            return True
            
        except Exception as e:
            print(f"❌ 行业轮动图失败: {e}")
            self.logger('行业轮动图', 'error', str(e))
            plt.close('all')
            return False
    
    def plot_oil_gold_ratio(self):
        """绘制油金比与美债收益率"""
        try:
            oil_prices = self.fetcher.get_data("CL", None, None)
            gold_prices = self.fetcher.get_data("GC", None, None)
            
            if not (validate_data(oil_prices, 50) and validate_data(gold_prices, 50)):
                self.logger('油金比', 'warning', '数据不足')
                return False
            
            oil_prices, gold_prices = oil_prices.align(gold_prices, join='inner')
            if not validate_data(oil_prices, 30):
                return False
            
            oil_gold_ratio = oil_prices / gold_prices
            us_bond = self.fetcher.get_data('US_BOND', None, None)
            
            if not validate_data(us_bond, 30):
                return False
            
            # 限制数据长度
            us_bond = us_bond.iloc[-300:] if len(us_bond) > 300 else us_bond
            oil_gold_ratio = oil_gold_ratio.iloc[-300:] if len(oil_gold_ratio) > 300 else oil_gold_ratio
            
            fig, ax1 = plt.subplots(figsize=(20, 12), facecolor='black')
            ax2 = ax1.twinx()
            
            line1 = ax1.plot(oil_gold_ratio, 'r-', label='Oil/Gold Ratio', linewidth=1.5)
            ax1.set_ylabel('Oil/Gold Ratio', color='r', fontsize=10)
            
            line2 = ax2.plot(us_bond, 'b-', label='US 10Y Yield', linewidth=1
