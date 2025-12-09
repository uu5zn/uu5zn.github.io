# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import json
from config import MIN_DATA_POINTS, VIX_HIGH, VIX_EXTREME, VIX_LOW, SECTOR_ETFS, OUTPUT_DIR
from utils import validate_data, normalize, calculate_percentile

class MarketAnalyzer:
    def __init__(self, logger_callback):
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
        """从缓存获取数据"""
        all_data = self._load_cached_data()
        return all_data.get(symbol, pd.DataFrame(dtype=float))
    
    def calculate_trend(self, data, period=10):
        if not validate_data(data, period * 2):
            return 'unknown'
        # 处理DataFrame，取Close列或第一列
        if isinstance(data, pd.DataFrame):
            # 如果有Close列，使用Close列，否则使用第一列
            if 'Close' in data.columns:
                series = data['Close']
            else:
                series = data.iloc[:, 0]
        else:
            series = data
        recent = series.iloc[-period:].mean()
        previous = series.iloc[-period*2:-period].mean()
        return 'up' if recent > previous else 'down'
    
    def analyze_index_divergence(self):
        print("\n" + "="*70)
        print("【市场结构解读】")
        print("="*70)
        
        try:
            tickers = ['^IXIC', '^GSPC', '^RUT']
            
            # 从缓存获取数据
            nasdaq_close = self.get_cached_data('^IXIC')
            sp500_close = self.get_cached_data('^GSPC')
            russell_close = self.get_cached_data('^RUT')
            
            if not (validate_data(nasdaq_close, MIN_DATA_POINTS) and 
                    validate_data(sp500_close, MIN_DATA_POINTS) and 
                    validate_data(russell_close, MIN_DATA_POINTS)):
                print("⚠️  指数数据不足，无法分析")
                self.logger('指数差异分析', 'warning', '数据不足')
                return None
            
            # 从DataFrame中正确提取value列
            nasdaq_series = nasdaq_close['Close'] if 'Close' in nasdaq_close.columns else nasdaq_close.iloc[:, 0]
            sp500_series = sp500_close['Close'] if 'Close' in sp500_close.columns else sp500_close.iloc[:, 0]
            russell_series = russell_close['Close'] if 'Close' in russell_close.columns else russell_close.iloc[:, 0]
            
            # 计算指标（确保标量）
            nasdaq_ret = float((nasdaq_series.iloc[-1] / nasdaq_series.iloc[-30] - 1) * 100)
            sp500_ret = float((sp500_series.iloc[-1] / sp500_series.iloc[-30] - 1) * 100)
            russell_ret = float((russell_series.iloc[-1] / russell_series.iloc[-30] - 1) * 100)
            
            nasdaq_vol = float(nasdaq_series.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100)
            sp500_vol = float(sp500_series.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100)
            russell_vol = float(russell_series.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100)
            
            # 相关性
            # 先提取Series
            nasdaq_pct = nasdaq_series.pct_change().dropna()
            sp500_pct = sp500_series.pct_change().dropna()
            russell_pct = russell_series.pct_change().dropna()
            
            # 确保数据对齐
            df = pd.concat([nasdaq_pct, sp500_pct, russell_pct], axis=1, keys=['纳指', '标普', '罗素']).dropna()
            
            corr_nasdaq_sp500 = float(df['纳指'].corr(df['标普']))
            corr_nasdaq_russell = float(df['纳指'].corr(df['罗素']))
            corr_sp500_russell = float(df['标普'].corr(df['罗素']))
            
            print(f"\n📊 近30日涨跌幅:")
            print(f"  纳斯达克100: {nasdaq_ret:+.2f}% (波动率: {nasdaq_vol:.1f}%)")
            print(f"  标普500:     {sp500_ret:+.2f}% (波动率: {sp500_vol:.1f}%)")
            print(f"  罗素2000:    {russell_ret:+.2f}% (波动率: {russell_vol:.1f}%)")
            
            print(f"\n🔗 日收益率相关性:")
            print(f"  纳指-标普:   {corr_nasdaq_sp500:.3f}")
            print(f"  纳指-罗素:   {corr_nasdaq_russell:.3f}")
            print(f"  标普-罗素:   {corr_sp500_russell:.3f}")
            
            # 趋势分析
            nasdaq_trend = self.calculate_trend(nasdaq_close)
            sp500_trend = self.calculate_trend(sp500_close)
            russell_trend = self.calculate_trend(russell_close)
            
            print(f"\n📈 近期趋势:")
            print(f"  纳指: {'上涨' if nasdaq_trend == 'up' else '下跌'}趋势")
            print(f"  标普: {'上涨' if sp500_trend == 'up' else '下跌'}趋势")
            print(f"  罗素: {'上涨' if russell_trend == 'up' else '下跌'}趋势")
            
            # 市场风格解读
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
            
            # 记录洞察
            insight_msg = f"纳指{nasdaq_ret:+.2f}% 标普{sp500_ret:+.2f}% 罗素{russell_ret:+.2f}% {market_regime}"
            return {
                'regime': market_regime,
                'returns': {'nasdaq': nasdaq_ret, 'sp500': sp500_ret, 'russell': russell_ret},
                'insight': f"纳指{nasdaq_ret:+.2f}% 标普{sp500_ret:+.2f}% 罗素{russell_ret:+.2f}% {market_regime}"
            }
            
        except Exception as e:
            print(f"❌ 指数差异分析失败: {e}")
            self.logger('指数差异分析', 'error', str(e))
            return None
    
    def analyze_risk_regime(self):
        print("\n" + "="*70)
        print("【风险环境解读】")
        print("="*70)
        
        try:
            # 从缓存获取数据
            vix = self.get_cached_data('^VIX')
            ten_year = self.get_cached_data('^TNX')
            sp500 = self.get_cached_data('^GSPC')
            
            # 使用validate_data函数检查数据有效性
            if not (validate_data(vix, MIN_DATA_POINTS) and validate_data(ten_year, MIN_DATA_POINTS) and validate_data(sp500, MIN_DATA_POINTS)):
                self.logger('风险环境分析', 'warning', '数据不足')
                return None
            
            # 从DataFrame中正确提取value列
            vix_series = vix['Close'] if 'Close' in vix.columns else vix.iloc[:, 0]
            ten_year_series = ten_year['Close'] if 'Close' in ten_year.columns else ten_year.iloc[:, 0]
            
            current_vix = float(vix_series.iloc[-1])
            current_bond = float(ten_year_series.iloc[-1])
            vix_change = float((vix_series.iloc[-1] / vix_series.iloc[-5] - 1) * 100)
            bond_change = float((ten_year_series.iloc[-1] / ten_year_series.iloc[-5] - 1) * 100)
            
            # 计算百分位
            vix_percentile = calculate_percentile(vix_series, current_vix)
            bond_percentile = calculate_percentile(ten_year_series, current_bond)
            
            print(f"\n📊 当前风险指标:")
            print(f"  VIX:        {current_vix:.2f} ({vix_percentile:.0f}分位) 5日变化: {vix_change:+.2f}%")
            print(f"  10Y国债:    {current_bond:.2f}% ({bond_percentile:.0f}分位) 5日变化: {bond_change:+.2f}%")
            
            # VIX解读
            if current_vix > VIX_EXTREME:
                vix_signal = "🚨 恐慌极值区，市场极度避险"
                vix_level = "extreme"
            elif current_vix > VIX_HIGH:
                vix_signal = "⚠️  恐慌升温区，风险偏好下降"
                vix_level = "high"
            elif current_vix < VIX_LOW:
                vix_signal = "😌 恐慌低迷区，市场过度乐观"
                vix_level = "low"
            else:
                vix_signal = "✅ 正常波动区"
                vix_level = "normal"
            
            print(f"\n🎯 VIX解读: {vix_signal}")
            
            # 国债解读
            if current_bond > 5.0:
                bond_signal = "📈 极高利率区，严重压制资产估值"
                bond_level = "extreme_high"
            elif current_bond > 4.0:
                bond_signal = "📊 高利率区，不利长久期资产"
                bond_level = "high"
            elif current_bond < 2.5:
                bond_signal = "📉 极低利率区，资产估值泡沫化"
                bond_level = "extreme_low"
            elif current_bond < 3.5:
                bond_signal = "📉 低利率区，利好成长股"
                bond_level = "low"
            else:
                bond_signal = "🔄 利率中性区"
                bond_level = "normal"
            
            print(f"🎯 国债解读: {bond_signal}")
            
            # 趋势判断
            vix_trend = self.calculate_trend(vix)
            bond_trend = self.calculate_trend(ten_year)
            
            print(f"\n📈 近期趋势:")
            print(f"  VIX: 五日{'上升' if vix_trend == 'up' else '下降'} ({vix_change:+.2f}%)")
            print(f"  国债: 五日{'上升' if bond_trend == 'up' else '下降'} ({bond_change:+.2f}%)")
            
            # 股债相关性
            if validate_data(sp500, MIN_DATA_POINTS):
                # 从DataFrame中正确提取value列
                sp500_series = sp500['Close'] if 'Close' in sp500.columns else sp500.iloc[:, 0]
                
                # 计算相关性
                recent_corr = float(sp500_series.pct_change().iloc[-30:].corr(ten_year_series.diff().iloc[-30:]))
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
            if current_vix > VIX_HIGH: risk_score += 2
            elif current_vix < VIX_LOW: risk_score -= 1
            
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
            
            return {
                'vix': current_vix,
                'bond_yield': current_bond,
                'risk_level': risk_level
            }
            
        except Exception as e:
            print(f"❌ 风险环境分析失败: {e}")
            self.logger('风险环境分析', 'error', str(e))
            return None
    
    def analyze_china_us_linkage(self):
        """分析中美市场联动"""
        print("\n" + "="*70)
        print("【中美市场联动解读】")
        print("="*70)
        
        try:
            # 从缓存获取数据
            hsi = self.get_cached_data('^HSI')
            usdcny = self.get_cached_data('CNY=X')
            sp500 = self.get_cached_data('^GSPC')
            
            # 使用validate_data函数检查数据有效性
            if not (validate_data(hsi, 30) and validate_data(usdcny, 30) and validate_data(sp500, 30)):
                self.logger('中美联动分析', 'warning', '数据不足')
                return None
            
            # 从DataFrame中正确提取value列
            hsi_series = hsi['Close'] if 'Close' in hsi.columns else hsi.iloc[:, 0]
            sp500_series = sp500['Close'] if 'Close' in sp500.columns else sp500.iloc[:, 0]
            usdcny_series = usdcny['Close'] if 'Close' in usdcny.columns else usdcny.iloc[:, 0]
            
            # 确保标量值
            hsi_ret = float((hsi_series.iloc[-1] / hsi_series.iloc[-30] - 1) * 100)
            sp500_ret = float((sp500_series.iloc[-1] / sp500_series.iloc[-30] - 1) * 100)
            current_cny = float(usdcny_series.iloc[-1])
            cny_change_5d = float((usdcny_series.iloc[-1] / usdcny_series.iloc[-5] - 1) * 100)
            cny_change_30d = float((usdcny_series.iloc[-1] / usdcny_series.iloc[-30] - 1) * 100)
            
            print(f"\n📊 市场表现 (30日):")
            print(f"  恒生指数:    {hsi_ret:+.2f}%")
            print(f"  标普500:     {sp500_ret:+.2f}%")
            print(f"  人民币汇率:  {current_cny:.4f} (5日: {cny_change_5d:+.2f}%, 30日: {cny_change_30d:+.2f}%)")
            
            # 汇率解读
            if cny_change_5d > 0.5:
                cny_signal = "📉 快速贬值 → 资本外流压力，港股承压"
                cny_regime = "depreciation"
            elif cny_change_5d < -0.5:
                cny_signal = "📈 快速升值 → 外资流入，港股受益"
                cny_regime = "appreciation"
            else:
                cny_signal = "🔄 相对稳定 → 汇率不是主要矛盾"
                cny_regime = "stable"
            
            print(f"\n🎯 汇率信号: {cny_signal}")
            
            # 计算相关性
            # 先提取Series并计算收益率
            hsi_pct = hsi_series.pct_change().dropna()
            usdcny_pct = usdcny_series.pct_change().dropna()
            sp500_pct = sp500_series.pct_change().dropna()
            
            # 确保数据对齐
            df = pd.concat([hsi_pct, usdcny_pct, sp500_pct], axis=1, keys=['恒指', '人民币', '标普']).dropna()
            
            corr_hsi_sp500 = float(df['恒指'].corr(df['标普']))
            corr_hsi_cny = float(df['恒指'].corr(-df['人民币']))
            corr_sp500_cny = float(df['标普'].corr(-df['人民币']))
            
            print(f"\n🔗 相关性分析:")
            print(f"  恒指-标普:   {corr_hsi_sp500:.3f} {'🔒强联动' if corr_hsi_sp500 > 0.7 else '🔓弱联动' if corr_hsi_sp500 < 0.3 else '🔄中等'}")
            print(f"  恒指-人民币: {corr_hsi_cny:.3f} ({'✅正常' if corr_hsi_cny > 0 else '⚠️异常'})")
            print(f"  标普-人民币: {corr_sp500_cny:.3f}")
            
            # 联动性强度
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
                strength_reason = "估值修复、政策利好、南向资金流入"
            elif relative_strength < -strength_threshold:
                strength_signal = "😞 港股显著跑输"
                strength_reason = "汇率贬值、监管担忧、外资流出"
            else:
                strength_signal = "🤝 基本同步"
                strength_reason = "港股与美股相关性主导"
            
            print(f"\n📈 相对强弱: {strength_signal} (差值: {relative_strength:+.2f}%)")
            print(f"💡 原因推断: {strength_reason}")
            
            # 背离信号
            if corr_hsi_cny < 0 and corr_hsi_cny < -0.2:
                print("⚠️  汇率与港股负相关异常 → 基本面或情绪因素强于汇率")
            
            # 操作建议
            if relative_strength < -5 and cny_change_5d > 0.5:
                print("\n🚨 双重压力: 汇率贬值+相对弱势 → 谨慎观望")
            elif relative_strength > 5 and cny_change_5d < -0.5:
                print("\n✅ 双重利好: 汇率升值+相对强势 → 积极布局")
            
            return {
                'hsi_ret': hsi_ret,
                'sp500_ret': sp500_ret,
                'cny_change': cny_change_5d,
                'linkage': linkage,
                'linkage_desc': linkage_desc,
                'relative_strength': relative_strength,
                'strength_signal': strength_signal,
                'cny_regime': cny_regime
            }
            
        except Exception as e:
            print(f"❌ 中美联动分析失败: {e}")
            self.logger('中美联动分析', 'error', str(e))
            return None
    
    def analyze_liquidity_conditions(self, margin_data, shibor_data, bond_data):
        """分析流动性环境"""
        print("\n" + "="*70)
        print("【流动性环境解读】")
        print("="*70)
        
        try:
            if not validate_data(margin_data, 50):
                self.logger('流动性分析', 'warning', '融资余额数据不足')
                return None
            
            # 提取Series
            if isinstance(margin_data, pd.DataFrame):
                margin_series = margin_data['value'] if 'value' in margin_data.columns else margin_data.iloc[:, 0]
            else:
                margin_series = margin_data
            
            # 计算标量值
            current_margin = float(margin_series.iloc[-1] / 100000000)
            margin_change_5d = float(margin_series.pct_change(5).iloc[-1] * 100)
            margin_change_30d = float(margin_series.pct_change(30).iloc[-1] * 100)
            
            # 处理Shibor数据
            current_shibor = 0.0
            shibor_change = 0.0
            if validate_data(shibor_data, 10):
                # 确保shibor_data是Series
                if isinstance(shibor_data, pd.DataFrame):
                    shibor_series = shibor_data['value'] if 'value' in shibor_data.columns else shibor_data.iloc[:, 0]
                else:
                    shibor_series = shibor_data
                current_shibor = float(shibor_series.iloc[-1])
                shibor_change = float(shibor_series.pct_change().iloc[-1] * 100) if len(shibor_series) > 1 else 0
            
            print(f"\n📊 流动性指标:")
            print(f"  融资余额: {current_margin:.0f}亿")
            print(f"    ├─5日变化: {margin_change_5d:+.2f}%")
            print(f"    └─30日变化: {margin_change_30d:+.2f}%")
            print(f"  Shibor 1M: {current_shibor:.2f}%")
            print(f"    └─日变化: {shibor_change:+.2f}%")
            
            # 处理bond_data（统一处理，避免重复）
            current_spread = 0.0
            spread_change_5d = 0.0
            spread_signal = ""
            spread_desc = ""
            if validate_data(bond_data, 10):
                # 确保bond_data是Series
                if isinstance(bond_data, pd.DataFrame):
                    bond_series = bond_data['value'] if 'value' in bond_data.columns else bond_data.iloc[:, 0]
                else:
                    bond_series = bond_data
                
                # 计算中美利差（基点）
                current_spread = float(bond_series.iloc[-1])
                current_spread_bp = current_spread * 100  # 转换为基点
                spread_change_5d = float(bond_series.diff(5).iloc[-1] * 100) if len(bond_series) > 5 else 0  # 转换为基点
                
                print(f"  中美利差: {current_spread_bp:.2f}bp (5日变化: {spread_change_5d:+.0f}bp)")
                
                # 中美利差解读
                # 注意：current_spread 已经是基点单位
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
            
            # 流动性评分
            liquidity_score = 0
            if margin_change_5d > 1: liquidity_score += 1
            elif margin_change_5d < -1: liquidity_score -= 1
            
            if current_shibor < 2.5: liquidity_score += 1
            elif current_shibor > 3.0: liquidity_score -= 1
            
            if validate_data(bond_data, 10):
                # 确保bond_data是Series
                if isinstance(bond_data, pd.DataFrame):
                    bond_series = bond_data['value'] if 'value' in bond_data.columns else bond_data.iloc[:, 0]
                else:
                    bond_series = bond_data
                spread_value = float(bond_series.iloc[-1]) * 100  # 转换为基点
                if spread_value > 50: liquidity_score -= 1
            
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
            
            return {
                'margin': current_margin,
                'margin_change': margin_change_5d,
                'shibor': current_shibor,
                'liquidity_env': liquidity_env,
                'liquidity_score': liquidity_score
            }
            
        except Exception as e:
            print(f"❌ 流动性分析失败: {e}")
            self.logger('流动性分析', 'error', str(e))
            return None
    
    def analyze_pe_bond_spread(self):
        """分析股债性价比"""
        print("\n" + "="*70)
        print("【股债性价比解读】")
        print("="*70)
        
        try:
            # 从缓存获取数据
            bond_yield = self.get_cached_data('中国国债收益率10年')  # 正确获取国债收益率
            pe_50 = self.get_cached_data('上证50滚动市盈率')
            spread = self.get_cached_data('股债利差')  # 股债利差是计算结果
            
            if not (validate_data(bond_yield) and validate_data(pe_50) and validate_data(spread)):
                self.logger('股债性价比', 'warning', '数据获取失败或不足')
                return None
            
            # 从DataFrame中正确提取value列
            bond_yield_series = bond_yield['value'] if 'value' in bond_yield.columns else bond_yield.iloc[:, 0]
            pe_50_series = pe_50['value'] if 'value' in pe_50.columns else pe_50.iloc[:, 0]
            spread_series = spread['value'] if 'value' in spread.columns else spread.iloc[:, 0]
            
            # 最新数据
            current_bond = float(bond_yield_series.iloc[-1])
            current_pe = float(pe_50_series.iloc[-1])
            current_spread = float(spread_series.iloc[-1])
            
            # 历史百分位
            spread_percentile = calculate_percentile(spread_series, current_spread)
            
            # 解读
            if current_spread > -2.6:
                interpretation = "🔴 股债利差处于历史高位，债券吸引力显著增强，股票相对昂贵"
                signal = "债券占优"
            elif current_spread > -5.5:
                interpretation = "🟡 股债利差处于中等水平，股债配置相对均衡"
                signal = "均衡配置"
            elif current_spread > -7.8:
                interpretation = "🟢 股债利差处于历史低位，股票吸引力显著增强，债券相对昂贵"
                signal = "股票占优"
            else:
                interpretation = "🔵 股债利差极度偏低，股票性价比极高，强烈建议配置股票"
                signal = "股票极度占优"
            
            print(f"\n📊 股债性价比指标:")
            print(f"  中国10年期国债收益率: {current_bond:.2f}%")
            print(f"  上证50滚动市盈率:     {current_pe:.2f}")
            print(f"  股债利差:             {current_spread:.2f}")
            print(f"  历史百分位:           {spread_percentile:.0f}%")
            
            print(f"\n🎯 解读: {interpretation}")
            print(f"💡 信号: {signal}")
            
            # 操作建议
            if signal == "债券占优":
                print(f"💼 建议: 增加债券配置比例，减少股票持仓")
            elif signal == "均衡配置":
                print(f"💼 建议: 保持股债均衡配置，关注市场变化")
            elif signal == "股票占优":
                print(f"💼 建议: 增加股票配置比例，减少债券持仓")
            else:
                print(f"💼 建议: 大幅增加股票配置，减少债券持仓")
            
            return {
                '股债利差': interpretation,
                '当前利差': current_spread,
                '国债收益率': current_bond,
                '滚动市盈率': current_pe,
                '百分位': spread_percentile,
                '信号': signal
            }
            
        except Exception as e:
            print(f"❌ 股债性价比分析失败: {e}")
            import traceback
            traceback.print_exc()
            self.logger('股债性价比', 'error', str(e))
            return None
    
    
    
    def analyze_margin_analysis(self):
        """融资余额分析 - 从缓存数据获取"""
        try:
            # 从缓存获取数据
            margin_data = self.get_cached_data('融资余额')
            
            if not validate_data(margin_data, 50):
                return {
                    'success': False,
                    'message': '融资余额数据不足'
                }
            
            # 获取value列的数据
            margin_values = margin_data['value'] if 'value' in margin_data.columns else margin_data['Close']
            
            # 计算均线
            margin_ma10 = margin_values.rolling(10).mean()
            
            # 打印最新值
            # 确保获取的是标量值，从margin_values获取最新值
            last_margin = margin_values.iloc[-1] / 1000000
            last_ma10 = margin_ma10.iloc[-1]
            
            return {
                'success': True,
                'margin_data': margin_data,
                'margin_values': margin_values,
                'margin_ma10': margin_ma10,
                'last_margin': float(last_margin),  # 确保是标量
                'last_ma10': float(last_ma10),      # 确保是标量
                'below_ma10': last_margin < last_ma10  # 使用标量比较
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'融资余额分析失败: {e}'
            }
    
    def analyze_multi_indicator(self):
        """多指标对比 - 从缓存数据获取"""
        try:
            # 从缓存获取数据
            margin_data = self.get_cached_data('融资余额')
            exchange_rate = self.get_cached_data('美元')
            shibor_data = self.get_cached_data('Shibor 1M')
            bond_data = self.get_cached_data('中美国债收益率')
            etf_300 = self.get_cached_data('ETF_510300')
            etf_1000 = self.get_cached_data('ETF_159845')
            etf_500 = self.get_cached_data('ETF_510500')
            
            # 提取需要的数据列
            margin_values = margin_data['value'] if not margin_data.empty and 'value' in margin_data.columns else pd.Series()
            exchange_rate_values = exchange_rate['value'] if not exchange_rate.empty and 'value' in exchange_rate.columns else pd.Series()
            shibor_values = shibor_data['value'] if not shibor_data.empty and 'value' in shibor_data.columns else pd.Series()
            bond_values = bond_data['value'] if not bond_data.empty and 'value' in bond_data.columns else pd.Series()
            etf_300_values = etf_300['Close'] if not etf_300.empty and 'Close' in etf_300.columns else pd.Series()
            etf_1000_values = etf_1000['Close'] if not etf_1000.empty and 'Close' in etf_1000.columns else pd.Series()
            etf_500_values = etf_500['Close'] if not etf_500.empty and 'Close' in etf_500.columns else pd.Series()
            
            return {
                'success': True,
                'margin_data': margin_data,
                'exchange_rate': exchange_rate,
                'shibor_data': shibor_data,
                'bond_data': bond_data,
                'etf_300': etf_300,
                'etf_1000': etf_1000,
                'etf_500': etf_500,
                'margin_values': margin_values,
                'exchange_rate_values': exchange_rate_values,
                'shibor_values': shibor_values,
                'bond_values': bond_values,
                'etf_300_values': etf_300_values,
                'etf_1000_values': etf_1000_values,
                'etf_500_values': etf_500_values
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'多指标对比失败: {e}'
            }
    
    def analyze_correlation(self):
        """相关性分析 - 从缓存数据获取"""
        try:
            # 从缓存获取数据
            hsi = self.get_cached_data('^HSI')
            rut = self.get_cached_data('^RUT')
            
            if hsi.empty or rut.empty:
                return {
                    'success': False,
                    'message': '相关性分析数据不足'
                }
            
            # 提取Close列或第一列
            def extract_close(data):
                if isinstance(data, pd.DataFrame):
                    if 'Close' in data.columns:
                        return data['Close'].dropna()
                    elif not data.empty:
                        return data.iloc[:, 0].dropna()
                return data
            
            hsi_close = extract_close(hsi)
            rut_close = extract_close(rut)
            
            if len(hsi_close) < 30 or len(rut_close) < 30:
                return {
                    'success': False,
                    'message': '相关性分析数据不足'
                }
            
            # 对齐数据
            df = pd.concat([hsi_close, rut_close], axis=1, keys=['HSI', 'RUT']).dropna()
            
            if len(df) < 30:
                return {
                    'success': False,
                    'message': '相关性分析数据不足'
                }
            
            correlation = float(df['HSI'].corr(df['RUT']))
            
            return {
                'success': True,
                'hsi': hsi,
                'rut': rut,
                'hsi_close': hsi_close,
                'rut_close': rut_close,
                'df': df,
                'correlation': correlation
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'相关性分析失败: {e}'
            }
    
    def analyze_sector_rotation(self):
        """分析行业轮动"""
        print("\n" + "="*70)
        print("【行业轮动解读】")
        print("="*70)
        
        try:
            
            returns = {}
            for sector, ticker in SECTOR_ETFS.items():
                try:
                    if not ticker:
                        returns[sector] = np.nan
                        continue
                    
                    # 从data_fetcher获取缓存数据
                    data = self.get_cached_data(ticker)
                    
                    if validate_data(data, 10):
                        returns[sector] = float((data.iloc[-1].iloc[0] / data.iloc[0].iloc[0] - 1) * 100)
                    else:
                        returns[sector] = np.nan
                        
                except Exception as e:
                    print(f"⚠️  {sector}({ticker}) 失败: {e}")
                    returns[sector] = np.nan
            
            # 过滤有效数据
            valid_returns = {k: v for k, v in returns.items() if not np.isnan(v)}
            if not valid_returns:
                self.logger('行业轮动', 'warning', '无有效数据')
                return None
            
            # 排序
            sorted_returns = sorted(valid_returns.items(), key=lambda x: x[1], reverse=True)
            
            print(f"\n📊 近1月行业表现:")
            for i, (sector, ret) in enumerate(sorted_returns, 1):
                print(f"  {i}. {sector}: {ret:+.2f}%")
            
            # 领涨与落后
            leaders = [s for s, r in sorted_returns[:2]]
            laggards = [s for s, r in sorted_returns[-2:]]
            
            print(f"\n🏆 领涨: {', '.join(leaders)}")
            print(f"📉 落后: {', '.join(laggards)}")
            
            # 轮动强度
            rotation_signal = "中性"
            dispersion = 0
            if len(sorted_returns) >= 3:
                top3_avg = np.mean([r for _, r in sorted_returns[:3]])
                bottom3_avg = np.mean([r for _, r in sorted_returns[-3:]])
                dispersion = top3_avg - bottom3_avg
                
                print(f"\n🔄 轮动强度: {dispersion:.2f}%")
                if dispersion > 8:
                    rotation_signal = "🔥 剧烈轮动"
                    rotation_desc = "板块分化严重，追高风险大"
                elif dispersion < 3:
                    rotation_signal = "🟢 轮动平缓"
                    rotation_desc = "板块表现趋同，普涨行情"
                else:
                    rotation_signal = "🔄 正常轮动"
                    rotation_desc = "结构性机会为主"
                
                print(f"🎯 {rotation_signal}: {rotation_desc}")
            
            # 风格判断
            us_tech_leading = any('美股科技' in s for s in leaders)
            us_value_leading = any('美股金融' in s or '美股能源' in s for s in leaders)
            
            style_msg = []
            if us_tech_leading:
                style_msg.append("美股成长风格")
            if us_value_leading:
                style_msg.append("美股价值风格")
            
            style_str = " + ".join(style_msg) if style_msg else "风格不明朗"
            
            return {
                'leaders': leaders,
                'laggards': laggards,
                'returns': valid_returns,
                'rotation_strength': float(dispersion) if 'dispersion' in locals() else 0,
                'rotation_signal': rotation_signal,
                'style_str': style_str,
                'sorted_returns': sorted_returns,
                'rotation_desc': rotation_desc if 'rotation_desc' in locals() else "",
                'leading': ', '.join(leaders)
            }
            
        except Exception as e:
            print(f"❌ 行业轮动分析失败: {e}")
            self.logger('行业轮动分析', 'error', str(e))
            return None
    
    def analyze_market(self):
        """综合市场分析，整合所有分析模块"""
        print("\n" + "📈 开始生成综合市场解读".center(70, "="))
        
        # 初始化输出捕获存储
        insights = []
        detailed_output = {
            'sector_rotation': '',
            'index_divergence': '',
            'risk_regime': '',
            'china_us_linkage': '',
            'liquidity_conditions': ''
        }
        
        try:
            # 行业轮动
            # 先检查analyze_sector_rotation方法是否存在
            if hasattr(self, 'analyze_sector_rotation'):
                success, sector_result, output = capture_print(self.analyze_sector_rotation)
                if sector_result:
                    insights.append(('行业轮动', f"行业轮动强度{sector_result['rotation_strength']:.2f}% {sector_result['leading']}"))
                    detailed_output['sector_rotation'] = output
            
            # 指数差异
            success, index_result, output = capture_print(self.analyze_index_divergence)
            if index_result:
                insights.append(('指数差异', index_result['insight']))
                detailed_output['index_divergence'] = output
            
            # 风险环境
            success, risk_result, output = capture_print(self.analyze_risk_regime)
            if risk_result:
                insights.append(('风险环境', f"VIX{risk_result['vix']:.2f} 国债{risk_result['bond_yield']:.2f}% {risk_result['risk_level']}"))
                detailed_output['risk_regime'] = output
            
            # 中美联动
            success, linkage_result, output = capture_print(self.analyze_china_us_linkage)
            if linkage_result:
                insights.append(('中美联动', f"恒指{linkage_result['hsi_ret']:+.2f}% 汇率{linkage_result['cny_change']:+.2f}% {linkage_result['linkage']}"))
                detailed_output['china_us_linkage'] = output
            
            # 流动性 - 使用缓存数据
            margin_data = self.get_cached_data('融资余额')
            shibor_data = self.get_cached_data('Shibor 1M')
            bond_data = self.get_cached_data('中美国债收益率')
            
            # 提取需要的数据列
            margin_values = margin_data['value'] if not margin_data.empty and 'value' in margin_data.columns else pd.Series()
            shibor_values = shibor_data['value'] if not shibor_data.empty and 'value' in shibor_data.columns else pd.Series()
            bond_values = bond_data['value'] if not bond_data.empty and 'value' in bond_data.columns else pd.Series()
            
            success, liquidity_result, output = capture_print(self.analyze_liquidity_conditions, margin_values, shibor_values, bond_values)
            if liquidity_result:
                insights.append(('流动性', f"融资{liquidity_result['margin']:.0f}亿 Shibor{liquidity_result['shibor']:.2f}% {liquidity_result['liquidity_env']}"))
                detailed_output['liquidity_conditions'] = output
            
            # 股债性价比
            success, pe_bond_result, output = capture_print(self.analyze_pe_bond_spread)
            if pe_bond_result:
                insights.append(('股债利差', pe_bond_result['股债利差']))
                detailed_output['pe_bond_spread'] = output
            
            print("\n" + "📊 市场解读完成".center(70, "="))
            
            return {
                'insights': insights,
                'detailed_output': detailed_output
            }
            
        except Exception as e:
            print(f"❌ 市场解读失败: {e}")
            self.logger('市场解读', 'error', str(e))
            return {
                'insights': insights,
                'detailed_output': detailed_output
            }