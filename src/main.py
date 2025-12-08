# -*- coding: utf-8 -*-
import sys
import os
import time
import pandas as pd
from datetime import datetime, timedelta

# 添加src到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import OUTPUT_DIR, INDICES, EXECUTION_LOG
from utils import setup_logging, log_execution, setup_matplotlib_fonts, check_available_fonts, normalize, capture_print
from data_fetcher import DataFetcher
from analyzer import MarketAnalyzer
from charts import ChartGenerator
from reporter import ReportGenerator

def initialize():
    """初始化系统"""
    print("\n" + "="*70)
    print("金融数据分析系统初始化".center(70))
    print("="*70)
    
    # 设置字体
    setup_matplotlib_fonts()
    check_available_fonts()
    
    # 初始化日志
    log = setup_logging()
    log['start_time'] = datetime.now().isoformat()
    
    # ✅ 修复：logger 函数必须接受 **kwargs
    def logger_func(category, status, message, **kwargs):
        """
        日志回调函数
        :param kwargs: 接收 chart_path 等额外参数
        """
        log_execution(log, category, status, message, **kwargs)
    
    # 创建核心组件
    fetcher = DataFetcher(logger_func)
    analyzer = MarketAnalyzer(fetcher, logger_func)
    chart_gen = ChartGenerator(logger_func, fetcher)
    
    print(f"初始化完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return log, fetcher, analyzer, chart_gen

def task_kline_charts(chart_gen):
    """任务1: 生成指数K线图"""
    print("\n【任务1】生成指数K线图...")
    success_count = 0
    
    for item in INDICES:
        ticker, filename = item[0], item[1]
        period = item[2] if len(item) > 2 else "1mo"
        
        try:
            if chart_gen.plot_kline(ticker, filename, period):
                success_count += 1
        except Exception as e:
            print(f"❌ K线图失败 {ticker}: {e}")
    
    return success_count

def task_margin_analysis(fetcher, analyzer, chart_gen):
    """任务2: 融资余额分析"""
    print("\n【任务2】融资余额分析...")
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=300)
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        
        margin_data = fetcher.get_data('融资余额', start_date_str, end_date_str)
        
        if len(margin_data) < 50:
            print("⚠️ 融资余额数据不足")
            return False
        
        # 计算均线
        margin_ma10 = margin_data.rolling(10).mean()
        
        # 绘图
        chart_gen.plot_line(
            {'融资余额': margin_data.iloc[-50:], 'ma10': margin_ma10.iloc[-50:]},
            '融资余额与MA10', ['融资余额', 'MA10'], ['r', 'b'],
            save_path='rongziyue_ma.png'
        )
        
        # 打印最新值
        last_margin = margin_data.iloc[-1] / 1000000
        last_ma10 = margin_ma10.iloc[-1]
        print(f"最新融资余额: {last_margin:.1f}M")
        
        if margin_data.iloc[-1] < last_ma10:
            print("⚠️  警告: 融资余额低于MA10，资金流出")
        
        return True
        
    except Exception as e:
        print(f"❌ 融资余额分析失败: {e}")
        return False

def task_multi_indicator(fetcher, analyzer, chart_gen):
    """任务3: 多指标对比"""
    print("\n【任务3】多指标对比...")
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)  # 调整为180天，解决横坐标过长问题
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        
        # 获取数据
        margin_data = fetcher.get_data('融资余额', start_date_str, end_date_str)
        exchange_rate = fetcher.get_data('美元', start_date_str, end_date_str)
        shibor_data = fetcher.get_data('Shibor 1M', start_date_str, end_date_str)
        bond_data = fetcher.get_data('中美国债收益率', start_date_str, end_date_str)
        etf_300 = fetcher.get_data('ETF_510300', start_date_str, end_date_str)
        etf_1000 = fetcher.get_data('ETF_159845', start_date_str, end_date_str)
        etf_500 = fetcher.get_data('ETF_510500', start_date_str, end_date_str)
        
        # 归一化绘图
        chart_gen.plot_line(
            {
                '融资余额': normalize(margin_data),
                '汇率': normalize(-exchange_rate),
                '中美利差': normalize(bond_data.iloc[-180:]),
                '500ETF': normalize(etf_500)
            },
            '归一化指标对比', ['融资余额', '汇率', '中美利差', '500ETF'],
            ['g', 'c', 'w', 'r'], save_path='rongziyue_1.png'
        )
        
        chart_gen.plot_line(
            {
                '融资余额': normalize(margin_data),
                '300ETF': normalize(etf_300),
                '1000ETF': normalize(etf_1000)
            },
            '融资余额与ETF对比', ['融资余额', '300ETF', '1000ETF'],
            ['g', 'r', 'b'], save_path='rongziyue_2.png'
        )
        
        chart_gen.plot_line(
            {
                'Shibor 1M': normalize(shibor_data.iloc[-200:]),
                '中美国债利差': normalize(bond_data.iloc[-200:])
            },
            '流动性指标', ['Shibor 1M', '中美国债利差'], ['r', 'g'],
            save_path='liudongxing.png'
        )
        
        return True
        
    except Exception as e:
        print(f"❌ 多指标对比失败: {e}")
        return False

def task_oil_gold(chart_gen):
    """任务4: 油金比分析"""
    print("\n【任务4】油金比分析...")
    return chart_gen.plot_oil_gold_ratio()

def task_correlation(fetcher, chart_gen):
    """任务5: 相关性分析"""
    print("\n【任务5】相关性分析...")
    
    try:
        # 直接使用yfinance下载数据，返回MultiIndex DataFrame
        import yfinance as yf
        from config import YF_TIMEOUT
        
        hsi_df = yf.download(['^HSI'], period='300d', interval='1d', auto_adjust=True, progress=False, timeout=YF_TIMEOUT)
        rut_df = yf.download(['^RUT'], period='300d', interval='1d', auto_adjust=True, progress=False, timeout=YF_TIMEOUT)
        
        if hsi_df.empty or rut_df.empty:
            return False
        
        # 确保返回MultiIndex结构
        def ensure_multiindex(df, ticker):
            """确保DataFrame是MultiIndex结构"""
            if isinstance(df.columns, pd.MultiIndex):
                return df
            else:
                # 单个ticker情况，转换为MultiIndex
                multi_cols = pd.MultiIndex.from_product([['Open', 'High', 'Low', 'Close', 'Volume'], [ticker]])
                result = pd.DataFrame(df.values, index=df.index, columns=multi_cols)
                return result
        
        hsi_df = ensure_multiindex(hsi_df, '^HSI')
        rut_df = ensure_multiindex(rut_df, '^RUT')
        
        # ✅ 修复：正确访问 MultiIndex
        def extract_close(df, ticker):
            """从 MultiIndex DataFrame 提取 Close 序列"""
            if isinstance(df.columns, pd.MultiIndex):
                try:
                    return df['Close'][ticker].dropna()
                except KeyError:
                    # 降级处理
                    return df.iloc[:, 0].dropna()
            else:
                # 扁平结构（不应该发生）
                return df.iloc[:, 0].dropna()
        
        hsi_close = extract_close(hsi_df, '^HSI')
        rut_close = extract_close(rut_df, '^RUT')
        
        if len(hsi_close) < 30 or len(rut_close) < 30:
            return False
        
        df = pd.concat([hsi_close, rut_close], axis=1, keys=['HSI', 'RUT']).dropna()
        
        if len(df) < 30:
            return False
        
        correlation = float(df['HSI'].corr(df['RUT']))
        print(f"恒生指数与Russell 2000相关性: {correlation:.4f}")
        
        # 绘图
        chart_gen.plot_line(
            {'HSI': df['HSI']/df['HSI'].iloc[0], 'RUT': df['RUT']/df['RUT'].iloc[0]},
            '恒生指数与Russell 2000走势对比(归一化)',
            ['HSI', 'RUT'], ['#3498db', '#e74c3c'],
            save_path='hsi_rut_comparison.png'
        )
        
        return True
        
    except Exception as e:
        print(f"❌ 相关性分析失败: {e}")
        return False
def task_pe_bond_spread(chart_gen):
    """任务6: 股债利差"""
    print("\n【任务6】股债利差分析...")
    return chart_gen.plot_pe_bond_spread()

def task_sector_rotation(analyzer, chart_gen):
    """任务7: 行业轮动"""
    print("\n【任务7】行业轮动分析...")
    result = analyzer.analyze_sector_rotation()
    
    if result and 'sorted_returns' in result:
        chart_gen.plot_sector_rotation(result['sorted_returns'])
        return True
    
    return False

def main():
    """主函数"""
    # 初始化
    log, fetcher, analyzer, chart_gen = initialize()
    
    # 任务调度
    tasks = [
        ("K线图生成", lambda: task_kline_charts(chart_gen)),
        ("融资余额分析", lambda: task_margin_analysis(fetcher, analyzer, chart_gen)),
        ("多指标对比", lambda: task_multi_indicator(fetcher, analyzer, chart_gen)),
        ("油金比分析", lambda: task_oil_gold(chart_gen)),
        ("相关性分析", lambda: task_correlation(fetcher, chart_gen)),
        ("股债利差", lambda: task_pe_bond_spread(chart_gen)),
        ("行业轮动", lambda: task_sector_rotation(analyzer, chart_gen)),
    ]
    
    # 执行
    start_time = time.time()
    success_count = 0
    
    # 在 main() 函数的任务调度部分

    for task_name, task_func in tasks:
        try:
            if task_func():
                success_count += 1
                # ✅ 修复：添加 message 参数
                log_execution(log, task_name, 'success', '任务执行成功')
            else:
                # 这行已经是正确的
                log_execution(log, task_name, 'warning', '执行失败')
        except Exception as e:
            print(f"❌ 任务失败 {task_name}: {e}")
            # 这行也是正确的
            log_execution(log, task_name, 'error', str(e))
    
    # 市场解读（核心分析）
    print("\n" + "📈 开始生成综合市场解读".center(70, "="))
    
    # 初始化输出捕获存储
    log['detailed_output'] = {
        'sector_rotation': '',
        'index_divergence': '',
        'risk_regime': '',
        'china_us_linkage': '',
        'liquidity_conditions': ''
    }
    
    try:
        # 行业轮动
        from analyzer import MarketAnalyzer
        # 先检查analyze_sector_rotation方法是否存在
        if hasattr(analyzer, 'analyze_sector_rotation'):
            success, sector_result, sector_output = capture_print(analyzer.analyze_sector_rotation)
            log['detailed_output']['sector_rotation'] = sector_output
            if sector_result:
                log['insights'].append(('行业轮动', f"行业轮动强度{sector_result['rotation_strength']:.2f}% {sector_result['leading']}"))
        
        # 指数差异
        success, divergence_result, divergence_output = capture_print(analyzer.analyze_index_divergence)
        log['detailed_output']['index_divergence'] = divergence_output
        if divergence_result:
            log['insights'].append(('指数差异', divergence_result['insight']))
        
        # 风险环境
        success, risk_result, risk_output = capture_print(analyzer.analyze_risk_regime)
        log['detailed_output']['risk_regime'] = risk_output
        if risk_result:
            log['insights'].append(('风险环境', f"VIX{risk_result['vix']:.2f} 国债{risk_result['bond_yield']:.2f}% {risk_result['risk_level']}"))
            log['market_signals']['risk_level'] = risk_result['risk_level']
        
        # 中美联动
        success, linkage_result, linkage_output = capture_print(analyzer.analyze_china_us_linkage)
        log['detailed_output']['china_us_linkage'] = linkage_output
        if linkage_result:
            log['insights'].append(('中美联动', f"恒指{linkage_result['hsi_ret']:+.2f}% 汇率{linkage_result['cny_change']:+.2f}% {linkage_result['linkage']}"))
        
        # 流动性
        end_date = datetime.now()
        start_date = end_date - timedelta(days=300)
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        
        margin_data = fetcher.get_data('融资余额', start_date_str, end_date_str)
        shibor_data = fetcher.get_data('Shibor 1M', start_date_str, end_date_str)
        bond_data = fetcher.get_data('中美国债收益率', start_date_str, end_date_str)
        
        success, liquidity_result, liquidity_output = capture_print(analyzer.analyze_liquidity_conditions, margin_data, shibor_data, bond_data)
        log['detailed_output']['liquidity_conditions'] = liquidity_output
        if liquidity_result:
            log['insights'].append(('流动性', f"融资{liquidity_result['margin']:.0f}亿 Shibor{liquidity_result['shibor']:.2f}% {liquidity_result['liquidity_env']}"))
            log['market_signals']['liquidity_env'] = liquidity_result['liquidity_env']
        
        # 股债性价比
        success, pe_bond_result, pe_bond_output = capture_print(analyzer.analyze_pe_bond_spread)
        log['detailed_output']['pe_bond_spread'] = pe_bond_output
        if pe_bond_result:
            log['insights'].append(('股债利差', pe_bond_result['股债利差']))
            log['market_signals']['pe_bond_signal'] = pe_bond_result['信号']
        
        print("\n" + "📊 市场解读完成".center(70, "="))
        
    except Exception as e:
        print(f"❌ 市场解读失败: {e}")
        log_execution(log, '市场解读', 'error', str(e))
    
    # 生成报告
    log['duration'] = f"{time.time() - start_time:.2f}秒"
    
    # 🔧 传递 logger 给 ReportGenerator
    reporter = ReportGenerator(log, lambda *args: log_execution(log, *args))
    reporter.save_json_report()
    reporter.generate_markdown_report()
    
    # 总结
    print("\n" + "="*70)
    print(f"执行完成: {success_count}/{len(tasks)} 任务成功")
    print(f"总耗时: {log['duration']}")
    print(f"图表输出: {len([t for t in log['tasks'] if t.get('chart_path')])} 张")
    print(f"风险提示: {len(log['warnings'])} 个")
    print(f"查看输出: ls -lh {os.path.abspath(OUTPUT_DIR)}")
    print("="*70)
    
    return success_count == len(tasks)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n用户中断执行")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n致命错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
