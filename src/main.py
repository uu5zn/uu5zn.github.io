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
from analyzer import MarketAnalyzer
from charts import ChartGenerator
from reporter import ReportGenerator
from data_fetcher import DataFetcher

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
    data_fetcher = DataFetcher(logger_func)
    analyzer = MarketAnalyzer(logger_func)
    chart_gen = ChartGenerator(logger_func)
    
    print(f"初始化完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return log, data_fetcher, analyzer, chart_gen

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

def task_margin_analysis(analyzer, chart_gen):
    """任务2: 融资余额分析 - 使用缓存数据"""
    print("\n【任务2】融资余额分析...")
    
    try:
        # 调用analyzer中的新方法
        result = analyzer.analyze_margin_analysis()
        
        if not result['success']:
            print(f"⚠️ {result['message']}")
            return False
        
        # 绘图
        chart_gen.plot_line(
            {'融资余额': result['margin_values'].iloc[-50:], 'ma10': result['margin_ma10'].iloc[-50:]},
            '融资余额与MA10', ['融资余额', 'MA10'], ['r', 'b'],
            save_path='rongziyue_ma.png'
        )
        
        # 打印最新值
        print(f"最新融资余额: {result['last_margin']:.1f}M")
        
        if result['below_ma10']:
            print("⚠️  警告: 融资余额低于MA10，资金流出")
        
        return True
        
    except Exception as e:
        print(f"❌ 融资余额分析失败: {e}")
        return False

def task_multi_indicator(analyzer, chart_gen):
    """任务3: 多指标对比 - 使用缓存数据"""
    print("\n【任务3】多指标对比...")
    
    try:
        # 调用analyzer中的新方法
        result = analyzer.analyze_multi_indicator()
        
        if not result['success']:
            print(f"⚠️ {result['message']}")
            return False
        
        # 归一化绘图
        chart_gen.plot_line(
            {
                '融资余额': normalize(result['margin_values']),
                '汇率': normalize(-result['exchange_rate_values']),
                '中美利差': normalize(result['bond_values']),
                '500ETF': normalize(result['etf_500'])
            },
            '归一化指标对比', ['融资余额', '汇率', '中美利差', '500ETF'],
            ['g', 'c', 'w', 'r'], save_path='rongziyue_1.png'
        )
        
        chart_gen.plot_line(
            {
                '融资余额': normalize(result['margin_data']),
                '300ETF': normalize(result['etf_300']),
                '1000ETF': normalize(result['etf_1000'])
            },
            '融资余额与ETF对比', ['融资余额', '300ETF', '1000ETF'],
            ['g', 'r', 'b'], save_path='rongziyue_2.png'
        )
        
        chart_gen.plot_line(
            {
                'Shibor 1M': normalize(result['shibor_data'].iloc[-200:]),
                '中美国债利差': normalize(result['bond_data'].iloc[-200:])
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

def task_correlation(analyzer, chart_gen):
    """任务5: 相关性分析 - 使用缓存数据"""
    print("\n【任务5】相关性分析...")
    
    try:
        # 调用analyzer中的新方法
        result = analyzer.analyze_correlation()
        
        if not result['success']:
            print(f"⚠️ {result['message']}")
            return False
        
        print(f"恒生指数与Russell 2000相关性: {result['correlation']:.4f}")
        
        # 绘图
        chart_gen.plot_line(
            {'HSI': result['df']['HSI']/result['df']['HSI'].iloc[0], 'RUT': result['df']['RUT']/result['df']['RUT'].iloc[0]},
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
    log, data_fetcher, analyzer, chart_gen = initialize()
    
    # 第一步：获取所有数据并生成缓存
    print("\n【数据获取】开始获取所有数据并生成缓存...")
    try:
        data_fetcher.fetch_all_data()
        print(f"✅ 数据获取完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_execution(log, "数据获取", "success", "所有数据已成功获取并缓存")
    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
        log_execution(log, "数据获取", "error", str(e))
    
    # 任务调度 - 基于缓存数据执行后续任务
    tasks = [
        ("K线图生成", lambda: task_kline_charts(chart_gen)),
        ("融资余额分析", lambda: task_margin_analysis(analyzer, chart_gen)),
        ("多指标对比", lambda: task_multi_indicator(analyzer, chart_gen)),
        ("油金比分析", lambda: task_oil_gold(chart_gen)),
        ("相关性分析", lambda: task_correlation(analyzer, chart_gen)),
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
    # 调用 analyzer 中的综合市场分析方法
    market_result = analyzer.analyze_market()
    
    # 将分析结果添加到日志中
    if 'insights' in market_result:
        for insight in market_result['insights']:
            log['insights'].append(insight)
    
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
