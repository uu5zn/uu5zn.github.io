# -*- coding: utf-8 -*-
import pandas as pd  # 🔧 添加


import numpy as np
import os
import json
from datetime import datetime
from config import OUTPUT_DIR, MPL_STYLE
from utils import validate_data
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
        return all_data.get(symbol, pd.DataFrame(dtype=float))
    
    def plot_kline(self, ticker, filename, period="1mo"):
        """生成K线图 - 使用mplfinance库绘制真正的K线图"""
        try:
                     
            # 从缓存获取数据
            ohlc_data = self.get_cached_data(ticker).iloc[-20:]
            
            # 检查数据是否为空
            if ohlc_data.empty:
                print(f"   ⚠️  缓存中无 {ticker} 数据")
                self.logger('K线图', 'warning', f'{ticker}: 缓存中无数据')
                return False
            
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            # 使用mplfinance绘制K线图
            
            try:
                # 设置K线图样式
                mc = mpf.make_marketcolors(
                    up='#2ecc71', down='#e74c3c',
                    edge='inherit',
                    wick='inherit',
                    volume='in',
                    ohlc='inherit'
                )
                s = mpf.make_mpf_style(
                    base_mpf_style='charles',
                    marketcolors=mc,
                    facecolor='black',
                    edgecolor='#666666',
                    figcolor='black',
                    gridcolor='#666666',
                    gridstyle='--',
                    gridaxis='both',
                    rc={'font.size': 8, 'font.sans-serif': ['SimHei']}
                )
                
                # 绘制K线图
                mpf.plot(
                    ohlc_data,
                    type='candle',
                    style=s,
                    figsize=(6, 4),
                    title=ticker,
                    ylabel='价格',
                    volume=False,
                    savefig=dict(fname=filepath, dpi=150, bbox_inches='tight'),
                    tight_layout=True
                )
            except Exception as e:
                print(f"   ❌ mplfinance绘制失败: {e}")
                # 如果mplfinance绘制失败，回退到折线图
                print(f"   回退到折线图绘制")
                
                # 确保有Close列或第一列
                if isinstance(ohlc_data, pd.DataFrame):
                    if 'Close' in ohlc_data.columns:
                        close_data = ohlc_data['Close']
                    else:
                        close_data = ohlc_data.iloc[:, 0]
                else:
                    close_data = ohlc_data
                
                fig, ax = plt.subplots(figsize=(6, 4), facecolor='black')
                ax.set_facecolor('black')
                ax.plot(close_data.index, close_data, color='#2ecc71', linewidth=2.5)
                
                # 设置标题和标签
                current_font = plt.rcParams['font.sans-serif'][0]
                ax.set_title(ticker, fontsize=12, fontweight='bold', color='white', fontname=current_font)
                ax.set_xlabel('日期', fontsize=10, color='white', fontname=current_font)
                ax.set_ylabel('价格', fontsize=10, color='white', fontname=current_font)
                
                # 设置坐标轴颜色
                ax.spines['bottom'].set_color('#666666')
                ax.spines['top'].set_color('#666666')
                ax.spines['left'].set_color('#666666')
                ax.spines['right'].set_color('#666666')
                
                # 设置刻度颜色
                ax.tick_params(axis='x', colors='white', labelsize=8)
                ax.tick_params(axis='y', colors='white', labelsize=8)
                
                # 设置网格
                ax.grid(True, alpha=0.3, color='#666666', linestyle='--')
                
                # 设置日期格式
                fig.autofmt_xdate()
                
                # 调整布局并保存
                plt.tight_layout()
                plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='black')
                plt.close(fig)
          
            
        except Exception as e:
            import traceback
            print(f"❌ K线图失败 {ticker}: {e}")
            print(f"   错误堆栈: {traceback.format_exc()}")
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
                linewidth = linewidths[i] if linewidths else 2.5
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
            
            line1 = ax1.plot(oil_gold_ratio, 'r-', label='Oil/Gold Ratio', linewidth=2.5)
            ax1.set_ylabel('Oil/Gold Ratio', color='r', fontsize=10, fontname=title_font)
            
            line2 = ax2.plot(us_bond, 'b-', label='US 10Y Yield', linewidth=2.5)
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
            # 直接使用已计算好的股债利差数据
            spread_df = self.get_cached_data('股债利差')
            
            if spread_df.empty:
                self.logger('股债利差', 'warning', '数据获取失败')
                return False
            
            # 从DataFrame中提取value列作为Series
            spread = spread_df['value'] if 'value' in spread_df.columns else spread_df.iloc[:, 0]
            spread = spread.dropna()
            
            if not validate_data(spread, 50):
                return False
            
            # 设置字体
            title_font = plt.rcParams['font.sans-serif'][0]
            
            # 绘图
            fig, ax = plt.subplots(figsize=(20, 12), facecolor='black')
            spread.plot(ax=ax, color='white', linewidth=2.5)
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
