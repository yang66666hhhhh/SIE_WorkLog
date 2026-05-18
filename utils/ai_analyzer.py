import openai
import pandas as pd
from typing import List, Dict, Any


class AIAnalyzer:

    SYSTEM_PROMPT = """你是一个专业的工作数据分析助手。根据用户提供的工时数据统计信息，提供简洁、有价值的分析洞察。

分析维度：
1. 工时分布 - 各来源/设备的占比和合理性
2. 工作效率 - 任务耗时异常检测、高负荷时段
3. 趋势分析 - 周/月变化趋势
4. 优化建议 - 基于数据提出具体可行的改进建议

要求：
- 用中文回复
- 每个洞察点简洁明了，最多2句话
- 提供数据支撑（具体数字和百分比）
- 如有异常情况，明确指出
"""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client = None
        if api_key:
            self._client = openai.OpenAI(api_key=api_key, base_url=base_url if base_url else None)

    def generate_summary(self, df: pd.DataFrame) -> str:
        if not self.api_key or not self._client:
            return self._rule_based_insights(df)

        try:
            stats = self._calculate_stats(df)
            user_prompt = self._build_prompt(stats)

            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"⚠️ AI 分析失败: {str(e)}\n\n---\n\n{self._rule_based_insights(df)}"

    def _calculate_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        stats = {}

        stats["总工时"] = df["工时"].sum()
        stats["总任务数"] = len(df)

        daily_sum = df.groupby("日期")["工时"].sum()
        stats["日均工时"] = daily_sum.mean()
        stats["工作天数"] = len(daily_sum)
        stats["日工时标准差"] = daily_sum.std() if len(daily_sum) > 1 else 0

        if "来源" in df.columns:
            src_stats = df.groupby("来源")["工时"].agg(["sum", "count"]).round(1)
            stats["来源分布"] = src_stats.to_dict()

        if "线体/设备" in df.columns:
            dev_stats = df.groupby("线体/设备")["工时"].agg(["sum", "count"]).round(1).sort_values("sum", ascending=False)
            stats["设备分布"] = dev_stats.head(5).to_dict()

        if "任务类型" in df.columns:
            type_stats = df.groupby("任务类型")["工时"].agg(["sum", "count"]).round(1).sort_values("sum", ascending=False)
            stats["任务类型分布"] = type_stats.to_dict()

        stats["平均任务耗时"] = df["工时"].mean().round(2)
        stats["最长任务"] = df["工时"].max()

        if "是否周末" in df.columns:
            weekend_hours = df[df["是否周末"] == True]["工时"].sum()
            stats["周末工时"] = weekend_hours
            stats["周末占比"] = f"{weekend_hours / stats['总工时'] * 100:.0f}%" if stats['总工时'] > 0 else "0%"

        daily_hours = df.groupby("日期")["工时"].sum().sort_index()
        if len(daily_hours) >= 2:
            stats["近7天趋势"] = "下降" if daily_hours.tail(3).mean() < daily_hours.head(3).mean() else "上升"

        return stats

    def _build_prompt(self, stats: Dict) -> str:
        prompt = f"""请分析以下工作数据统计：

【总体数据】
- 总工时: {stats['总工时']:.1f}h
- 总任务数: {stats['总任务数']}个
- 工作天数: {stats.get('工作天数', 'N/A')}天
- 日均工时: {stats['日均工时']:.1f}h
- 平均任务耗时: {stats['平均任务耗时']}h
- 最长任务: {stats['最长任务']:.1f}h
- 日工时波动: {stats.get('日工时标准差', 0):.1f}h

"""
        if "来源分布" in stats:
            prompt += "【来源分布】\n"
            for src, data in stats["来源分布"]["sum"].items():
                prompt += f"- {src}: {data:.1f}h\n"

        if "设备分布" in stats:
            prompt += "\n【设备分布 TOP5】\n"
            for dev, data in stats["设备分布"]["sum"].items():
                prompt += f"- {dev}: {data:.1f}h\n"

        if "任务类型分布" in stats:
            prompt += "\n【任务类型分布】\n"
            for task_type, data in stats["任务类型分布"]["sum"].items():
                prompt += f"- {task_type}: {data:.1f}h\n"

        if "周末工时" in stats:
            prompt += f"\n【周末工作】: {stats['周末工时']:.1f}h ({stats.get('周末占比', 'N/A')})\n"

        if "近7天趋势" in stats:
            prompt += f"\n【近7天趋势】: {stats['近7天趋势']}\n"

        prompt += """
请提供4-6个最有价值的分析洞察，包含数据支撑和改进建议。
"""
        return prompt

    def _rule_based_insights(self, df: pd.DataFrame) -> str:
        from utils.analyzer import generate_insights
        return generate_insights(df)
