"""
AI 分析模块 - 生成工作数据分析洞察报告
"""

import pandas as pd
import numpy as np
from datetime import timedelta


def generate_insights(df: pd.DataFrame) -> str:
    """
    生成 AI 分析报告（Markdown 格式）

    包含：
    1. 工时健康度评估
    2. 设备异常检测
    3. 任务类型诊断
    4. 趋势突变检测
    5. 行动建议
    """

    if df is None or len(df) == 0:
        return "**暂无数据可供分析**"

    report = []
    report.append("## 📊 工作数据分析报告\n")

    # ========== 1. 工时健康度评估 ==========
    report.append(_health_assessment(df))

    # ========== 2. 设备异常检测 ==========
    report.append(_device_anomaly_detection(df))

    # ========== 3. 任务类型诊断 ==========
    report.append(_task_type_diagnosis(df))

    # ========== 4. 趋势突变检测 ==========
    report.append(_trend_anomaly_detection(df))

    # ========== 5. 行动建议 ==========
    report.append(_action_recommendations(df))

    return "\n".join(report)


def _health_assessment(df: pd.DataFrame) -> str:
    """工时健康度评估"""
    lines = ["### 1️⃣ 工时健康度评估\n"]

    total_hours = df["工时"].sum()
    total_tasks = len(df)
    work_days = df["日期"].nunique()
    daily_avg = total_hours / work_days if work_days else 0

    # 日均工时评估
    if daily_avg >= 7.5:
        status = "🟢 正常"
    elif daily_avg >= 6:
        status = "🟡偏低"
    else:
        status = "🔴异常"

    lines.append(f"- **日均工时**: {daily_avg:.1f}h {status}")

    # 周末工时
    weekend_hours = df[df["是否周末"] == True]["工时"].sum()
    weekend_ratio = weekend_hours / total_hours * 100 if total_hours else 0
    lines.append(f"- **周末工时**: {weekend_hours:.1f}h ({weekend_ratio:.0f}%)")

    if weekend_ratio > 20:
        lines.append("  ⚠️ 周末工作占比过高，建议关注工作生活平衡")
    elif weekend_ratio == 0:
        lines.append("  ✅ 无周末加班，工作安排合理")

    # 日均工时标准差
    daily_hours = df.groupby("日期")["工时"].sum()
    if len(daily_hours) > 1:
        std_dev = daily_hours.std()
        cv = std_dev / daily_avg * 100 if daily_avg else 0
        lines.append(f"- **日工时波动**: {cv:.0f}% (变异系数)")
        if cv > 50:
            lines.append("  ⚠️ 日工时波动较大，建议关注任务分配均匀性")

    return "\n".join(lines)


def _device_anomaly_detection(df: pd.DataFrame, threshold: float = 0.30) -> str:
    """设备工时异常检测"""
    lines = ["### 2️⃣ 设备异常检测\n"]

    if "线体/设备" not in df.columns:
        return "\n".join(lines) + "\n\n_（无可用设备数据）_\n"

    device_stats = df.groupby("线体/设备")["工时"].agg(["sum", "mean", "count"])
    overall_mean = df["工时"].mean()

    anomalies = []
    normal = []

    for device, row in device_stats.iterrows():
        deviation = (row["mean"] - overall_mean) / overall_mean if overall_mean else 0
        if abs(deviation) > threshold:
            anomalies.append((device, row["mean"], deviation, row["count"]))
        else:
            normal.append((device, row["mean"], deviation, row["count"]))

    if anomalies:
        lines.append("**🔴 异常设备（偏离均值 >30%）:**")
        for device, mean, dev, count in anomalies:
            direction = "高于" if dev > 0 else "低于"
            lines.append(f"- **{device}**: {mean:.1f}h/任务 ({direction}{abs(dev)*100:.0f}%, {int(count)}个任务)")
    else:
        lines.append("**🟢 所有设备工时正常**")

    if normal:
        lines.append("\n**🔵 正常设备:**")
        for device, mean, dev, count in sorted(normal, key=lambda x: abs(x[2]), reverse=True)[:5]:
            lines.append(f"- {device}: {mean:.1f}h/任务 ({dev*100:+.0f}%)")

    return "\n".join(lines)


def _task_type_diagnosis(df: pd.DataFrame, warning_threshold: float = 0.40) -> str:
    """任务类型合理性判断"""
    lines = ["### 3️⃣ 任务类型诊断\n"]

    if "任务类型" not in df.columns:
        return "\n".join(lines) + "\n\n_（无可用任务类型数据）_\n"

    type_stats = df.groupby("任务类型")["工时"].sum()
    total = type_stats.sum()
    type_pct = type_stats / total * 100 if total else 0

    for task_type, hours in type_stats.sort_values(ascending=False).items():
        pct = type_pct[task_type]
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        warning = " ⚠️" if task_type in ["调试", "分析"] and pct > warning_threshold * 100 else ""
        lines.append(f"- **{task_type}**: {hours:.1f}h ({pct:.0f}%) {bar}{warning}")

    # 调试占比过高预警
    debug_pct = type_pct.get("调试", 0)
    if debug_pct > warning_threshold * 100:
        lines.append(f"\n⚠️ **警告**: 调试占比 {debug_pct:.0f}% 超过 {warning_threshold*100:.0f}% 阈值")
        lines.append("建议: 检查是否存在重复问题或设备质量问题")

    return "\n".join(lines)


def _trend_anomaly_detection(df: pd.DataFrame, drop_threshold: float = 0.50) -> str:
    """趋势突变检测"""
    lines = ["### 4️⃣ 趋势突变检测\n"]

    daily_hours = df.groupby("日期")["工时"].sum().sort_index()

    if len(daily_hours) < 2:
        lines.append("_数据不足，无法进行趋势分析_")
        return "\n".join(lines)

    # 计算日均变化
    daily_hours = daily_hours.reset_index()
    daily_hours["变化率"] = daily_hours["工时"].pct_change()

    anomalies = []
    for i, row in daily_hours.iterrows():
        if i == 0:
            continue
        change = row["变化率"]
        if change < -drop_threshold:
            date_str = row["日期"].strftime("%Y-%m-%d")
            anomalies.append((date_str, change, daily_hours.iloc[i-1]["工时"], row["工时"]))

    if anomalies:
        lines.append("**🔴 工时骤降（单日下降 >50%）:**")
        for date_str, change, before, after in anomalies:
            lines.append(f"- **{date_str}**: {before:.1f}h → {after:.1f}h ({change*100:.0f}%)")
    else:
        lines.append("**🟢 无明显趋势异常**")

    # 周趋势
    df_copy = df.copy()
    df_copy["周"] = df_copy["日期"].dt.isocalendar().week
    weekly_hours = df_copy.groupby("周")["工时"].sum()

    if len(weekly_hours) >= 2:
        first_week = weekly_hours.iloc[0]
        last_week = weekly_hours.iloc[-1]
        week_change = (last_week - first_week) / first_week if first_week else 0
        direction = "📈 上升" if week_change > 0 else "📉 下降"
        lines.append(f"\n**周趋势**: {direction} {abs(week_change)*100:.0f}% (第{weekly_hours.index[0]}周 → 第{weekly_hours.index[-1]}周)")

    return "\n".join(lines)


def _action_recommendations(df: pd.DataFrame) -> str:
    """具体可执行的行动建议"""
    lines = ["### 5️⃣ 行动建议\n"]

    recommendations = []

    # 基于工时健康度
    total_hours = df["工时"].sum()
    work_days = df["日期"].nunique()
    daily_avg = total_hours / work_days if work_days else 0

    if daily_avg < 6:
        recommendations.append(("🔴高", "日均工时偏低，建议与主管确认任务饱满度"))
    elif daily_avg > 9:
        recommendations.append(("🔴高", "日均工时偏高，关注过劳风险"))

    # 基于设备异常
    if "线体/设备" in df.columns:
        device_stats = df.groupby("线体/设备")["工时"].agg(["mean", "count"])
        overall_mean = df["工时"].mean()
        for device, row in device_stats.iterrows():
            if row["mean"] > overall_mean * 1.5 and row["count"] >= 3:
                recommendations.append(("🟡中", f"重点复盘 {device}，任务耗时持续偏高"))

    # 基于调试占比
    if "任务类型" in df.columns:
        type_hours = df.groupby("任务类型")["工时"].sum()
        total = type_hours.sum()
        debug_pct = type_hours.get("调试", 0) / total * 100 if total else 0
        if debug_pct > 40:
            recommendations.append(("🔴高", "调试占比过高，建议推动设备预防性维护"))

    # 基于周末工时
    weekend_hours = df[df["是否周末"] == True]["工时"].sum()
    if weekend_hours > 0:
        recommendations.append(("🟡中", f"存在 {weekend_hours:.1f}h 周末工时，建议评估加班必要性"))

    # 基于趋势突变
    daily_hours = df.groupby("日期")["工时"].sum()
    if len(daily_hours) >= 2:
        recent_avg = daily_hours.tail(3).mean()
        earlier_avg = daily_hours.head(3).mean()
        if recent_avg < earlier_avg * 0.7:
            recommendations.append(("🟡中", "近期工时呈下降趋势，关注任务来源变化"))

    if recommendations:
        # 按优先级排序
        priority_order = ["🔴高", "🟡中", "🟢低"]
        recommendations.sort(key=lambda x: priority_order.index(x[0]) if x[0] in priority_order else 3)

        for priority, rec in recommendations:
            lines.append(f"- **{priority}** {rec}")
    else:
        lines.append("✅ 当前无明显异常继续保持")

    lines.append("\n---\n*报告生成时间: 基于当前筛选数据*")
    return "\n".join(lines)
