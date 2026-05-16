import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.test_report_processor import TestReportProcessor
from utils.report_form import render_report_form

st.set_page_config(page_title="测试报告分析", layout="wide", page_icon="📋")

status_icons = {"已解决": "✅", "待处理": "⚠️", "排查中": "🔍"}
status_colors = {"已解决": "#54A24B", "待处理": "#E45756", "排查中": "#F58518"}
line_colors = {"VCP1": "#667eea", "VCP2": "#f093fb", "PLB": "#4facfe", "其他": "#666"}


def render_kpi_card(label, value, icon, color):
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {color} 0%, {color}cc 100%);
                padding: 20px 12px; border-radius: 12px; text-align: center; color: white;
                box-shadow: 0 2px 10px {color}40;">
        <div style="font-size: 2rem; font-weight: 700; line-height: 1.2;">{value}</div>
        <div style="font-size: 0.85rem; opacity: 0.9; margin-top: 6px;">{icon} {label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_problem_card(线体, 状态, 描述):
    sc = status_colors.get(状态, "#666")
    lc = line_colors.get(线体, "#666")
    si = status_icons.get(状态, "📋")
    st.markdown(f"""
    <div style="border: 1px solid #eee; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; background: #fafafa;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="background: {lc}20; color: {lc}; padding: 3px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">{线体}</span>
            <span style="background: {sc}15; color: {sc}; padding: 3px 10px; border-radius: 6px; font-size: 0.8rem;">{si} {状态}</span>
            <span style="color: #555; font-size: 0.85rem; flex: 1;">{描述.replace(chr(10), ' · ')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_analysis_page():
    st.title("📋 自动化测试报告分析")

    processor = TestReportProcessor()
    df = processor.process_all()

    if df.empty:
        st.info("📭 暂无测试报告，请先创建")
        if st.button("➕ 创建报告", type="primary"):
            st.switch_page("pages/4_新建报告.py")
        st.stop()

    problem_df = processor.get_problem_detail(df)
    stats = processor.get_problem_stats(df)
    daily_stats = processor.get_daily_stats(df)

    hours_series = df['测试总时长'].str.extract(r'(\d+\.?\d*)')[0].astype(float) if '测试总时长' in df.columns else pd.Series([0])
    total_hours = hours_series.sum()

    cols = st.columns(5)
    with cols[0]: render_kpi_card("总测试时长", f"{total_hours:.1f}h", "⏱️", "#667eea")
    with cols[1]: render_kpi_card("问题总数", stats.get("total", 0), "📊", "#4C78A8")
    with cols[2]: render_kpi_card("已解决", stats.get("resolved", 0), "✅", "#54A24B")
    with cols[3]: render_kpi_card("待处理", stats.get("pending", 0), "⚠️", "#E45756")
    with cols[4]: render_kpi_card("排查中", stats.get("investigating", 0), "🔍", "#F58518")

    tab1, tab2, tab3 = st.tabs(["📈 统计", "📝 问题", "📄 详情"])

    with tab1:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("**每日问题趋势**")
            if not daily_stats.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(x=daily_stats["日期"], y=daily_stats["问题数"], name="问题总数", marker_color="#4C78A8"))
                fig.add_trace(go.Bar(x=daily_stats["日期"], y=daily_stats["已解决数"], name="已解决", marker_color="#54A24B"))
                fig.update_layout(height=280, barmode="group", margin=dict(t=10, b=10, l=40, r=10), legend=dict(orientation="h", y=1.05))
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("**状态分布**")
            if stats.get("total", 0) > 0:
                fig2 = go.Figure(go.Pie(labels=["已解决", "待处理", "排查中"],
                    values=[stats.get("resolved", 0), stats.get("pending", 0), stats.get("investigating", 0)],
                    hole=0.5, marker_colors=["#54A24B", "#E45756", "#F58518"], textinfo="value+percent"))
                fig2.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig2, use_container_width=True)

        if stats.get("by_line"):
            st.markdown("**各线体问题统计**")
            line_data = [{"线体": k, "总数": v["total"], "已解决": v["resolved"], "待处理": v["pending"], "排查中": v["investigating"]}
                        for k, v in stats["by_line"].items()]
            st.dataframe(pd.DataFrame(line_data), use_container_width=True, hide_index=True)

    with tab2:
        if problem_df.empty:
            st.info("暂无问题记录")
        else:
            all_dates = sorted(problem_df["日期"].unique().tolist())
            all_status = ["已解决", "待处理", "排查中"]

            col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])
            with col_f1:
                selected_dates = st.multiselect("日期范围", all_dates, all_dates, label_visibility="collapsed")
            with col_f2:
                selected_status = st.multiselect("问题状态", all_status, all_status, label_visibility="collapsed")
            with col_f3:
                st.write("")
                csv = problem_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("📥 导出", csv, f"问题列表_{pd.Timestamp.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)
            with col_f4:
                st.write("")
                if st.button("🔄 重置", use_container_width=True):
                    st.rerun()

            filtered = problem_df[
                (problem_df["日期"].isin(selected_dates)) &
                (problem_df["状态"].isin(selected_status))
            ]

            st.markdown("---")
            st.markdown(f"**共 {len(filtered)} 条问题**")

            if not filtered.empty:
                by_dept = filtered.groupby("来源")
                dept_order = ["投收板机", "自动化物流（海康）", "主线设备", "软件集成（SIE）", "生产/工艺", "生产", "工艺", "维护", "IT", "其他"]

                for dept in dept_order:
                    if dept not in by_dept.groups:
                        continue
                    dept_problems = by_dept.get_group(dept)
                    dept_count = len(dept_problems)

                    with st.expander(f"**📦 {dept}** · {dept_count}条问题", expanded=True):
                        by_date = dept_problems.groupby("日期")
                        for date in selected_dates:
                            if date not in by_date.groups:
                                continue
                            date_problems = by_date.get_group(date)
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**📅 {date}** · {len(date_problems)}条")
                            for _, prob in date_problems.iterrows():
                                render_problem_card(prob["线体"], prob["状态"], prob["原始描述"])
            else:
                st.info("无符合条件的问题")

    with tab3:
        for _, row in df.iterrows():
            c1, c2 = st.columns([5, 1])
            with c1:
                with st.expander(f"📅 {row['日期']} · {row.get('线体', '')}"):
                    cl, cr = st.columns(2)
                    with cl:
                        if row.get("测试总时长"): st.caption(f"⏱️ {row['测试总时长']}")
                        if row.get("工单"): st.caption(f"📦 {row['工单']}")
                    with cr:
                        if row.get("计划完成情况"): st.caption(f"✅ {row['计划完成情况']}")
                    if row.get("问题汇总"): st.caption(f"⚠️ {row['问题汇总'].replace(chr(10), ' · ')}")
            with c2:
                st.write("")
                if st.button("✏️", key=f"e_{row['日期']}"):
                    st.session_state.edit_mode = True
                    st.session_state.edit_report_data = row.to_dict()
                    st.session_state.edit_original_filename = row.get("文件名", "")
                    st.rerun()

        st.caption("📋 自动化测试报告分析系统")

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

if st.session_state.get("edit_mode"):
    result = render_report_form(st.session_state.get("edit_report_data"), mode="edit", original_filename=st.session_state.get("edit_original_filename"))
    if result == "back":
        st.session_state.edit_mode = False
        st.rerun()
    elif result:
        st.session_state.edit_mode = False
        st.rerun()
else:
    render_analysis_page()