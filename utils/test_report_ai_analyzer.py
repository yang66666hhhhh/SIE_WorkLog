"""
测试报告 AI 分析模块
支持规则分析 + LLM 增强分析
"""
import pandas as pd
from typing import Dict, Any
from datetime import datetime


class TestReportAIAnalyzer:
    """测试报告 AI 分析器"""

    SYSTEM_PROMPT = """你是一个专业的自动化测试报告分析助手。根据用户提供的测试问题统计数据，提供简洁、有价值的分析洞察。

分析维度：
1. 问题趋势 - 各状态分布、解决率变化
2. 高频问题 - 哪些设备/线体问题最多
3. 部门问题分布 - 哪些部门问题最多
4. 根因分析 - 问题是否有规律
5. 改进建议 - 如何减少问题发生

要求：
- 用中文回复
- 每个洞察点简洁明了，最多2句话
- 提供数据支撑（具体数字和百分比）
- 如有异常情况，明确指出
"""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client = None
        if api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)
            except Exception:
                pass

    def generate_insights(self, stats: Dict[str, Any], problem_list: list = None) -> str:
        """生成分析洞察"""
        if self._client and self.api_key:
            try:
                return self._llm_insights(stats, problem_list)
            except Exception:
                pass
        return self._rule_insights(stats, problem_list)

    def _rule_insights(self, stats: Dict[str, Any], problem_list: list = None) -> str:
        """基于规则的分析"""
        lines = ["## 📋 测试报告 AI 分析\n"]

        total = stats.get("total", 0)
        pending = stats.get("pending", 0)
        investigating = stats.get("investigating", 0)
        resolved = stats.get("resolved", 0)

        if total == 0:
            return "\n".join(lines) + "**暂无问题数据**\n"

        resolve_rate = resolved / total * 100 if total > 0 else 0

        lines.append("### 🔍 问题概览\n")
        lines.append(f"| 指标 | 数值 |")
        lines.append(f"|------|------|")
        lines.append(f"| 问题总数 | **{total}** |")
        lines.append(f"| 🔴 待处理 | **{pending}** ({pending/total*100:.0f}%) |")
        lines.append(f"| 🟡 排查中 | **{investigating}** ({investigating/total*100:.0f}%) |")
        lines.append(f"| 🟢 已解决 | **{resolved}** ({resolve_rate:.0f}%) |")
        lines.append("")

        lines.append("### 📊 问题分布\n")

        by_line = stats.get("by_line", {})
        if by_line:
            lines.append("**按线体:**")
            sorted_lines = sorted(by_line.items(), key=lambda x: x[1].get("total", 0), reverse=True)
            for line_name, line_stats in sorted_lines[:5]:
                t = line_stats.get("total", 0)
                p = line_stats.get("pending", 0)
                lines.append(f"- **{line_name}**: {t}个问题 ({p}待处理)")
            lines.append("")

        by_category = stats.get("by_category", {})
        if by_category:
            lines.append("**按部门:**")
            sorted_cats = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
            for cat_name, count in sorted_cats[:5]:
                lines.append(f"- **{cat_name}**: {count}个问题")
            lines.append("")

        lines.append("### 💡 分析洞察\n")

        recommendations = []

        if resolve_rate < 30:
            recommendations.append(f"🔴 **解决率偏低** ({resolve_rate:.0f}%)，建议加快问题处理节奏")
        elif resolve_rate >= 70:
            recommendations.append(f"🟢 **解决率良好** ({resolve_rate:.0f}%)，继续保持")

        if pending > 5:
            recommendations.append(f"🔴 **待处理问题较多** ({pending}个)，建议优先处理阻塞性问题")

        if by_line:
            top_line = sorted_lines[0]
            line_total = top_line[1].get("total", 0)
            if line_total > total * 0.4:
                recommendations.append(f"🟡 **{top_line[0]}** 问题集中 ({line_total}个, 占{total*100:.0f}%)，建议重点关注")

        if problem_list and len(problem_list) > 0:
            from collections import Counter
            desc_text = " ".join([str(p.get("原始描述", "")) for p in problem_list]).lower()
            keywords = []
            if "agv" in desc_text or "小车" in desc_text:
                keywords.append("AGV/小车")
            if "失联" in desc_text or "通讯" in desc_text:
                keywords.append("通讯失联")
            if "配方" in desc_text or "参数" in desc_text:
                keywords.append("配方/参数")
            if keywords:
                recommendations.append(f"📌 **高频关键词**: {', '.join(keywords)}")

        if not recommendations:
            recommendations.append("✅ 当前无明显异常，建议继续保持当前工作节奏")

        for rec in recommendations:
            lines.append(f"- {rec}")

        lines.append("\n---")
        lines.append(f"*分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        return "\n".join(lines)

    def _llm_insights(self, stats: Dict[str, Any], problem_list: list = None) -> str:
        """LLM 增强分析"""
        try:
            user_prompt = self._build_prompt(stats, problem_list)
            response = self._client.chat.completions.create(
                model=self.model or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"⚠️ AI 分析失败: {str(e)}\n\n---\n\n{self._rule_insights(stats, problem_list)}"

    def _build_prompt(self, stats: Dict[str, Any], problem_list: list = None) -> str:
        prompt = f"""请分析以下测试报告问题统计：

【总体统计】
- 问题总数: {stats.get('total', 0)}
- 待处理: {stats.get('pending', 0)}
- 排查中: {stats.get('investigating', 0)}
- 已解决: {stats.get('resolved', 0)}
- 解决率: {stats.get('resolved', 0) / stats.get('total', 1) * 100:.1f}%

"""

        by_line = stats.get("by_line", {})
        if by_line:
            prompt += "【按线体分布】\n"
            for line, data in sorted(by_line.items(), key=lambda x: x[1].get("total", 0), reverse=True)[:5]:
                prompt += f"- {line}: 共{data.get('total', 0)}个 (待{data.get('pending', 0)}, 排查{data.get('investigating', 0)}, 已解决{data.get('resolved', 0)})\n"

        by_category = stats.get("by_category", {})
        if by_category:
            prompt += "\n【按部门分布】\n"
            for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True)[:5]:
                prompt += f"- {cat}: {count}个问题\n"

        if problem_list and len(problem_list) > 0:
            recent_problems = problem_list[:10]
            prompt += "\n【最近问题示例】\n"
            for p in recent_problems:
                prompt += f"- [{p.get('状态', '')}] {p.get('来源', '')}: {str(p.get('原始描述', ''))[:50]}...\n"

        prompt += """
请提供4-6个最有价值的分析洞察和改进建议，包含数据支撑。
"""
        return prompt
