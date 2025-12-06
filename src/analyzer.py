# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from config import MIN_DATA_POINTS, VIX_HIGH, VIX_EXTREME, VIX_LOW
from utils import validate_data, normalize, calculate_percentile

class MarketAnalyzer:
    def __init__(self, data_fetcher, logger_callback):
        """
        市场分析器
        :param data_fetcher: 数据获取器实例
        :param logger_callback: 日志回调函数
        """
        self.fetcher = data_fetcher
        self.logger = logger_callback
    
    def calculate_trend(self, series, period=10):
        """计算趋势方向"""
        if not validate_data(series, period * 2):
            return 'unknown'
        recent = series.iloc[-period:].mean()
        previous = series.iloc[-period*2:-period].mean()
        return 'up' if recent > previous else 'down'
    
    def analyze_index_divergence(self):
        """
        分析指数差异（纳指、标普、罗素2000）
        识别市场风格：成长/价值/周期
        """
        print("\n" + "="*70)
        print("【市场结构解读】")
        print("="*70)
        
        try:
            # 批量下载指数数据
            tickers = ['^IXIC', '^GSPC', '^RUT']
            raw_data = self.fetcher.batch_download(tickers, period="3mo")
            
            if raw_data.empty:
                self.logger('指数差异分析', 'warning', '数据下载失败')
                return None
            
            # 提取收盘价
            if isinstance(raw_data.columns, pd.MultiIndex):
                nasdaq = raw_data['Close']['^IXIC'].dropna()
                sp500 = raw_data['Close']['^GSPC'].dropna()
                russell = raw_data['Close']['^RUT'].dropna()
            else:
                # 降级处理
                nasdaq = self.fetcher.get_yf_data('^IXIC', period='3mo')['Close']
                sp500 = self.fetcher.get_yf_data('^GSPC', period='3mo')['Close']
                russell = self.fetcher.get_yf_data('^RUT', period='3mo')['Close']
            
            if not (validate_data(nasdaq, MIN_DATA_POINTS) and 
                    validate_data(sp500, MIN_DATA_POINTS) and 
                    validate_data(russell, MIN_DATA_POINTS)):
                print("⚠️  指数数据不足，无法分析")
                self.logger('指数差异分析', 'warning', '数据不足')
                return None
            
            # 计算收益率
            nasdaq_ret = (nasdaq.iloc[-1] / nasdaq.iloc[-30] - 1) * 100
            sp500_ret = (sp500.iloc[-1] / sp500.iloc[-30] - 1) * 100
            russell_ret = (russell.iloc[-1] / russell.iloc[-30] - 1) * 100
            
            # 计算年化波动率
            nasdaq_vol = nasdaq.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
            sp500_vol = sp500.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
            russell_vol = russell.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
            
            # 计算相关性矩阵
            df = pd.concat([
                nasdaq.pct_change().dropna(),
                sp500.pct_change().dropna(),
                russell.pct_change().dropna()
            ], axis=1, keys=['纳指', '标普', '罗素']).dropna()
            
            corr_nasdaq_sp500 = df['纳指'].corr(df['标普'])
            corr_nasdaq_russell = df['纳指'].corr(df['罗素'])
            corr_sp500_russell = df['标普'].corr(df['罗素'])
            
            print(f"\n📊 近30日涨跌幅:")
            print(f"  纳斯达克100: {nasdaq_ret:+.2f}% (波动率: {nasdaq_vol:.1f}%)")
            print(f"  标普500:     {sp500_ret:+.2f}% (波动率: {sp500_vol:.1f}%)")
            print(f"  罗素2000:    {russell_ret:+.2f}% (波动率: {russell_vol:.1f}%)")
            
            print(f"\n🔗 日收益率相关性:")
            print(f"  纳指-标普:   {corr_nasdaq_sp500:.3f}")
            print(f"  纳指-罗素:   {corr_nasdaq_russell:.3f}")
            print(f"  标普-罗素:   {corr_sp500_russell:.3f}")
            
            # 趋势分析
            nasdaq_trend = self.calculate_trend(nasdaq)
            sp500_trend = self.calculate_trend(sp500)
            russell_trend = self.calculate_trend(russell)
            
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
            
            # 波动性异常检测
            avg_vol = np.mean([nasdaq_vol, sp500_vol, russell_vol])
            if russell_vol > avg_vol * 1.2:
                print("⚠️  小盘股波动率异常放大 → 市场不确定性集中在小盘")
            
            # 相关性异常检测
            if corr_nasdaq_russell < 0.6:
                print("⚠️  纳指与罗素相关性显著下降 → 大小盘走势分化，市场结构不健康")
            
            # 记录洞察
            insight_msg = f"纳指{nasdaq_ret:+.2f}% 标普{sp500_ret:+.2f}% 罗素{russell_ret:+.2f}% {market_regime}"
            return {
                'regime': market_regime,
                'returns': {'nasdaq': nasdaq_ret, 'sp500': sp500_ret, 'russell': russell_ret},
                'volatilities': {'nasdaq': nasdaq_vol, 'sp500': sp500_vol, 'russell': russell_vol},
                'correlations': {
                    'nasdaq_sp500': corr_nasdaq_sp500,
                    'nasdaq_russell': corr_nasdaq_russell,
                    'sp500_russell': corr_sp500_russell
                },
                'trends': {'nasdaq': nasdaq_trend, 'sp500': sp500_trend, 'russell': russell_trend},
                'insight': insight_msg
            }
            
        except Exception as e:
            print(f"❌ 指数差异分析失败: {e}")
            self.logger('指数差异分析', 'error', str(e))
            return None
    
    def analyze_risk_regime(self):
        """分析风险环境（VIX+国债）"""
        print("\n" + "="*70)
        print("【风险环境解读】")
        print("="*70)
        
        try:
            # 获取数据
            vix = self.fetcher.get_yf_data('^VIX', period='3mo')
            ten_year = self.fetcher.get_yf_data('^TNX', period='3mo')
            sp500 = self.fetcher.get_yf_data('^GSPC', period='3mo')
            
            if not (validate_data(vix, MIN_DATA_POINTS) and 
                    validate_data(ten_year, MIN_DATA_POINTS)):
                self.logger('风险环境分析', 'warning', '数据不足')
                return None
            
            current_vix = vix.iloc[-1]
            current_bond = ten_year.iloc[-1]
            vix_change = (vix.iloc[-1] / vix.iloc[-5] - 1) * 100
            bond_change = (ten_year.iloc[-1] / ten_year.iloc[-5] - 1) * 100
            
            # 计算百分位
            vix_percentile = calculate_percentile(vix, current_vix)
            bond_percentile = calculate_percentile(ten_year, current_bond)
            
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
                recent_corr = sp500.pct_change().iloc[-30:].corr(ten_year.diff().iloc[-30:])
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
                'vix_change': vix_change,
                'bond_change': bond_change,
                'risk_level': risk_level,
                'vix_level': vix_level,
                'bond_level': bond_level,
                'risk_score': risk_score,
                'action': action,
                'vix_signal': vix_signal,
                'bond_signal': bond_signal
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
            hsi = self.fetcher.get_yf_data('^HSI', period='3mo')
            usdcny = self.fetcher.get_yf_data('CNY=X', period='3mo')
            sp500 = self.fetcher.get_yf_data('^GSPC', period='3mo')
            
            if not (validate_data(hsi, MIN_DATA_POINTS) and 
                    validate_data(usdcny, MIN_DATA_POINTS)):
                self.logger('中美联动分析', 'warning', '数据不足')
                return None
            
            current_cny = usdcny.iloc[-1]
            cny_change_5d = (usdcny.iloc[-1] / usdcny.iloc[-5] - 1) * 100
            cny_change_30d = (usdcny.iloc[-1] / usdcny.iloc[-30] - 1) * 100
            
            hsi_ret = (hsi.iloc[-1] / hsi.iloc[-30] - 1) * 100
            sp500_ret = (sp500.iloc[-1] / sp500.iloc[-30] - 1) * 100
            
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
            df = pd.concat([
                hsi.pct_change().dropna(),
                usdcny.pct_change().dropna(),
                sp500.pct_change().dropna()
            ], axis=1, keys=['恒指', '人民币', '标普']).dropna()
            
            corr_hsi_sp500 = df['恒指'].corr(df['标普'])
            corr_hsi_cny = df['恒指'].corr(-df['人民币'])  # 贬值应对港股不利
            corr_sp500_cny = df['标普'].corr(-df['人民币'])
            
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
            if not (validate_data(margin_data, 50) and validate_data(shibor_data, 30)):
                self.logger('流动性分析', 'warning', '数据不足')
                return None
            
            current_margin = margin_data.iloc[-1] / 100000000
            margin_change_5d = margin_data.pct_change(5).iloc[-1] * 100
            margin_change_30d = margin_data.pct_change(30).iloc[-1] * 100
            
            current_shibor = shibor_data.iloc[-1] if len(shibor_data) > 0 else np.nan
            shibor_change = shibor_data.pct_change().iloc[-1] * 100 if len(shibor_data) > 1 else 0
            
            print(f"\n📊 流动性指标:")
            print(f"  融资余额: {current_margin:.0f}亿")
            print(f"    └─5日变化: {margin_change_5d:+.2f}%")
            print(f"    └─30日变化: {margin_change_30d:+.2f}%")
            print(f"  Shibor 1M: {current_shibor:.2f}%")
            print(f"    └─日变化: {shibor_change:+.2f}%")
            
            if validate_data(bond_data) and 'spread' in bond_data.columns:
                current_spread = bond_data['spread'].iloc[-1]
                spread_change_5d = bond_data['spread'].diff(5).iloc[-1]
                print(f"  中美利差: {current_spread:.2f}bp (5日变化: {spread_change_5d:+.0f}bp)")
            
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
            
            # 股债性价比
            if validate_data(bond_data) and 'spread' in bond_data.columns:
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
            
            # 流动性评分
            liquidity_score = 0
            if margin_change_5d > 1: liquidity_score += 1
            elif margin_change_5d < -1: liquidity_score -= 1
            
            if current_shibor < 2.5: liquidity_score += 1
            elif current_shibor > 3.0: liquidity_score -= 1
            
            if validate_data(bond_data) and 'spread' in bond_data.columns:
                if bond_data['spread'].iloc[-1] > 50: liquidity_score -= 1
            
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
    
    def analyze_sector_rotation(self):
        """
        分析行业轮动
        识别领涨板块和市场风格
        """
        print("\n" + "="*70)
        print("【行业轮动解读】")
        print("="*70)
        
        try:
            from config import SECTOR_ETFS
            
            tickers = list(SECTOR_ETFS.values())
            print(f"📥 正在下载 {len(tickers)} 个行业ETF数据...")
            
            # 批量下载
            raw_data = self.fetcher.batch_download(tickers, period="1mo")
            
            returns = {}
            for sector, ticker in SECTOR_ETFS.items():
                try:
                    if not ticker:
                        returns[sector] = np.nan
                        continue
                    
                    # 提取数据
                    if isinstance(raw_data, pd.DataFrame) and ticker in raw_data.columns:
                        data = raw_data[ticker].dropna()
                    else:
                        # 降级到单个下载
                        data = self.fetcher.get_yf_data(ticker, period='1mo')
                        if isinstance(data, pd.DataFrame):
                            data = data['Close'].dropna()
                    
                    if validate_data(data, 10):
                        returns[sector] = (data.iloc[-1] / data.iloc[0] - 1) * 100
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
                'dispersion': dispersion,
                'rotation_signal': rotation_signal,
                'style_str': style_str,
                'sorted_returns': sorted_returns,
                'rotation_desc': rotation_desc if len(sorted_returns) >= 3 else ""
            }
            
        except Exception as e:
            print(f"❌ 行业轮动分析失败: {e}")
            self.logger('行业轮动分析', 'error', str(e))
            return None
