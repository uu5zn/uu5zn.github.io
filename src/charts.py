# -*- coding: utf-8 -*-
import pandas as pd  # 🔧 添加


import numpy as np
import os
import json
from datetime import datetime
from .config import OUTPUT_DIR, MPL_STYLE
from .utils import validate_data
import matplotlib.pyplot as plt
import mplfinance as mpf





   
class ChartGenerator:
    def __init__(self, logger_callback):
        """
        图表生成器
        :param logger_callback: 日志回调函数
        """
        self.logger = logger_callback
        self.cache_dir = os.path.join(OUTPUT_DIR, 'data_cache')
        self.cache_validity = 24 * 3600  # 缓存有效期（秒）
    
    def _is_cache_valid(self):
        """检查缓存是否有效"""
        cache_meta_file = os.path.join(self.cache_dir, 'cache_meta.json')
        if os.path.exists(cache_meta_file):
            try:
                with open(cache_meta_file, 'r') as f:
                    meta = json.load(f)
                cache_time = meta.get('cache_time', 0)
                current_time = datetime.now().timestamp()
                return current_time - cache_time < self.cache_validity
            except:
                pass
        return False
    
    def _load_cached_data(self):
        """加载所有缓存数据"""
        data_file = os.path.join(self.cache_dir, 'all_data.pkl')
        if os.path.exists(data_file):
            try:
                all_data = pd.read_pickle(data_file)
                return all_data
            except Exception as e:
                self.logger('数据缓存', 'error', f'加载缓存失败: {e}')
        return {}
    
    def get_cached_data(self, symbol):
        """
        从缓存获取数据
        """
        all_data = self._load_cached_data()
        return all_data.get(symbol, pd.Series(dtype=float))
    
    def plot_kline(self, ticker, filename, period="1mo"):
        """生成K线图"""
        try:
            # 从缓存获取数据
            close_data = self.get_cached_data(ticker)
            
            # 增强数据验证，确保数据有效且包含收盘价
            if not validate_data(close_data, 5):
                self.logger('K线图', 'warning', f'{ticker} 数据不足')
                print(f"⚠️  {ticker} 数据不足，跳过绘制")
                return False
            
            # 检查是否包含有效收盘价数据
            if close_data.isna().all():
                self.logger('K线图', 'warning', f'{ticker} 无有效收盘价数据')
                print(f"⚠️  {ticker} 无有效收盘价数据，跳过绘制")
                return False
            
            # 由于缓存中只有Close数据，我们创建一个简单的K线数据结构
            # 实际应用中，可能需要从data_fetcher获取完整的OHLC数据
            data = pd.DataFrame({
                'Open': close_data,
                'High': close_data,
                'Low': close_data,
                'Close': close_data,
                'Volume': 0
            })
            
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # 获取当前可用的中文字体
            current_font = plt.rcParams['font.sans-serif'][0]
            print(f"📊 绘制K线图 - 使用字体: {current_font}")
            
            # 为mplfinance创建样式，确保使用正确的中文字体
            # 首先保存当前的rcParams
            original_rc = plt.rcParams.copy()
            
            # 强制设置mplfinance使用正确的中文字体
            mpf_rc = {
                'font.size': 8,
                'font.family': 'sans-serif',
                'font.sans-serif': [current_font],
                'axes.unicode_minus': False,
                'figure.facecolor': 'black',
                'axes.facecolor': 'black',
                'savefig.facecolor': 'black',
            }
            
            # 更新全局rcParams以确保mplfinance使用正确字体
            plt.rcParams.update(mpf_rc)
            
            style = mpf.make_mpf_style(
                base_mpf_style='charles',
                marketcolors=mpf.make_marketcolors(up='#e74c3c', down='#2ecc71', edge='inherit'),
                facecolor='black', edgecolor='white', figcolor='black',
                gridcolor='#666666', gridstyle='--',
                rc=mpf_rc
            )
            
            mpf.plot(
                data, type='candle', figscale=0.35, volume=False,
                savefig=dict(fname=filepath, dpi=150, bbox_inches='tight'),
                datetime_format='%m-%d', style=style,
                title=ticker, tight_layout=True,
                warn_too_much_data=1000
            )
            
            # 恢复原始rcParams
            plt.rcParams.update(original_rc)
            
            # 验证文件是否生成成功
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"✅ K线图: {filename} (路径: {filepath}, 大小: {file_size} 字节)")
                self.logger('K线图', 'success', f'{ticker} -> {filename}', chart_path=filename)
                return True
            else:
                print(f"❌ K线图: {filename} 生成失败，文件不存在")
                self.logger('K线图', 'error', f'{ticker}: 生成失败，文件不存在')
                return False
            
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
            
            # 打印当前字体配置，用于调试
            current_font = plt.rcParams['font.sans-serif'][0]
            print(f"📊 绘制折线图 - {title} 使用字体: {current_font}")
            
            fig, ax = plt.subplots(figsize=(20, 12), facecolor='black')
            
            # 设置标题和标签字体
            title_font = current_font
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
                print(f"✅ 图表: {save_path} (路径: {filepath})")
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
            print(f"✅ 图表: sector_rotation.png (路径: {filepath})")
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
            # 使用缓存获取数据
            oil_prices = self.get_cached_data("CL")
            
            gold_prices = self.get_cached_data("GC")
            
            if not (validate_data(oil_prices, 50) and validate_data(gold_prices, 50)):
                self.logger('油金比', 'warning', '数据不足')
                print("⚠️  油金比数据验证失败：原油或黄金数据不足")
                return False
            
            oil_prices, gold_prices = oil_prices.align(gold_prices, join='inner')
            
            if not validate_data(oil_prices, 30):
                print("⚠️  油金比数据验证失败：对齐后数据不足")
                return False
            
            oil_gold_ratio = oil_prices / gold_prices
            us_bond = self.get_cached_data('US_BOND')
            
            # 降低美债数据验证阈值，因为ak.bond_zh_us_rate返回的数据量较少
            if not validate_data(us_bond, 10):
                print("⚠️  油金比数据验证失败：美债数据不足")
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
            print(f"✅ 图表: jyb_gz.png (路径: {filepath})")
            plt.close(fig)
            
            return True
            
        except Exception as e:
            print(f"❌ 油金比图表失败: {e}")
            import traceback
            traceback.print_exc()
            self.logger('油金比', 'error', str(e))
            plt.close('all')
            return False
    
    def plot_pe_bond_spread(self):
        """绘制股债利差图"""
        try:
            # 使用缓存获取数据
            bond_yield = self.get_cached_data('中国国债收益率10年')
            pe_50 = self.get_cached_data('上证50滚动市盈率')
            
            if bond_yield.empty or pe_50.empty:
                self.logger('股债利差', 'warning', '数据获取失败')
                return False
            
            # 对齐日期并计算利差
            combined = pd.DataFrame({'中国国债收益率10年': bond_yield, '滚动市盈率': pe_50}).dropna()
            spread = combined['中国国债收益率10年'] - 100 / combined['滚动市盈率']
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
