import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.test_report_processor import TestReportProcessor

st.set_page_config(page_title="测试报告分析", layout="wide", page_icon="📋")

st.title("📋 自动化测试报告分析")

processor = TestReportProcessor()
df = processor.process_all()

if df.empty:
    st.info("未找到测试报告文件，请将报告放入 `report` 目录")
    st.stop()

problem_df = processor.get_problem_detail(df)
stats = processor.get_problem_stats(df)
daily_stats = processor.get_daily_stats(df)

st.subheader("📊 汇总统计")

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("报告数量", len(df))
c2.metric("总测试时间", f"{df['可测试时间'].sum():.1f}h")
c3.metric("问题总数", stats.get("total", 0))
c4.metric("已解决", stats.get("resolved", 0))
c5.metric("待处理", stats.get("pending", 0))
c6.metric("排查中", stats.get("investigating", 0))

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("**📈 每日问题趋势**")
    if not daily_stats.empty:
        fig_daily = go.Figure()
        fig_daily.add_trace(go.Bar(
            x=daily_stats["日期"],
            y=daily_stats["问题数"],
            name="问题总数",
            marker_color="#4C78A8",
            text=daily_stats["问题数"],
            textposition="outside"
        ))
        fig_daily.add_trace(go.Bar(
            x=daily_stats["日期"],
            y=daily_stats["已解决数"],
            name="已解决",
            marker_color="#54A24B",
            text=daily_stats["已解决数"],
            textposition="outside"
        ))
        fig_daily.update_layout(
            height=220,
            margin=dict(t=10, b=30, l=40, r=40),
            yaxis_title="问题数",
            barmode="group",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_daily, use_container_width=True)

with col_chart2:
    st.markdown("**📊 问题状态分布**")
    if stats.get("total", 0) > 0:
        fig_pie = go.Figure(go.Pie(
            labels=["已解决", "待处理", "排查中"],
            values=[stats.get("resolved", 0), stats.get("pending", 0), stats.get("investigating", 0)],
            hole=0.4,
            marker_colors=["#54A24B", "#E45756", "#F58518"],
            textinfo="value+percent"
        ))
        fig_pie.update_layout(height=220)
        st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

with st.expander("🔍 筛选条件", expanded=True):
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    all_dates = sorted(problem_df["日期"].unique().tolist()) if not problem_df.empty else []
    all_sources = sorted(problem_df["来源"].unique().tolist()) if not problem_df.empty else []

    with col_f1:
        selected_dates = st.multiselect("📅 日期", all_dates, all_dates)

    with col_f2:
        selected_lines = st.multiselect("🏭 线体", ["VCP1", "VCP2", "PLB"], ["VCP1", "VCP2", "PLB"])

    with col_f3:
        selected_sources = st.multiselect("🏢 来源", all_sources, all_sources)

    with col_f4:
        selected_status = st.multiselect("⚠️ 状态", ["已解决", "待处理", "排查中"], ["已解决", "待处理", "排查中"])

if not problem_df.empty:
    filtered_df = problem_df[
        (problem_df["日期"].isin(selected_dates)) &
        (problem_df["线体"].apply(lambda x: any(l in x for l in selected_lines))) &
        (problem_df["来源"].isin(selected_sources)) &
        (problem_df["状态"].isin(selected_status))
    ]
else:
    filtered_df = pd.DataFrame()

st.markdown("---")

status_icons = {"已解决": "✅", "待处理": "⚠️", "排查中": "🔍"}
status_colors = {"已解决": "#54A24B", "待处理": "#E45756", "排查中": "#F58518"}

grouped = filtered_df.groupby("日期") if not filtered_df.empty else None

if grouped:
    for date in selected_dates:
        if date not in filtered_df["日期"].values:
            continue

        date_problems = filtered_df[filtered_df["日期"] == date]
        count = len(date_problems)

        with st.expander(f"**📅 {date}** ({count} 条问题)", expanded=True):
            for _, row in date_problems.iterrows():
                status_icon = status_icons.get(row["状态"], "📋")
                status_color = status_colors.get(row["状态"], "#666")

                col1, col2, col3, col4 = st.columns([1, 1.5, 2, 5])

                with col1:
                    st.markdown(f"**{row['线体']}**")
                with col2:
                    st.markdown(f"🏢 {row['来源']}")
                with col3:
                    st.markdown(f"<span style='color:{status_color}'>{status_icon} {row['状态']}</span>", unsafe_allow_html=True)
                with col4:
                    st.markdown(row["原始描述"].replace("\n", "<br>"), unsafe_allow_html=True)

                st.markdown("")
    else:
        st.info("没有符合筛选条件的问题")

st.markdown("---")
st.subheader("📑 每日详情")

for _, row in df.iterrows():
    if row["日期"] not in selected_dates:
        continue

    with st.expander(f"**📅 {row['日期']}** - {row['线体']} (可测试时间: {row.get('可测试时间', 0)}h)", expanded=False):
        if row.get("明细时间段"):
            st.markdown(f"**明细时间段：** {row['明细时间段']}")

        st.markdown("---")

        col_left, col_right = st.columns(2)

        with col_left:
            if row.get("测试结果"):
                st.markdown("**测试结果：**")
                st.markdown(row["测试结果"].replace("\n", "<br>"), unsafe_allow_html=True)

        with col_right:
            if row.get("计划完成情况"):
                st.markdown("**计划完成情况：**")
                st.markdown(row["计划完成情况"].replace("\n", "<br>"), unsafe_allow_html=True)

        if row.get("需要协调事项") and row.get("需要协调事项") != "无":
            st.markdown(f"**需要协调事项：** {row['需要协调事项']}")

        st.markdown("---")
        st.markdown("**明日/下周计划：**")
        if row.get("明日/下周计划"):
            st.markdown(row["明日/下周计划"].replace("\n", "<br>"), unsafe_allow_html=True)
        else:
            st.text("无")

st.markdown("---")
st.subheader("📝 每日明细")

show_cols = ["日期", "线体", "可测试时间", "明细时间段"]
available_cols = [c for c in show_cols if c in df.columns]
if available_cols:
    st.dataframe(df[available_cols], use_container_width=True)