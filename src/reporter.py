# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from config import OUTPUT_DIR

class ReportGenerator:
    def __init__(self, execution_log, logger_callback=None):  # 🔧 添加 logger 参数
        """
        报告生成器
        :param execution_log: 执行日志字典
        :param logger_callback: 日志回调函数（可选）
        """
        self.log = execution_log
        self.logger = logger_callback  # 🔧 保存 logger 引用
    
    def save_json_report(self):
        """保存JSON格式执行报告"""
        try:
            report_path = os.path.join(OUTPUT_DIR, '执行报告.json')
            self.log['end_time'] = datetime.now().isoformat()
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.log, f, ensure_ascii=False, indent=2)
            
            print(f"\n📋 JSON报告已保存: {report_path}")
            
            # 🔧 使用 logger 记录
            if self.logger:
                self.logger('JSON报告', 'success', f'路径: {report_path}')
            
            return report_path
        except Exception as e:
            print(f"❌ JSON报告保存失败: {e}")
            if self.logger:
                self.logger('JSON报告', 'error', str(e))
            return None
    
    def generate_markdown_report(self, **kwargs):
        """
        生成Markdown格式综合报告
        :param kwargs: 额外参数
        """
        print("\n" + "📝 生成Markdown报告".center(70, "="))
        
        try:
            report_path = os.path.join(OUTPUT_DIR, '市场分析报告.md')
            
            # 提取洞察
            insights = {}
            for category, insight in self.log.get('insights', []):
                insights[category] = insight
            
            # 统计信息
            total_tasks = len(self.log.get('tasks', []))
            success_tasks = len([t for t in self.log.get('tasks', []) if t.get('status') == 'success'])
            warnings = len(self.log.get('warnings', []))
            errors = len(self.log.get('errors', []))
            charts = len([t for t in self.log.get('tasks', []) if t.get('chart_path')])
            
            with open(report_path, 'w', encoding='utf-8') as f:
                # 报告头部
                f.write(f"""# 📊 每日市场分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**数据来源**: yfinance, akshare, 新浪财经  
**分析周期**: 3个月滚动窗口  
**执行状态**: {'✅ 全部成功' if errors == 0 else '⚠️ 部分失败'}

---

## 🎯 执行摘要

- **总任务数**: {total_tasks}
- **成功任务**: {success_tasks}
- **警告数量**: {warnings}
- **错误数量**: {errors}
- **生成图表**: {charts} 张
- **总耗时**: {self.log.get('duration', 'N/A')}

---

## 💡 核心市场洞察

### 1️⃣ 指数结构分析
""")
                # 指数洞察
                if '指数差异' in insights:
                    f.write(f"{insights['指数差异']}\n")
                else:
                    f.write("- 数据暂缺\n")
                
                f.write("""
### 2️⃣ 风险环境评估
""")
                if '风险环境' in insights:
                    f.write(f"- {insights['风险环境']}\n")
                
                f.write("""
### 3️⃣ 中美市场联动
""")
                if '中美联动' in insights:
                    f.write(f"- {insights['中美联动']}\n")
                
                f.write("""
### 4️⃣ 流动性状况
""")
                if '流动性' in insights:
                    f.write(f"- {insights['流动性']}\n")
                else:
                    f.write("- 数据暂缺\n")
                
                f.write("""
### 5️⃣ 股债性价比
""")
                if '股债利差' in insights:
                    f.write(f"- {insights['股债利差']}\n")
                else:
                    f.write("- 数据暂缺\n")
                
                f.write("""
### 6️⃣ 行业轮动
""")
                if '行业轮动' in insights:
                    f.write(f"- {insights['行业轮动']}\n")
                else:
                    f.write("- 数据暂缺\n")
                
                f.write("\n---\n\n")
                
                # 图表展示
                f.write("""## 📈 图表分析

### 🔷 全球核心指数
""")
                index_charts = [
                    ('sp500.png', '标普500指数'),
                    ('nasdaq.png', '纳斯达克100指数'),
                    ('rs2000.png', '罗素2000小盘股'),
                    ('hsi.png', '恒生指数'),
                    ('rmb.png', '人民币汇率')
                ]
                
                for chart_file, title in index_charts:
                    if os.path.exists(os.path.join(OUTPUT_DIR, chart_file)):
                        f.write(f"""
#### {title}
![{title}](./{chart_file})
""")
                    else:
                        f.write(f"#### {title}\n❌ 图表生成失败\n\n")
                
                f.write("""
### 🔷 风险与利率指标
#### 美国10年期国债收益率
![10Y国债](./tenbond.png)

#### VIX恐慌指数
![VIX](./vix.png)

#### 油金比 vs 美债收益率
![油金比](./jyb_gz.png)

### 🔷 中国市场流动性
#### 融资余额与10日均线
![融资余额](./rongziyue_ma.png)

#### 多指标归一化对比
![归一化指标](./rongziyue_1.png)

#### 流动性指标
![流动性指标](./liudongxing.png)

### 🔷 股债性价比
#### 上证50股债利差
![股债利差](./guzhaixicha.png)

### 🔷 跨市场相关性
#### 恒生指数 vs Russell 2000
![相关性](./hsi_rut_comparison.png)

### 🔷 行业轮动
#### 近1月行业ETF表现
![行业轮动](./sector_rotation.png)

---
""")
                
                # 资产配置建议
                f.write("""## 💼 资产配置建议

### 基于当前市场环境的配置
""")
                
                # 提取信号
                risk_level = self.log.get('market_signals', {}).get('risk_level', '')
                equity_signal = self.log.get('market_signals', {}).get('equity_signal', '')
                liquidity_env = self.log.get('market_signals', {}).get('liquidity_env', '')
                
                # 根据信号生成配置
                if '🔴 高风险' in risk_level:
                    equity, bond, cash = "30%", "50%", "20%"
                    strategy = "保守配置，防御为主"
                elif '🟢 低风险' in risk_level and '性价比高' in str(equity_signal):
                    equity, bond, cash = "70%", "20%", "10%"
                    strategy = "积极进取，把握机会"
                else:
                    equity, bond, cash = "50%", "40%", "10%"
                    strategy = "平衡配置，动态调整"
                
                f.write(f"""
| 资产类别 | 建议比例 | 说明 |
|----------|----------|------|
| **股票** | {equity} | {strategy} |
| **债券** | {bond} | 作为稳定器，对冲风险 |
| **现金** | {cash} | 保持机动性 |
| **商品** | 0-10% | 根据通胀预期调整 |

### 区域配置建议
""")
                
                if '中美联动' in insights:
                    if '港股强' in insights['中美联动']:
                        f.write("- **港股**: 超配（估值修复+相对强势）\n")
                    elif '港股弱' in insights['中美联动']:
                        f.write("- **港股**: 低配（汇率压力+相对弱势）\n")
                    else:
                        f.write("- **港股**: 标配\n")
                
                if '指数差异' in insights:
                    if '成长' in insights['指数差异']:
                        f.write("- **美股**: 超配科技股（成长风格主导）\n")
                    elif '价值' in insights['指数差异']:
                        f.write("- **美股**: 超配价值股（周期风格主导）\n")
                    else:
                        f.write("- **美股**: 均衡配置\n")
                
                f.write("- **A股**: 根据融资余额和流动性信号调整\n")
                
                f.write("""
### 重点关注板块
""")
                if '行业轮动' in insights:
                    f.write(f"- {insights['行业轮动']}\n")
                else:
                    f.write("- 根据领涨板块动态调整\n")
                
                f.write("""
---

## ⚠️ 风险警示

### 当前需重点关注的风险
""")
                
                risk_list = []
                if '风险环境' in insights:
                    if '🚨' in insights['风险环境']:
                        risk_list.append("市场恐慌指数处于高位")
                    if '📈 高利率' in insights['风险环境']:
                        risk_list.append("利率环境压制资产估值")
                
                if '中美联动' in insights:
                    if '贬值' in insights['中美联动'] and '压力' in insights['中美联动']:
                        risk_list.append("人民币汇率贬值压力")
                
                if len(risk_list) > 0:
                    for i, risk in enumerate(risk_list, 1):
                        f.write(f"{i}. {risk}\n")
                else:
                    f.write("- 暂无显著系统性风险\n")
                
                f.write("""
### 技术指标警示
- **股债利差**: 若跌破-7.8%，股票吸引力极低
- **VIX**: 若升至30以上，恐慌情绪蔓延
- **融资余额**: 若连续3天跌破MA10，资金撤离信号
- **中美利差**: 若持续走阔，资本外流压力加大

### 操作建议
1. **止损纪律**: 个股亏损超过8%坚决止损
2. **仓位管理**: 单只股票不超过总仓位20%
3. **再平衡**: 每月末根据配置比例再平衡
4. **动态调整**: 根据宏观信号每季度调整战略配置

---

## 📋 数据与方法论说明

### 数据来源
| 数据类型 | 来源 | 更新频率 |
|----------|------|----------|
| 美股/全球指数 | Yahoo Finance | 实时 |
| 中国宏观经济 | akshare | 每日 |
| 汇率/利率 | 新浪财经/央行 | 每日 |
| 融资余额 | 东方财富 | 每日 |

### 分析方法论
1. **多因子框架**: 结合估值、趋势、情绪、流动性四个维度
2. **相对价值**: 通过股债利差判断资产性价比
3. **风险平价**: 关注股债相关性变化
4. **行为金融**: 融资余额反映市场情绪

### 模型局限性
- 历史数据不代表未来表现
- 极端市场环境下模型可能失效
- 需结合基本面分析综合判断

---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*  
*版本: v2.0 | 算法更新: 2024-12*  
*免责声明: 仅供参考，不构成投资建议。投资有风险，决策需谨慎。*
""")
            
            print(f"✅ Markdown报告已生成: {report_path}")
            
            # 🔧 使用 logger 记录
            if self.logger:
                self.logger('Markdown报告', 'success', f'路径: {report_path}')
            
            return report_path
            
        except Exception as e:
            print(f"❌ Markdown报告生成失败: {e}")
            if self.logger:
                self.logger('Markdown报告', 'error', str(e))
            return None
