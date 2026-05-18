"""
增强版规则分析模块 - 生成工作数据分析洞察报告
"""

import pandas as pd
import numpy as np
from datetime import timedelta


def generate_insights(df: pd.DataFrame) -> str:
    """
    生成分析报告（Markdown 格式）
    包含 6 大维度 + 可执行建议
    """
    if df is None or len(df) == 0:
        return "**暂无数据可供分析**"

    report = []
    report.append("## 📊 工作数据分析报告\n")

    report.append(_overview_cards(df))
    report.append(_health_assessment(df))
    report.append(_device_analysis(df))
    report.append(_task_type_diagnosis(df))
    report.append(_source_analysis(df))
    report.append(_trend_analysis(df))
    report.append(_problem_keyword_analysis(df))
    report.append(_action_recommendations(df))

    return "\n".join(report)


def _overview_cards(df: pd.DataFrame) -> str:
    """数据概览卡片"""
    lines = ["### 📋 数据概览\n"]
    total_hours = df["工时"].sum()
    total_tasks = len(df)
    work_days = df["日期"].nunique()
    daily_avg = total_hours / work_days if work_days else 0

    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 总工时 | **{total_hours:.1f}h** |")
    lines.append(f"| 任务数 | **{total_tasks}** 个 |")
    lines.append(f"| 工作日 | **{work_days}** 天 |")
    lines.append(f"| 日均工时 | **{daily_avg:.1f}h** |")

    if "来源" in df.columns:
        src_counts = df.groupby("来源").size()
        lines.append(f"| 来源分布 | {', '.join(f'{s}({c})' for s, c in src_counts.items())} |")

    lines.append("")
    return "\n".join(lines)


def _health_assessment(df: pd.DataFrame) -> str:
    """工时健康度评估"""
    lines = ["### 1️⃣ 工时健康度\n"]

    total_hours = df["工时"].sum()
    work_days = df["日期"].nunique()
    daily_avg = total_hours / work_days if work_days else 0

    if daily_avg >= 7.5:
        status_icon = "🟢"
        status_text = "正常"
    elif daily_avg >= 6:
        status_icon = "🟡"
        status_text = "偏低"
    else:
        status_icon = "🔴"
        status_text = "异常"

    lines.append(f"- **日均工时**: {daily_avg:.1f}h {status_icon} {status_text}")

    weekend_hours = df[df["是否周末"] == True]["工时"].sum()
    weekend_ratio = weekend_hours / total_hours * 100 if total_hours else 0
    lines.append(f"- **周末工时**: {weekend_hours:.1f}h ({weekend_ratio:.0f}%)")

    if weekend_ratio > 20:
        lines.append("  ⚠️ 周末工作占比过高")
    elif weekend_ratio == 0:
        lines.append("  ✅ 无周末加班")

    daily_hours = df.groupby("日期")["工时"].sum()
    if len(daily_hours) > 1:
        std_dev = daily_hours.std()
        cv = std_dev / daily_avg * 100 if daily_avg else 0
        lines.append(f"- **日工时波动**: {cv:.0f}%")
        if cv > 50:
            lines.append("  ⚠️ 波动较大，任务分配不均")

    lines.append("")
    return "\n".join(lines)


def _device_analysis(df: pd.DataFrame) -> str:
    """设备/线体分析"""
    lines = ["### 2️⃣ 设备分析\n"]

    if "线体/设备" not in df.columns:
        return "\n".join(lines) + "_（无可用设备数据）_\n\n"

    device_stats = df.groupby("线体/设备")["工时"].agg(["sum", "mean", "count"]).sort_values("sum", ascending=False)
    total = device_stats["sum"].sum()

    lines.append("| 设备 | 工时 | 占比 | 均耗时 |")
    lines.append("|------|------|------|--------|")
    for device, row in device_stats.iterrows():
        pct = row["sum"] / total * 100 if total else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        lines.append(f"| {device} | {row['sum']:.1f}h | {bar} {pct:.0f}% | {row['mean']:.1f}h |")

    overall_mean = df["工时"].mean()
    anomalies = device_stats[abs(device_stats["mean"] - overall_mean) / overall_mean > 0.3]
    if not anomalies.empty:
        lines.append("\n⚠️ **异常设备**（均耗时偏离均值>30%）:")
        for device, row in anomalies.iterrows():
            direction = "高于" if row["mean"] > overall_mean else "低于"
            lines.append(f"- **{device}**: {row['mean']:.1f}h ({direction}{abs((row['mean']-overall_mean)/overall_mean)*100:.0f}%)")

    lines.append("")
    return "\n".join(lines)


def _task_type_diagnosis(df: pd.DataFrame) -> str:
    """任务类型诊断"""
    lines = ["### 3️⃣ 任务类型诊断\n"]

    if "任务类型" not in df.columns:
        return "\n".join(lines) + "_（无可用任务类型数据）_\n\n"

    type_stats = df.groupby("任务类型")["工时"].sum().sort_values(ascending=False)
    total = type_stats.sum()
    if total == 0:
        return "\n".join(lines) + "_（无任务数据）_\n\n"

    lines.append("| 类型 | 工时 | 占比 |")
    lines.append("|------|------|------|")
    for task_type, hours in type_stats.items():
        pct = hours / total * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        lines.append(f"| {task_type} | {hours:.1f}h | {bar} {pct:.0f}% |")

    debug_pct = type_stats.get("调试", 0) / total * 100
    if debug_pct > 40:
        lines.append(f"\n⚠️ **调试占比 {debug_pct:.0f}%** 超过 40% 阈值，建议推动设备预防性维护")

    lines.append("")
    return "\n".join(lines)


def _source_analysis(df: pd.DataFrame) -> str:
    """来源分析"""
    lines = ["### 4️⃣ 来源分析\n"]

    if "来源" not in df.columns or df["来源"].nunique() <= 1:
        return "\n".join(lines) + "_（单一来源或无来源数据）_\n\n"

    src_stats = df.groupby("来源")["工时"].agg(["sum", "count"]).sort_values("sum", ascending=False)
    total = src_stats["sum"].sum()

    lines.append("| 来源 | 工时 | 占比 | 任务数 |")
    lines.append("|------|------|------|--------|")
    for src, row in src_stats.iterrows():
        pct = row["sum"] / total * 100 if total else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        lines.append(f"| {src} | {row['sum']:.1f}h | {bar} {pct:.0f}% | {int(row['count'])} |")

    dominant = src_stats.index[0]
    dominant_pct = src_stats.iloc[0]["sum"] / total * 100
    if dominant_pct > 80:
        lines.append(f"\n💡 **{dominant}** 占比 {dominant_pct:.0f}%，来源较为集中")

    lines.append("")
    return "\n".join(lines)


def _trend_analysis(df: pd.DataFrame) -> str:
    """趋势分析"""
    lines = ["### 5️⃣ 趋势分析\n"]

    daily_hours = df.groupby("日期")["工时"].sum().sort_index().reset_index()
    if len(daily_hours) < 2:
        return "\n".join(lines) + "_（数据不足）_\n\n"

    daily_hours["变化率"] = daily_hours["工时"].pct_change()

    drop_days = daily_hours[daily_hours["变化率"] < -0.3]
    if not drop_days.empty and len(drop_days) > 0:
        for _, row in drop_days.iterrows():
            date_str = row["日期"].strftime("%m-%d")
            lines.append(f"- 🔻 **{date_str}** 工时下降 {abs(row['变化率'])*100:.0f}%（{row['工时']:.1f}h）")

    if len(daily_hours) >= 7:
        first_week_avg = daily_hours.head(3)["工时"].mean()
        last_week_avg = daily_hours.tail(3)["工时"].mean()
        if first_week_avg > 0:
            trend = (last_week_avg - first_week_avg) / first_week_avg * 100
            if abs(trend) > 20:
                direction = "📈" if trend > 0 else "📉"
                lines.append(f"- {direction} 近一周趋势: {'增长' if trend > 0 else '下降'} {abs(trend):.0f}%")

    df_copy = df.copy()
    df_copy["周"] = df_copy["日期"].dt.isocalendar().week
    weekly = df_copy.groupby("周")["工时"].sum()
    if len(weekly) >= 2:
        first_w, last_w = weekly.index[0], weekly.index[-1]
        week_change = (weekly.iloc[-1] - weekly.iloc[0]) / weekly.iloc[0] * 100 if weekly.iloc[0] > 0 else 0
        lines.append(f"- **周对比**: 第{first_w}周 {weekly.iloc[0]:.1f}h → 第{last_w}周 {weekly.iloc[-1]:.1f}h ({week_change:+.0f}%)")

    if len(daily_hours) <= 1 or (drop_days.empty and len(weekly) < 2):
        lines.append("- 🟢 无明显趋势异常")

    lines.append("")
    return "\n".join(lines)


def _problem_keyword_analysis(df: pd.DataFrame) -> str:
    """问题描述关键词分析"""
    lines = ["### 6️⃣ 问题关键词\n"]

    if "问题描述" not in df.columns:
        return "\n".join(lines) + "_（无问题描述字段）_\n\n"

    problems = df[df["问题描述"].notna() & (df["问题描述"] != "")]
    if problems.empty:
        return "\n".join(lines) + "_（无问题记录）_\n\n"

    problem_text = " ".join(problems["问题描述"].astype(str).tolist()).lower()

    keywords = {
        "AGV": ["agv", "小车"],
        "通讯": ["失联", "中断", "异常", "故障"],
        "设备": ["设备", "机器", "机器"],
        "软件": ["软件", "系统", "程序"],
        "工艺": ["工艺", "参数", "配方"],
    }

    found = []
    for kw_name, kw_list in keywords.items():
        count = sum(1 for kw in kw_list if kw in problem_text)
        if count > 0:
            found.append(f"{kw_name}({count})")

    if found:
        lines.append(f"高频关键词: **{', '.join(found)}**")
    else:
        lines.append("- 暂无明显关键词模式")

    lines.append(f"- 问题记录: **{len(problems)}** 条")
    lines.append("")
    return "\n".join(lines)


def _action_recommendations(df: pd.DataFrame) -> str:
    """可执行行动建议"""
    lines = ["### 7️⃣ 行动建议\n"]

    recommendations = []

    total_hours = df["工时"].sum()
    work_days = df["日期"].nunique()
    daily_avg = total_hours / work_days if work_days else 0

    if daily_avg < 6:
        recommendations.append(("🔴高", "日均工时偏低，建议确认任务饱满度"))
    elif daily_avg > 9:
        recommendations.append(("🔴高", "日均工时偏高，关注过劳风险"))

    if "线体/设备" in df.columns:
        device_stats = df.groupby("线体/设备")["工时"].agg(["mean", "count"])
        overall_mean = df["工时"].mean()
        for device, row in device_stats.iterrows():
            if row["mean"] > overall_mean * 1.5 and row["count"] >= 3:
                recommendations.append(("🟡中", f"重点复盘 {device}，任务耗时持续偏高"))

    if "任务类型" in df.columns:
        type_hours = df.groupby("任务类型")["工时"].sum()
        total = type_hours.sum()
        debug_pct = type_hours.get("调试", 0) / total * 100 if total > 0 else 0
        if debug_pct > 40:
            recommendations.append(("🔴高", "调试占比过高，建议推动设备预防性维护"))

    weekend_hours = df[df["是否周末"] == True]["工时"].sum()
    if weekend_hours > 0:
        recommendations.append(("🟡中", f"存在 {weekend_hours:.1f}h 周末工时，建议评估加班必要性"))

    daily_hours = df.groupby("日期")["工时"].sum()
    if len(daily_hours) >= 5:
        recent_avg = daily_hours.tail(3).mean()
        earlier_avg = daily_hours.head(3).mean()
        if earlier_avg > 0 and recent_avg < earlier_avg * 0.7:
            recommendations.append(("🟡中", "近期工时持续下降，关注任务来源变化"))

    if recommendations:
        priority_order = ["🔴高", "🟡中", "🟢低"]
        recommendations.sort(key=lambda x: priority_order.index(x[0]) if x[0] in priority_order else 3)
        for priority, rec in recommendations:
            lines.append(f"- **{priority}** {rec}")
    else:
        lines.append("✅ 当前无明显异常，继续保持")

    lines.append("\n---")
    lines.append("*报告生成时间: 基于当前筛选数据*")
    return "\n".join(lines)
