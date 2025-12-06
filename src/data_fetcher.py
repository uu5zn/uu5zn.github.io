# -*- coding: utf-8 -*-
import yfinance as yf
import akshare as ak
import pandas as pd  # 确认这行存在
import numpy as np  # 也添加 numpy
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from io import StringIO
from tqdm import tqdm
from config import HEADERS, YF_TIMEOUT
from utils import validate_data, log_execution
import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='yfinance')


class DataFetcher:
    def __init__(self, logger_callback):
        """
        数据获取器
        :param logger_callback: 日志回调函数
        """
        self.logger = logger_callback
    
    def safe_get_data(self, func, *args, **kwargs):
        """安全获取数据"""
        try:
            data = func(*args, **kwargs)
            if data is None or (hasattr(data, 'empty') and data.empty):
                return pd.DataFrame()
            return data
        except Exception as e:
            self.logger('数据获取', 'warning', f'{func.__name__}: {str(e)[:100]}')
            return pd.DataFrame()
    
    def get_yf_data(self, ticker, period="3mo", interval='1d'):
        """
        获取yfinance数据
        :param ticker: 股票代码
        :param period: 周期
        :param interval: 间隔
        """
        try:
            data = yf.download(
                ticker, period=period, interval=interval, 
                progress=False, timeout=YF_TIMEOUT
            )
            print(data.head())
            if data.empty:
                self.logger('YFinance', 'warning', f'{ticker} 返回空数据')
                return pd.DataFrame()
            
            # 处理多列情况
            if isinstance(data.columns, pd.MultiIndex):
                return data['Close']
            else:
                return data
        except Exception as e:
            self.logger('YFinance', 'error', f'{ticker}: {str(e)}')
            return pd.DataFrame()
    
    # src/data_fetcher.py

    def batch_download(self, tickers, period="1mo"):
        """
        批量下载数据，返回收盘价DataFrame，列名为tickers
        :param tickers: 代码列表或单个代码
        :param period: 周期
        :return: DataFrame，列名为tickers，索引为日期
        """
        try:
            if not tickers:
                return pd.DataFrame()
            
            # 确保 tickers 是列表
            if isinstance(tickers, str):
                tickers = [tickers]
            
            data = yf.download(
                tickers, period=period, interval='1d', 
                progress=False, timeout=YF_TIMEOUT
            )
            
            if data.empty:
                self.logger('批量下载', 'warning', '返回空数据')
                return pd.DataFrame()
            
            # 提取收盘价，简化列结构
            if isinstance(data.columns, pd.MultiIndex):
                # 多级索引：只保留 Close 价格
                close_data = data['Close']
                # 如果是 MultiIndex，移除 'Ticker' 级别名称
                if isinstance(close_data.columns, pd.MultiIndex):
                    close_data.columns = close_data.columns.droplevel(0)
                return close_data
            else:
                # 单个 ticker：直接返回 Close 列
                ticker_name = tickers[0] if isinstance(tickers, list) else tickers
                return pd.DataFrame({ticker_name: data['Close']})
        
        except Exception as e:
            self.logger('批量下载', 'error', f'{str(e)[:100]}')
            return pd.DataFrame()
    
    def fix_currency_boc_sina(self, symbol="美元", start_date="20230304", end_date="20231110"):
        """
        修复版新浪财经-中行人民币牌价数据
        :param symbol: 货币名称
        :param start_date: 开始日期 YYYYMMDD
        :param end_date: 结束日期 YYYYMMDD
        """
        url = "http://biz.finance.sina.com.cn/forex/forex.php"
        
        try:
            # 第一步：获取货币代码映射
            params = {
                "startdate": f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}",
                "enddate": f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}",
                "money_code": "EUR", "type": "0",
            }
            
            response = requests.get(url, params=params, headers=HEADERS, timeout=15)
            response.encoding = "gbk"
            soup = BeautifulSoup(response.text, "lxml")
            
            money_code_element = soup.find(attrs={"id": "money_code"})
            if money_code_element is None:
                self.logger('汇率数据', 'warning', '无法获取货币代码映射')
                return pd.DataFrame()
            
            data_dict = dict(
                zip(
                    [item.text for item in money_code_element.find_all("option")],
                    [item["value"] for item in money_code_element.find_all("option")]
                )
            )
            
            if symbol not in data_dict:
                self.logger('汇率数据', 'warning', f'不支持的货币: {symbol}')
                return pd.DataFrame()
            
            money_code = data_dict[symbol]
            
            # 第二步：获取实际数据
            params = {
                "money_code": money_code, "type": "0",
                "startdate": f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}",
                "enddate": f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}",
                "page": "1", "call_type": "ajax",
            }
            
            big_df = pd.DataFrame()
            first_response = requests.get(url, params=params, headers=HEADERS, timeout=15)
            first_soup = BeautifulSoup(first_response.text, "lxml")
            
            page_element_list = first_soup.find_all("a", attrs={"class": "page"})
            page_num = int(page_element_list[-2].text) if len(page_element_list) != 0 else 1
            
            for page in tqdm(range(1, page_num + 1), leave=False, desc=f"获取{symbol}数据"):
                params.update({"page": page})
                r = requests.get(url, params=params, headers=HEADERS, timeout=15)
                try:
                    temp_df = pd.read_html(StringIO(r.text), header=0)[0]
                    big_df = pd.concat([big_df, temp_df], ignore_index=True)
                except:
                    continue
            
            # 列名处理
            if len(big_df.columns) == 6:
                big_df.columns = ["日期", "中行汇买价", "中行钞买价", "中行钞卖价", "中行汇卖价", "央行中间价"]
            elif len(big_df.columns) == 5:
                big_df.columns = ["日期", "中行汇买价", "中行钞买价", "中行钞卖价/汇卖价", "央行中间价"]
            else:
                self.logger('汇率数据', 'warning', f'未知列数: {len(big_df.columns)}')
                return pd.DataFrame()
            
            # 数据清洗
            big_df["日期"] = pd.to_datetime(big_df["日期"], errors="coerce").dt.date
            for col in big_df.columns[1:]:
                big_df[col] = pd.to_numeric(big_df[col], errors="coerce")
            
            big_df.sort_values(by=["日期"], inplace=True, ignore_index=True)
            self.logger('汇率数据', 'success', f'获取 {len(big_df)} 条记录')
            return big_df
            
        except Exception as e:
            self.logger('汇率数据', 'error', f'{symbol}: {str(e)}')
            return pd.DataFrame()
    
    def get_data(self, symbol, start_date, end_date):
        """
        统一数据获取接口
        :param symbol: 数据类型标识
        :param start_date: 开始日期
        :param end_date: 结束日期
        """
        try:
            # 汇率数据
            if symbol == '美元':
                data = self.fix_currency_boc_sina(symbol=symbol, start_date=start_date, end_date=end_date)
                if not data.empty and '央行中间价' in data.columns:
                    return data.set_index("日期")['央行中间价']
            
            # 融资余额
            elif symbol == '融资余额':
                data = self.safe_get_data(ak.stock_margin_sse, start_date=start_date, end_date=end_date)
                if not data.empty and len(data.columns) >= 2:
                    data = data.iloc[:, [0, 1]].iloc[::-1]
                    data['信用交易日期'] = pd.to_datetime(data['信用交易日期'], errors='coerce', format='%Y%m%d')
                    return data.dropna().set_index('信用交易日期')['融资余额']
            
            # Shibor
            elif symbol == 'Shibor 1M':
                data = self.safe_get_data(ak.macro_china_shibor_all)
                if not data.empty and '日期' in data.columns and '1M-定价' in data.columns:
                    data['日期'] = pd.to_datetime(data['日期'], errors='coerce')
                    return data.dropna().set_index('日期')['1M-定价']
            
            # 中美国债
            elif symbol == '中美国债收益率':
                data = self.safe_get_data(ak.bond_zh_us_rate)
                if not data.empty and '日期' in data.columns:
                    data['日期'] = pd.to_datetime(data['日期'], errors='coerce')
                    data = data.dropna().set_index('日期')
                    data = data.ffill(axis=0)
                    if '中国国债收益率10年' in data.columns and '美国国债收益率10年' in data.columns:
                        data['spread'] = data['中国国债收益率10年'] - data['美国国债收益率10年']
                        return data
            
            # ETF数据
            elif symbol.startswith('ETF_'):
                etf_code = symbol.split('_')[1]
                data = self.safe_get_data(ak.fund_etf_hist_em, symbol=etf_code)
                if not data.empty and '日期' in data.columns and '收盘' in data.columns:
                    data = data.iloc[-220:] if len(data) > 220 else data
                    data['日期'] = pd.to_datetime(data['日期'], errors='coerce')
                    return data.dropna().set_index('日期')['收盘']
            
            # 期货数据
            elif symbol in ['CL', 'GC']:  # 原油、黄金
                data = self.safe_get_data(ak.futures_foreign_hist, symbol=symbol)
                if not data.empty and 'date' in data.columns and 'close' in data.columns:
                    return data.set_index('date')['close']
            
            # 美国国债
            elif symbol == 'US_BOND':
                data = self.safe_get_data(ak.bond_zh_us_rate)
                if not data.empty and '日期' in data.columns and '美国国债收益率10年' in data.columns:
                    bond_df = data.copy()
                    bond_df['日期'] = pd.to_datetime(bond_df['日期'], errors='coerce')
                    us_bond = bond_df.dropna().sort_values('日期').set_index('日期')
                    return us_bond['美国国债收益率10年'].ffill()
            
            else:
                self.logger('数据获取', 'warning', f'未识别的数据类型: {symbol}')
                
        except Exception as e:
            self.logger('数据处理', 'error', f'{symbol}: {str(e)}')
        
        # 默认返回空Series
        return pd.Series(dtype=float)
