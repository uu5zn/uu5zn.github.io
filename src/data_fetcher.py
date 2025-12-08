# -*- coding: utf-8 -*-
import yfinance as yf
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import os
import json
from config import HEADERS, YF_TIMEOUT, OUTPUT_DIR, SECTOR_ETFS, INDICES

import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='yfinance')


class DataFetcher:
    def __init__(self, logger_callback):
        """
        数据获取器
        :param logger_callback: 日志回调函数
        """
        self.logger = logger_callback
        self.cache_dir = os.path.join(OUTPUT_DIR, 'data_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_validity = 24 * 3600  # 缓存有效期（秒）
        self.all_data = None  # 存储所有数据的字典
        self.cache_meta_file = os.path.join(self.cache_dir, 'cache_meta.json')
    
    def _is_cache_valid(self):
        """检查缓存是否有效"""
        if os.path.exists(self.cache_meta_file):
            try:
                with open(self.cache_meta_file, 'r') as f:
                    meta = json.load(f)
                cache_time = meta.get('cache_time', 0)
                current_time = datetime.now().timestamp()
                return current_time - cache_time < self.cache_validity
            except:
                pass
        return False
    
    def _load_cache(self):
        """加载缓存数据"""
        if self._is_cache_valid():
            try:
                data_file = os.path.join(self.cache_dir, 'all_data.pkl')
                if os.path.exists(data_file):
                    self.all_data = pd.read_pickle(data_file)
                    self.logger('数据缓存', 'success', '已加载缓存数据')
                    return True
            except Exception as e:
                self.logger('数据缓存', 'error', f'加载缓存失败: {e}')
        return False
    
    def _save_cache(self):
        """保存数据到缓存"""
        try:
            if self.all_data is not None:
                # 保存数据
                data_file = os.path.join(self.cache_dir, 'all_data.pkl')
                pd.to_pickle(self.all_data, data_file)
                
                # 保存元数据
                meta = {
                    'cache_time': datetime.now().timestamp(),
                    'data_types': list(self.all_data.keys()),
                    'last_update': datetime.now().isoformat()
                }
                with open(self.cache_meta_file, 'w') as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
                
                self.logger('数据缓存', 'success', '已保存数据到缓存')
        except Exception as e:
            self.logger('数据缓存', 'error', f'保存缓存失败: {e}')
    def get_yf_data(self, ticker, period="3mo", interval='1d'):
        """
        获取yfinance数据
        :param ticker: 股票代码
        :param period: 周期
        :param interval: 间隔
        :return: DataFrame with columns: [Open, High, Low, Close, Volume]
        """
        try:
            data = yf.download(
                ticker, period=period, interval=interval, auto_adjust=True, 
                progress=False, timeout=YF_TIMEOUT
            )
            
            if data.empty:
                self.logger('YFinance', 'warning', f'{ticker} 返回空数据')
                return pd.DataFrame()
            
            # 处理多列情况 - 扁平化列索引
            if isinstance(data.columns, pd.MultiIndex):
                # 单个 ticker 时，yfinance 返回的 MultiIndex 有 ticker 层
                data.columns = data.columns.droplevel(1)
            
            # 确保返回的 DataFrame 有正确的列名
            expected_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in expected_cols):
                # 如果只有 Close 列（某些指数数据）
                if len(data.columns) == 1:
                    data.columns = ['Close']
            
            return data
            
        except Exception as e:
            self.logger('YFinance', 'error', f'{ticker}: {str(e)}')
            return pd.DataFrame()


    def fetch_all_data(self, force_refresh=False):
        """一次性获取所有需要的数据"""
        if not force_refresh and self._load_cache():
            return
        
        self.logger('数据获取', 'info', '开始获取所有数据...')
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*3)  # 获取3年数据
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        
        self.all_data = {}
        
        # 1. 融资余额
        self.logger('数据获取', 'info', '获取融资余额数据...')
        try:
            data = ak.stock_margin_sse(start_date=start_date_str, end_date=end_date_str)
            if not data.empty and len(data.columns) >= 2:
                data = data.iloc[:, [0, 1]].iloc[::-1]
                data['信用交易日期'] = pd.to_datetime(data['信用交易日期'], errors='coerce', format='%Y%m%d')
                # 统一长度为300
                self.all_data['融资余额'] = data.dropna().set_index('信用交易日期')['融资余额'].iloc[-300:]
            else:
                self.all_data['融资余额'] = pd.Series(dtype=float)
        except Exception as e:
            self.logger('数据获取', 'warning', f'融资余额: {str(e)[:100]}')
            self.all_data['融资余额'] = pd.Series(dtype=float)
        
        
        
        # 3. Shibor 1M
        self.logger('数据获取', 'info', '获取Shibor数据...')
        try:
            data = ak.macro_china_shibor_all()
            if not data.empty and '日期' in data.columns and '1M-定价' in data.columns:
                data['日期'] = pd.to_datetime(data['日期'], errors='coerce', format='%Y%m%d')
                # 统一长度为300
                self.all_data['Shibor 1M'] = data.dropna().set_index('日期')['1M-定价'].iloc[-300:]
            else:
                self.all_data['Shibor 1M'] = pd.Series(dtype=float)
        except Exception as e:
            self.logger('数据获取', 'warning', f'Shibor: {str(e)[:100]}')
            self.all_data['Shibor 1M'] = pd.Series(dtype=float)
        
        # 4. 中美国债收益率及相关数据
        self.logger('数据获取', 'info', '获取中美国债收益率数据...')
        try:
            data = ak.bond_zh_us_rate()[['日期','中国国债收益率10年', '美国国债收益率10年']].iloc[-600:]
            data['spread'] = data['中国国债收益率10年'] - data['美国国债收益率10年']
            data['日期'] = pd.to_datetime(data['日期'], errors='coerce', format='%Y%m%d')
            data = data.set_index('日期')
            data = data.ffill(axis=0)
            # 统一长度为300
            self.all_data['中美国债收益率'] = data['spread'].iloc[-300:]
            # 保存美国国债收益率
            self.all_data['US_BOND'] = data['美国国债收益率10年'].iloc[-300:]
            # 保存中国国债收益率10年
            self.all_data['中国国债收益率10年'] = data['中国国债收益率10年'].iloc[-300:]
        except Exception as e:
            self.logger('数据获取', 'warning', f'中美国债收益率: {str(e)[:100]}')
            self.all_data['中美国债收益率'] = pd.Series(dtype=float)
            self.all_data['US_BOND'] = pd.Series(dtype=float)
            self.all_data['中国国债收益率10年'] = pd.Series(dtype=float)
        
        # 5. ETF数据
        etf_list = {'ETF_510300': '510300', 'ETF_159845': '159845', 'ETF_510500': '510500'}
        for etf_key, etf_code in etf_list.items():
            self.logger('数据获取', 'info', f'获取{etf_key}数据...')
            try:
                data = ak.fund_etf_hist_em(symbol=etf_code)
                if not data.empty and '日期' in data.columns and '收盘' in data.columns:
                    data['日期'] = pd.to_datetime(data['日期'], errors='coerce')
                    # 统一长度为300
                    self.all_data[etf_key] = data.dropna().set_index('日期')['收盘'].iloc[-300:]
                else:
                    self.all_data[etf_key] = pd.Series(dtype=float)
            except Exception as e:
                self.logger('数据获取', 'warning', f'{etf_key}: {str(e)[:100]}')
                self.all_data[etf_key] = pd.Series(dtype=float)
        
        # 6. 原油价格
        self.logger('数据获取', 'info', '获取原油价格数据...')
        try:
            data = ak.futures_foreign_hist(symbol='CL')
            if not data.empty and 'date' in data.columns and 'close' in data.columns:
                data_copy = data.copy()
                data_copy['date'] = pd.to_datetime(data_copy['date'], errors='coerce')
                # 统一长度为300
                self.all_data['CL'] = data_copy.dropna().sort_values('date').set_index('date')['close'].iloc[-300:]
            else:
                self.all_data['CL'] = pd.Series(dtype=float)
        except Exception as e:
            self.logger('数据获取', 'warning', f'原油价格: {str(e)[:100]}')
            self.all_data['CL'] = pd.Series(dtype=float)
        
        # 7. 黄金价格
        self.logger('数据获取', 'info', '获取黄金价格数据...')
        try:
            data = ak.futures_foreign_hist(symbol='GC')
            if not data.empty and 'date' in data.columns and 'close' in data.columns:
                data_copy = data.copy()
                data_copy['date'] = pd.to_datetime(data_copy['date'], errors='coerce')
                # 统一长度为300
                self.all_data['GC'] = data_copy.dropna().sort_values('date').set_index('date')['close'].iloc[-300:]
            else:
                self.all_data['GC'] = pd.Series(dtype=float)
        except Exception as e:
            self.logger('数据获取', 'warning', f'黄金价格: {str(e)[:100]}')
            self.all_data['GC'] = pd.Series(dtype=float)
        
        # 8. 股债利差相关数据
        self.logger('数据获取', 'info', '获取股债利差相关数据...')
        # 上证50滚动市盈率
        try:
            pe_df = ak.stock_index_pe_lg(symbol="上证50")[['日期','滚动市盈率']]
            pe_df['日期'] = pd.to_datetime(pe_df['日期'], errors='coerce')
            pe_df.set_index('日期', inplace=True)
            # 统一长度为300
            self.all_data['上证50滚动市盈率'] = pe_df['滚动市盈率'].iloc[-300:]
        except Exception as e:
            self.logger('数据获取', 'warning', f'上证50滚动市盈率: {str(e)[:100]}')
            self.all_data['上证50滚动市盈率'] = pd.Series(dtype=float)
        
        # 10. Yf数据 - 补充更多全球指数和ETF
        indices = list(INDICES.values())
        sector_tickers = list(SECTOR_ETFS.values())

        self.logger('数据获取', 'info', '获取指数数据...')
        for idx in indices+sector_tickers:
            if idx not in self.all_data:
                try:
                    # 直接使用yfinance下载数据，不通过get_yf_data方法
                    idx_data = self.get_yf_data(idx, period="300d")
                except Exception as e:
                    self.logger('数据获取', 'warning', f'{idx}: {str(e)[:100]}')
                    self.all_data[idx] = pd.Series(dtype=float)
        
        self.logger('数据获取', 'success', f'已获取所有数据，共{len(self.all_data)}种数据类型')
        
        # 保存到缓存
        self._save_cache()
    
    def get_cached_data(self, symbol):
        """从缓存获取数据，如果缓存不存在则获取"""
        if self.all_data is None:
            self.fetch_all_data()
        
        if symbol in self.all_data:
            return self.all_data[symbol]
        else:
            # 如果数据不在缓存中，尝试从yfinance获取
            self.logger('数据获取', 'info', f'缓存中未找到{symbol}，尝试从yfinance获取...')
            idx_data = self.get_yf_data(symbol, period="300d")
            if not idx_data.empty and 'Close' in idx_data.columns:
                self.all_data[symbol] = idx_data['Close']
            else:
                self.all_data[symbol] = pd.Series(dtype=float)
            return self.all_data[symbol]
    
    
    
    
