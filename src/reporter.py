# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from config import OUTPUT_DIR

class ReportGenerator:
    def __init__(self, execution_log):
        """
        报告生成器
        :param execution_log: 执行日志字典
        """
        self.log = execution_log
    
    def save_json_report(self):
        """保存JSON格式执行报告"""
        try:
            report_path = os.path.join(OUTPUT_DIR, '执行报告.json')
            self.log['end_time'] = datetime.now().isoformat()
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.log, f, ensure_ascii=False, indent=2)
            
            print(f"\n📋 JSON报告已保存: {report_path}")
            return report_path
        except Exception as e:
            print(f"❌ JSON报告保存失败: {e}")
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
                index_ch
