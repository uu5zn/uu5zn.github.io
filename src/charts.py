# -*- coding: utf-8 -*-
import pandas as pd  # 🔧 添加


import numpy as np
import akshare as ak  # 🔧 添加
import os
from config import OUTPUT_DIR, MPL_STYLE
from utils import validate_data
import matplotlib.pyplot as plt
import mplfinance as mpf





   
class ChartGenerator:
    def __init__(self, logger_callback, data_fetcher=None):
        """
        图表生成器
        :param logger_callback: 日志回调函数
        :param data_fetcher: 数据获取器实例（可选）
        """
        self.logger = logger_callback
        self.fetcher = data_fetcher
        # 保存当前所有字体相关配置，避免被样式覆盖
        current_font_config = {
            'font.family': plt.rcParams.get('font.family', []),
            'font.sans-serif': plt.rcParams.get('font.sans-serif', []),
            'font.size': plt.rcParams.get('font.size', 9),
            'axes.titlesize': plt.rcParams.get('axes.titlesize', 13),
            'axes.labelsize': plt.rcParams.get('axes.labelsize', 10),
            'legend.fontsize': plt.rcParams.get('legend.fontsize', 8),
            'xtick.labelsize': plt.rcParams.get('xtick.labelsize', 8),
            'ytick.labelsize': plt.rcParams.get('ytick.labelsize', 8),
            'axes.unicode_minus': plt.rcParams.get('axes.unicode_minus', False)
        }
        # 应用样式配置
        plt.rcParams.update(MPL_STYLE)
        # 恢复所有字体相关配置
        plt.rcParams.update(current_font_config)
    
    def plot_kline(self, ticker, filename, period="1mo"):
        """生成K线图"""
        try:
            import yfinance as yf
            
            data = yf.Ticker(ticker).history(period=period)
            if not validate_data(data, 5):
                self.logger('K线图', 'warning', f'{ticker} 数据不足')
                return False
            
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            # 在 rc 参数中设置字体，而不是使用 title_fontdict
            style = mpf.make_mpf_style(
                base_mpf_style='charles',
                marketcolors=mpf.make_marketcolors(up='#e74c3c', down='#2ecc71', edge='inherit'),
                facecolor='black', edgecolor='white', figcolor='black',
                gridcolor='#666666', gridstyle='--',
                rc={
                    'font.size': 8,
                    'font.family': plt.rcParams['font.sans-serif'][0]  # 设置中文字体
                }
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
        """绘制折线图"""
        try:
            valid_data = {k: v for k, v in data_dict.items() if validate_data(v, 5)}
            if not valid_data:
                self.logger('绘图', 'warning', f'{title} 无有效数据')
                return False
            
            fig, ax = plt.subplots(figsize=(20, 12), facecolor='black')
            
            # 设置标题和标签字体
            title_font = plt.rcParams['font.sans-serif'][0]
            ax.set_title(title, fontsize=13, fontweight='heavy', pad=8, fontname=title_font)
            
            for i, (key, values) in enumerate(valid_data.items()):
                linewidth = linewidths[i] if linewidths else 1.5
                ax.plot(values.index, values, color=colors[i], 
                       label=labels[i], linewidth=linewidth)
            
            # 设置图例字体
            legend = ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
            for text in legend.get_texts():
                text.set_fontname(title_font)
            
            ax.grid(True, alpha=0.3, color='#666666')
            
            # 设置坐标轴标签字体
            ax.set_xlabel(ax.get_xlabel(), fontname=title_font)
            ax.set_ylabel(ax.get_ylabel(), fontname=title_font)
            
            # 设置刻度标签字体
            for label in ax.get_xticklabels():
                label.set_fontname(title_font)
            for label in ax.get_yticklabels():
                label.set_fontname(title_font)
            
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
        """绘制行业轮动图"""
        try:
            if not sorted_returns:
                return False
            
            sectors, rets = zip(*sorted_returns)
            colors = ['#e74c3c' if r > 0 else '#2ecc71' for r in rets]
            
            fig, ax = plt.subplots(figsize=(16, 10), facecolor='black')
            bars = ax.barh(range(len(sectors)), rets, color=colors, alpha=0.8)
            
            # 设置字体
            title_font = plt.rcParams['font.sans-serif'][0]
            
            ax.set_yticks(range(len(sectors)))
            # 直接设置yticklabels时指定字体
            ax.set_yticklabels(sectors, fontname=title_font)
            ax.set_xlabel('收益率 (%)', color='white', fontname=title_font)
            ax.set_title('行业ETF近1月表现', fontsize=14, fontweight='heavy', pad=12, fontname=title_font)
            ax.grid(axis='x', alpha=0.3, color='#666666')
            
            # 设置坐标轴标签字体
            ax.set_xlabel(ax.get_xlabel(), fontname=title_font)
            ax.set_ylabel(ax.get_ylabel(), fontname=title_font)
            
            # 设置刻度标签字体（双重保险）
            for label in ax.get_xticklabels():
                label.set_fontname(title_font)
            for label in ax.get_yticklabels():
                label.set_fontname(title_font)
            
            # 添加数值标签
            for i, ret in enumerate(rets):
                ax.text(ret + (0.2 if ret > 0 else -0.2), i, f'{ret:+.2f}%', 
                       va='center', ha='left' if ret > 0 else 'right', color='white', fontname=title_font)
            
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
            # 使用 self.fetcher
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
            
            us_bond = us_bond.iloc[-300:] if len(us_bond) > 300 else us_bond
            oil_gold_ratio = oil_gold_ratio.iloc[-300:] if len(oil_gold_ratio) > 300 else oil_gold_ratio
            
            fig, ax1 = plt.subplots(figsize=(20, 12), facecolor='black')
            ax2 = ax1.twinx()
            
            # 设置字体
            title_font = plt.rcParams['font.sans-serif'][0]
            
            line1 = ax1.plot(oil_gold_ratio, 'r-', label='Oil/Gold Ratio', linewidth=1.5)
            ax1.set_ylabel('Oil/Gold Ratio', color='r', fontsize=10, fontname=title_font)
            
            line2 = ax2.plot(us_bond, 'b-', label='US 10Y Yield', linewidth=1.5)
            ax2.set_ylabel('US 10Y Yield (%)', color='b', fontsize=10, fontname=title_font)
            
            plt.title('Oil/Gold Ratio vs US 10Y Treasury Yield Trend', 
                     fontsize=13, fontweight='heavy', pad=8, fontname=title_font)
            
            ax1.grid(True, alpha=0.3, color='#666666')
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            legend = ax1.legend(lines, labels, loc='upper left', fontsize=8)
            for text in legend.get_texts():
                text.set_fontname(title_font)
            
            # 设置坐标轴标签字体
            ax1.set_xlabel(ax1.get_xlabel(), fontname=title_font)
            ax2.set_xlabel(ax2.get_xlabel(), fontname=title_font)
            
            # 设置刻度标签字体
            for label in ax1.get_xticklabels():
                label.set_fontname(title_font)
            for label in ax1.get_yticklabels():
                label.set_fontname(title_font)
            for label in ax2.get_yticklabels():
                label.set_fontname(title_font)
            
            plt.gcf().autofmt_xdate(rotation=45, ha='right')
            plt.tight_layout(pad=0.8)
            
            filepath = os.path.join(OUTPUT_DIR, 'jyb_gz.png')
            plt.savefig(filepath, bbox_inches='tight', pad_inches=0.1, 
                       facecolor='black', dpi=150)
            print("✅ 图表: jyb_gz.png")
            plt.close(fig)
            
            return True
            
        except Exception as e:
            print(f"❌ 油金比图表失败: {e}")
            self.logger('油金比', 'error', str(e))
            plt.close('all')
            return False
    
    def plot_pe_bond_spread(self):
        """绘制股债利差图"""
        try:
            # 使用 self.fetcher
            bond_df = self.fetcher.safe_get_data(ak.bond_zh_us_rate, start_date="20121219")
            pe_df = self.fetcher.safe_get_data(ak.stock_index_pe_lg, symbol="上证50")
            
            if bond_df.empty or pe_df.empty:
                self.logger('股债利差', 'warning', '数据获取失败')
                return False
            
            # 数据验证
            if '日期' not in bond_df.columns or '中国国债收益率10年' not in bond_df.columns:
                self.logger('股债利差', 'warning', '债券数据缺少列')
                return False
            if '日期' not in pe_df.columns or '滚动市盈率' not in pe_df.columns:
                self.logger('股债利差', 'warning', 'PE数据缺少列')
                return False
            
            # 数据清洗
            bond_df['日期'] = pd.to_datetime(bond_df['日期'], errors='coerce')
            pe_df['日期'] = pd.to_datetime(pe_df['日期'], errors='coerce')
            
            bond_10y = bond_df.dropna().set_index('日期')['中国国债收益率10年']
            pe_ratio = pe_df.dropna().set_index('日期')['滚动市盈率']
            
            # 对齐日期
            common_idx = bond_10y.index.intersection(pe_ratio.index)
            if len(common_idx) < 100:
                self.logger('股债利差', 'warning', '日期交集不足')
                return False
            
            # 计算利差
            spread = bond_10y.loc[common_idx] - 100 / pe_ratio.loc[common_idx]
            spread = spread.ffill().dropna()
            
            if not validate_data(spread, 50):
                return False
            
            # 设置字体
            title_font = plt.rcParams['font.sans-serif'][0]
            
            # 绘图
            fig, ax = plt.subplots(figsize=(20, 12), facecolor='black')
            spread.plot(ax=ax, color='white', linewidth=1.5)
            ax.set_title('股债利差', fontsize=13, fontweight='heavy', pad=8, fontname=title_font)
            
            # 参考线
            for y, color, label in [
                (-2.6, 'red', '高息'), (-5.5, 'green', '正常'), 
                (-7.8, 'blue', '低息'), (-4.5, 'gray', ''), (-6.8, 'gray', '')
            ]:
                ax.axhline(y=y, ls=":", c=color, label=label if label else None, alpha=0.7)
            
            legend = ax.legend(fontsize=8, loc='upper left')
            for text in legend.get_texts():
                text.set_fontname(title_font)
            
            ax.grid(True, alpha=0.3, color='#666666')
            
            # 设置坐标轴标签字体
            ax.set_xlabel(ax.get_xlabel(), fontname=title_font)
            ax.set_ylabel(ax.get_ylabel(), fontname=title_font)
            
            # 设置刻度标签字体
            for label in ax.get_xticklabels():
                label.set_fontname(title_font)
            for label in ax.get_yticklabels():
                label.set_fontname(title_font)
            
            plt.gcf().autofmt_xdate(rotation=45, ha='right')
            plt.tight_layout(pad=0.8)
            
            filepath = os.path.join(OUTPUT_DIR, 'guzhaixicha.png')
            plt.savefig(filepath, bbox_inches='tight', pad_inches=0.1, 
                       facecolor='black', dpi=150)
            print("✅ 图表: guzhaixicha.png")
            plt.close(fig)
            
            return True
            
        except Exception as e:
            print(f"❌ 股债利差图表失败: {e}")
            self.logger('股债利差', 'error', str(e))
            plt.close('all')
            return False
