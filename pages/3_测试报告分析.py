import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from html import escape
from pathlib import Path
from utils.test_report_processor import TestReportProcessor
from utils.report_form import render_report_form
from utils.styles import (
    inject_global_css, render_kpi_card, render_section_title,
    render_empty_state, render_sidebar_nav, render_problem_card,
    PRIMARY, SUCCESS, WARNING, DANGER, INFO,
    STATUS_COLORS, STATUS_ICONS, LINE_COLORS,
)

st.set_page_config(page_title="测试报告分析", layout="wide", page_icon="📋")
inject_global_css()


@st.cache_resource
def get_test_report_processor():
    return TestReportProcessor()


PROBLEM_MODULES = [
    "投收板机", "自动化物流（海康）", "主线设备", "软件集成（SIE）",
    "生产/工艺", "生产", "工艺", "维护", "IT", "其他",
]


def normalize_problem_summary(summary):
    if summary is None or pd.isna(summary):
        return ""
    text = str(summary)
    for module in PROBLEM_MODULES:
        text = text.replace(f" · {module}：", f"\n{module}：")
        text = text.replace(f" · {module}:", f"\n{module}:")
    for marker in ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨"]:
        text = text.replace(f" · {marker}", f"\n{marker}")
    return text


def split_problem_summary(summary):
    modules = []
    current = None

    def save_current():
        if current:
            modules.append(current)

    for raw_line in normalize_problem_summary(summary).splitlines():
        line = raw_line.strip()
        if not line:
            continue

        colon_index = next((idx for idx in [line.find("："), line.find(":")] if idx >= 0), -1)
        is_numbered = line.startswith(("①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨"))

        if colon_index > 0 and not is_numbered:
            save_current()
            module_name = line[:colon_index].strip()
            content = line[colon_index + 1:].strip()
            current = {"module": module_name, "items": []}
            if content and content != "无":
                current["items"].append(content)
        elif current:
            current["items"].append(line)
        else:
            current = {"module": "其他", "items": [line]}

    save_current()
    return modules


def split_report_items(value):
    if not has_text(value):
        return []
    items = []
    for raw_line in str(value).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "无":
            continue
        items.append(line)
    return items


def has_text(value):
    if value is None or pd.isna(value):
        return False
    return bool(str(value).strip())


def detail_block_html(title, value, wide=False):
    items = split_report_items(value)
    block_class = "report-detail-block wide" if wide else "report-detail-block"
    if items:
        items_html = "".join(f'<div class="report-detail-item">{escape(item)}</div>' for item in items)
    else:
        items_html = '<div class="report-detail-empty">无</div>'
    return (
        f'<div class="{block_class}">'
        f'<div class="report-detail-title">{escape(title)}</div>'
        f'<div class="report-detail-list">{items_html}</div>'
        '</div>'
    )


def render_report_problem_summary(summary):
    if not has_text(summary):
        return
    modules = split_problem_summary(summary)
    if not modules:
        return

    rows_html = []
    for item in modules:
        module_name = escape(item["module"])
        items = [escape(text) for text in item["items"] if str(text).strip()]
        has_issue = bool(items)
        row_class = "has-issue" if has_issue else "is-empty"
        status_text = f"{len(items)} 条" if has_issue else "无"
        if has_issue:
            items_html = "".join(f'<div class="report-summary-item">{text}</div>' for text in items)
        else:
            items_html = '<div class="report-summary-empty">无</div>'
        rows_html.append(
            f'<div class="report-summary-row {row_class}">'
            '<div class="report-summary-head">'
            f'<span class="report-summary-module">{module_name}</span>'
            f'<span class="report-summary-status">{status_text}</span>'
            '</div>'
            f'<div class="report-summary-items">{items_html}</div>'
            '</div>'
        )

    st.markdown(f'<div class="report-summary">{"".join(rows_html)}</div>', unsafe_allow_html=True)


def render_report_detail(row):
    meta_items = [
        ("⏱️", row.get("测试总时长")),
        ("📦", row.get("工单")),
    ]
    chips = []
    for icon, value in meta_items:
        if has_text(value):
            safe_value = escape(str(value).replace(chr(10), " · "))
            chips.append(f'<span class="report-detail-chip">{icon}<span>{safe_value}</span></span>')

    if chips:
        st.markdown(f'<div class="report-detail-meta">{"".join(chips)}</div>', unsafe_allow_html=True)

    if has_text(row.get("问题汇总")):
        st.markdown("**⚠️ 问题汇总**")
        render_report_problem_summary(row["问题汇总"])

    blocks_html = [
        detail_block_html("今日计划", row.get("今日计划")),
        detail_block_html("实际场景", row.get("实际场景")),
        detail_block_html("流程", row.get("流程"), wide=True),
        detail_block_html("测试结果", row.get("测试结果")),
        detail_block_html("计划完成情况", row.get("计划完成情况")),
        detail_block_html("待办项", row.get("待办项")),
        detail_block_html("明日计划", row.get("明日计划"), wide=True),
    ]
    st.markdown(f'<div class="report-detail-grid">{"".join(blocks_html)}</div>', unsafe_allow_html=True)


def render_analysis_page():
    st.title("📋 自动化测试报告分析")

    processor = get_test_report_processor()
    df = processor.process_all()

    if df.empty:
        render_empty_state("📭", "暂无测试报告", "点击下方按钮创建第一份报告")
        if st.button("➕ 创建报告", type="primary", use_container_width=True):
            st.switch_page("pages/4_新建报告.py")
        st.stop()

    problem_df = processor.get_problem_detail(df)
    stats = processor.get_problem_stats(df)
    daily_stats = processor.get_daily_stats(df)

    hours_series = df['测试总时长'].str.extract(r'(\d+\.?\d*)')[0].astype(float) if '测试总时长' in df.columns else pd.Series([0])
    total_hours = hours_series.sum()

    # =====================
    # 顶部操作栏
    # =====================
    c_top1, c_top2 = st.columns([4, 1])
    with c_top2:
        if st.button("➕ 新建报告", type="primary", use_container_width=True):
            st.switch_page("pages/4_新建报告.py")

    # =====================
    # 侧边栏筛选
    # =====================
    with st.sidebar:
        render_sidebar_nav("测试报告")
        st.divider()
        st.markdown('<p class="sidebar-title">🔍 筛选条件</p>', unsafe_allow_html=True)

        with st.expander("📅 日期范围", expanded=True):
            all_dates = sorted(df["日期"].unique().tolist())
            selected_dates = st.multiselect("日期", all_dates, default=all_dates, key="report_date_filter")

        with st.expander("🏢 线体", expanded=False):
            all_lines = df["线体"].unique().tolist()
            selected_lines = st.multiselect("线体", all_lines, default=all_lines, key="report_line_filter")

        with st.expander("📊 问题状态", expanded=False):
            all_status = ["已解决", "待处理", "排查中"]
            selected_status = st.multiselect("状态", all_status, default=all_status, key="report_status_filter")

        st.divider()
        if st.button("🔄 重置筛选", use_container_width=True):
            st.rerun()

    # =====================
    # KPI
    # =====================
    resolve_rate = stats.get("resolved", 0) / stats["total"] * 100 if stats.get("total", 0) > 0 else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: render_kpi_card(f"{total_hours:.1f}h", "总测试时长", "⏱️", INFO)
    with k2: render_kpi_card(f"{stats.get('total', 0)}", "问题总数", "📊", PRIMARY)
    with k3: render_kpi_card(f"{stats.get('resolved', 0)}", "已解决", "✅", SUCCESS)
    with k4: render_kpi_card(f"{stats.get('pending', 0)}", "待处理", "⚠️", DANGER)
    with k5:
        color = SUCCESS if resolve_rate >= 60 else WARNING if resolve_rate >= 30 else DANGER
        render_kpi_card(f"{resolve_rate:.0f}%", "解决率", "🎯", color)

    # =====================
    # 统计图表
    # =====================
    render_section_title("📈", "统计分析")

    tab_chart1, tab_chart2, tab_chart3 = st.tabs(["问题趋势", "状态分布", "线体对比"])

    with tab_chart1:
        if not daily_stats.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=daily_stats["日期"], y=daily_stats["问题数"], name="问题总数", marker_color=PRIMARY))
            fig.add_trace(go.Bar(x=daily_stats["日期"], y=daily_stats["已解决数"], name="已解决", marker_color=SUCCESS))
            if len(daily_stats) > 1:
                fig.add_trace(go.Scatter(
                    x=daily_stats["日期"],
                    y=daily_stats["已解决数"] / daily_stats["问题数"] * 100,
                    name="解决率", yaxis="y2", mode="lines+markers",
                    line=dict(color=WARNING, width=2, dash="dot"),
                    marker=dict(size=6), hovertemplate="%{x}<br>解决率: %{y:.0f}%<extra></extra>"
                ))
            fig.update_layout(
                height=320, barmode="group",
                margin=dict(t=20, b=20, l=40, r=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis_title="日期", yaxis_title="问题数量",
                yaxis2=dict(title="解决率 (%)", overlaying="y", side="right", range=[0, 120], showgrid=False),
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab_chart2:
        if stats.get("total", 0) > 0:
            fig2 = go.Figure(go.Pie(
                labels=["已解决", "待处理", "排查中"],
                values=[stats.get("resolved", 0), stats.get("pending", 0), stats.get("investigating", 0)],
                hole=0.55, marker_colors=[SUCCESS, DANGER, WARNING],
                textinfo="value+percent",
                hovertemplate="%{label}<br>数量: %{value}<br>占比: %{percent}<extra></extra>"
            ))
            fig2.update_layout(
                height=320, margin=dict(t=20, b=20, l=20, r=20),
                annotations=[dict(text=f"{stats['total']}<br>问题", x=0.5, y=0.5, font_size=16, showarrow=False)]
            )
            st.plotly_chart(fig2, use_container_width=True)

    with tab_chart3:
        if stats.get("by_line"):
            line_names = list(stats["by_line"].keys())
            fig3 = go.Figure()
            for status_name, color in [("已解决", SUCCESS), ("待处理", DANGER), ("排查中", WARNING)]:
                fig3.add_trace(go.Bar(
                    x=line_names,
                    y=[stats["by_line"][l].get(status_name if status_name != "排查中" else "investigating",
                        stats["by_line"][l].get("investigating", 0) if status_name == "排查中" else
                        stats["by_line"][l].get("resolved", 0) if status_name == "已解决" else
                        stats["by_line"][l].get("pending", 0)) for l in line_names],
                    name=status_name, marker_color=color
                ))
            fig3.update_layout(
                height=320, barmode="stack",
                margin=dict(t=20, b=20, l=40, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis_title="线体", yaxis_title="问题数量",
                hovermode="x unified"
            )
            st.plotly_chart(fig3, use_container_width=True)

    # =====================
    # 问题详情
    # =====================
    render_section_title("📝", "问题详情")

    if problem_df.empty:
        render_empty_state("✅", "暂无问题记录", "所有测试报告均无问题描述")
    else:
        filtered = problem_df[
            (problem_df["日期"].isin(selected_dates)) &
            (problem_df["线体"].isin(selected_lines)) &
            (problem_df["状态"].isin(selected_status))
        ]

        tab_dept, tab_line = st.tabs(["按部门", "按线体"])

        with tab_dept:
            if filtered.empty:
                render_empty_state("🔍", "无匹配问题", "请调整筛选条件")
            else:
                st.markdown(f"**共 {len(filtered)} 条问题**")
                by_dept = filtered.groupby("来源")
                dept_order = ["投收板机", "自动化物流（海康）", "主线设备", "软件集成（SIE）",
                            "生产/工艺", "生产", "工艺", "维护", "IT", "其他"]
                for dept in dept_order:
                    if dept not in by_dept.groups:
                        continue
                    dept_problems = by_dept.get_group(dept)
                    dept_count = len(dept_problems)
                    with st.expander(f"📦 {dept} · {dept_count}条", expanded=False):
                        by_date = dept_problems.groupby("日期")
                        for date in sorted(dept_problems["日期"].unique().tolist()):
                            if date not in by_date.groups:
                                continue
                            date_problems = by_date.get_group(date)
                            st.markdown(f"**📅 {date}** · {len(date_problems)}条")
                            for _, prob in date_problems.iterrows():
                                render_problem_card(prob["线体"], prob["状态"], prob["原始描述"])

        with tab_line:
            if filtered.empty:
                render_empty_state("🔍", "无匹配问题", "请调整筛选条件")
            else:
                by_line = filtered.groupby("线体")
                for line_name in sorted(filtered["线体"].unique().tolist()):
                    if line_name not in by_line.groups:
                        continue
                    line_problems = by_line.get_group(line_name)
                    line_count = len(line_problems)
                    with st.expander(f"🔧 {line_name} · {line_count}条", expanded=False):
                        for _, prob in line_problems.iterrows():
                            render_problem_card(prob["线体"], prob["状态"], prob["原始描述"])

    # =====================
    # 报告详情
    # =====================
    render_section_title("📄", "报告详情")

    report_search = st.text_input("🔍 搜索报告", placeholder="按日期、线体搜索...", key="report_search")
    df_search = df.copy()
    if report_search:
        mask = df_search.astype(str).apply(lambda x: x.str.contains(report_search, case=False, na=False)).any(axis=1)
        df_search = df_search[mask]

    for _, row in df_search.sort_values("日期", ascending=False).iterrows():
        c1, c2 = st.columns([5, 1])
        with c1:
            title_parts = [f"📅 {row['日期']}", f"{row.get('线体', '')}"]
            with st.expander(" · ".join(p for p in title_parts if p), expanded=False):
                render_report_detail(row)
        with c2:
            st.write("")
            if st.button("✏️ 编辑", key=f"e_{row['日期']}_{row.get('线体','')}", use_container_width=True):
                st.session_state.edit_mode = True
                st.session_state.edit_report_data = row.to_dict()
                st.session_state.edit_original_filename = row.get("文件名", "")
                st.rerun()

    st.caption("📋 自动化测试报告分析系统 v2.2")


if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

if st.session_state.get("edit_mode"):
    result = render_report_form(
        st.session_state.get("edit_report_data"),
        mode="edit",
        original_filename=st.session_state.get("edit_original_filename")
    )
    if result == "back":
        st.session_state.edit_mode = False
        st.rerun()
    elif result:
        st.session_state.edit_mode = False
        st.rerun()
else:
    render_analysis_page()
