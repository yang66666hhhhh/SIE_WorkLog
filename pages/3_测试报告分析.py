import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys
from utils.test_report_processor import TestReportProcessor
from utils.report_form import render_report_form

st.set_page_config(page_title="测试报告分析", layout="wide", page_icon="📋")

# 缓存处理器实例，避免重复创建
@st.cache_resource
def get_test_report_processor():
    return TestReportProcessor()

# 颜色和样式配置
STATUS_COLORS = {
    "已解决": "#54A24B", "待处理": "#E45756", "排查中": "#F58518",
    "完成": "#54A24B", "未完成": "#E45756", "进行中": "#F58518"
}
LINE_COLORS = {
    "VCP1": "#667eea", "VCP2": "#f093fb", "PLB": "#4facfe", "其他": "#666"
}
DEPT_COLORS = {
    "投收板机": "#4C78A8", "自动化物流（海康）": "#F58518", 
    "主线设备": "#E45756", "软件集成（SIE）": "#72B7B2",
    "生产/工艺": "#54A24B", "生产": "#9D7559", "工艺": "#B279A2",
    "维护": "#8C6BB1", "IT": "#6A3D9A", "其他": "#666"
}

def render_kpi_card(label, value, icon, color):
    """优化后的 KPI 卡片"""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {color} 0%, {color}cc 100%);
                padding: 20px 16px; border-radius: 12px; text-align: center; color: white;
                box-shadow: 0 4px 12px {color}30; margin-bottom: 16px;">
        <div style="font-size: 2.2rem; font-weight: 700; line-height: 1.3;">{value}</div>
        <div style="font-size: 0.9rem; opacity: 0.9; margin-top: 8px; display: flex; align-items: center; justify-content: center; gap: 6px;">
            <span style="font-size: 1.2rem;">{icon}</span>
            <span>{label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_problem_card(线体, 状态, 描述):
    """优化后的问题卡片"""
    sc = STATUS_COLORS.get(状态, "#666")
    lc = LINE_COLORS.get(线体, "#666")
    si = status_icons.get(状态, "📋")
    
    st.markdown(f"""
    <div style="border: 1px solid #eee; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px; background: #f9f9f9; transition: all 0.2s;">
        <div style="display: flex; align-items: center; gap: 14px;">
            <span style="background: {lc}20; color: {lc}; padding: 4px 10px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; min-width: 60px; text-align: center;">{线体}</span>
            <span style="background: {sc}15; color: {sc}; padding: 4px 10px; border-radius: 6px; font-size: 0.85rem; min-width: 60px; text-align: center;">{si} {状态}</span>
            <span style="color: #444; font-size: 0.9rem; flex: 1; line-height: 1.4;">{描述.replace(chr(10), ' · ')}</span>
        </div>
    </div>
    """, unsafe_html=True)

def render_analysis_page():
    st.title("📋 自动化测试报告分析")
    
    processor = get_test_report_processor()
    df = processor.process_all()
    
    if df.empty:
        st.info("📭 暂无测试报告，请先创建")
        if st.button("➕ 创建报告", type="primary"):
            st.switch_page("pages/4_新建报告.py")
        st.stop()
    
    # 获取统计数据
    problem_df = processor.get_problem_detail(df)
    stats = processor.get_problem_stats(df)
    daily_stats = processor.get_daily_stats(df)
    
    # 计算总测试时长
    hours_series = df['测试总时长'].str.extract(r'(\d+\.?\d*)')[0].astype(float) if '测试总时长' in df.columns else pd.Series([0])
    total_hours = hours_series.sum()
    
    # =====================
    # KPI 仪表板
    # =====================
    st.markdown("### 📊 关键指标")
    cols = st.columns(5)
    with cols[0]: render_kpi_card("总测试时长", f"{total_hours:.1f}h", "⏱️", "#667eea")
    with cols[1]: render_kpi_card("问题总数", stats.get("total", 0), "📊", "#4C78A8")
    with cols[2]: render_kpi_card("已解决", stats.get("resolved", 0), "✅", "#54A24B")
    with cols[3]: render_kpi_card("待处理", stats.get("pending", 0), "⚠️", "#E45718")
    with cols[4]: render_kpi_card("排查中", stats.get("investigating", 0), "🔍", "#F58518")
    
    # =====================
    # 筛选器
    # =====================
    st.markdown("---")
    st.markdown("### 🔍 筛选条件")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        all_dates = sorted(df["日期"].unique().tolist())
        selected_dates = st.multiselect("日期范围", all_dates, default=all_dates, label_visibility="collapsed")
    with col2:
        all_lines = df["线体"].unique().tolist()
        selected_lines = st.multiselect("线体", all_lines, default=all_lines, label_visibility="collapsed")
    with col3:
        all_status = ["已解决", "待处理", "排查中"]
        selected_status = st.multiselect("问题状态", all_status, default=all_status, label_visibility="collapsed")
    with col4:
        st.write("")
        if st.button("🔄 重置筛选", use_container_width=True):
            st.rerun()
    
    # =====================
    # 统计图表
    # =====================
    st.markdown("---")
    st.markdown("### 📈 统计分析")
    
    tab1, tab2 = st.tabs(["趋势分析", "状态分布"])
    
    with tab1:
        if not daily_stats.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=daily_stats["日期"], y=daily_stats["问题数"], name="问题总数", marker_color="#4C78A8"))
            fig.add_trace(go.Bar(x=daily_stats["日期"], y=daily_stats["已解决数"], name="已解决", marker_color="#54A24B"))
            fig.update_layout(
                height=320, barmode="group",
                margin=dict(t=20, b=20, l=40, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis_title="日期", yaxis_title="问题数量",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        if stats.get("total", 0) > 0:
            fig2 = go.Figure(go.Pie(
                labels=["已解决", "待处理", "排查中"],
                values=[stats.get("resolved", 0), stats.get("pending", 0), stats.get("investigating", 0)],
                hole=0.5, marker_colors=["#54A24B", "#E45756", "#F58518"],
                textinfo="value+percent+label",
                hovertemplate="%{label}<br>数量: %{value}<br>占比: %{percent}<extra></extra>"
            ))
            fig2.update_layout(
                height=320, margin=dict(t=20, b=20, l=20, r=20),
                annotations=[dict(text=f"{stats['total']}个问题", x=0.5, y=0.5, font_size=16, showarrow=False)]
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    # =====================
    # 各线体问题统计
    # =====================
    if stats.get("by_line"):
        st.markdown("---")
        st.markdown("### 🏢 各线体问题统计")
        
        line_data = []
        for line, data in stats["by_line"].items():
            line_data.append({
                "线体": line,
                "问题总数": data["total"],
                "已解决": data["resolved"],
                "待处理": data["pending"],
                "排查中": data["investigating"]
            })
        
        st.dataframe(
            pd.DataFrame(line_data),
            use_container_width=True,
            hide_index=True,
            column_config={
                "线体": st.column_config.TextColumn("线体"),
                "问题总数": st.column_config.NumberColumn("总数", format="%d"),
                "已解决": st.column_config.NumberColumn("已解决", format="%d"),
                "待处理": st.column_config.NumberColumn("待处理", format="%d"),
                "排查中": st.column_config.NumberColumn("排查中", format="%d")
            }
        )
    
    # =====================
    # 问题详情
    # =====================
    st.markdown("---")
    st.markdown("### 📝 问题详情")
    
    if problem_df.empty:
        st.info("暂无问题记录")
    else:
        # 应用筛选
        filtered = problem_df[
            (problem_df["日期"].isin(selected_dates)) &
            (problem_df["线体"].isin(selected_lines)) &
            (problem_df["状态"].isin(selected_status))
        ]
        
        st.markdown(f"**共 {len(filtered)} 条问题**")
        
        if not filtered.empty:
            # 按部门分组显示
            by_dept = filtered.groupby("来源")
            dept_order = ["投收板机", "自动化物流（海康）", "主线设备", "软件集成（SIE）", 
                        "生产/工艺", "生产", "工艺", "维护", "IT", "其他"]
            
            for dept in dept_order:
                if dept not in by_dept.groups:
                    continue
                
                dept_problems = by_dept.get_group(dept)
                dept_count = len(dept_problems)
                
                with st.expander(f"📦 {dept} · {dept_count}条问题", expanded=False):
                    # 按日期分组显示
                    by_date = dept_problems.groupby("日期")
                    all_dates_in_dept = sorted(dept_problems["日期"].unique().tolist())
                    
                    for date in all_dates_in_dept:
                        if date not in by_date.groups:
                            continue
                        
                        date_problems = by_date.get_group(date)
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**📅 {date}** · {len(date_problems)}条")
                        
                        for _, prob in date_problems.iterrows():
                            render_problem_card(prob["线体"], prob["状态"], prob["原始描述"])
        
        else:
            st.info("无符合条件的问题")
    
    # =====================
    # 报告详情
    # =====================
    st.markdown("---")
    st.markdown("### 📄 报告详情")
    
    for _, row in df.iterrows():
        c1, c2 = st.columns([5, 1])
        with c1:
            with st.expander(f"📅 {row['日期']} · {row.get('线体', '')}", expanded=False):
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
    
    st.caption("📋 自动化测试报告分析系统 v2.2")

# 初始化状态
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# 处理编辑模式
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