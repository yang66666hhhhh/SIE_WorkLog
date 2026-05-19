import streamlit as st
import pandas as pd
from pathlib import Path
from utils.styles import inject_global_css, render_kpi_card, render_section_title, PRIMARY, SUCCESS, WARNING, INFO

st.set_page_config(page_title="数据分析", layout="wide", page_icon="📊", menu_items=None)
inject_global_css()

st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
    <span style="font-size:2rem;">📊</span>
    <h1 style="margin:0;font-size:1.8rem;color:#333;">胜宏科技工作分析系统</h1>
</div>
<p style="color:#888;font-size:0.9rem;margin:0 0 0 44px;">工作记录 · 数据分析 · 智能洞察 · 测试报告 · 联调总结</p>
""", unsafe_allow_html=True)

st.markdown("---")

OUTPUT_FILE = Path("任务级数据.xlsx")
REPORT_DIR = Path("report")

has_data = OUTPUT_FILE.exists()
has_reports = REPORT_DIR.exists() and any(f.suffix == ".txt" for f in REPORT_DIR.glob("*.txt"))

task_count = 0
total_hours = 0.0
if has_data:
    try:
        df = pd.read_excel(OUTPUT_FILE)
        task_count = len(df)
        total_hours = df["工时"].sum() if "工时" in df.columns else 0
    except Exception:
        pass

report_count = 0
if has_reports:
    try:
        report_count = len([f for f in REPORT_DIR.glob("*.txt")])
    except Exception:
        pass

render_section_title("📈", "数据概览")
c1, c2, c3 = st.columns(3)
with c1:
    render_kpi_card(f"{total_hours:.0f}h", "累计工时", "⏱️", PRIMARY)
with c2:
    render_kpi_card(f"{task_count}", "任务总数", "📋", SUCCESS)
with c3:
    render_kpi_card(f"{report_count}", "测试报告", "📄", INFO)

st.markdown("---")

render_section_title("🧭", "功能导航")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="feature-card" style="background:linear-gradient(135deg,#f0f5ff 0%,#e0ecff 100%);">
        <div class="card-icon">📊</div>
        <div class="card-title" style="color:#4C78A8;">数据分析</div>
        <div class="card-desc">工时趋势、任务分布、设备分析<br>AI 智能洞察与行动建议</div>
        <div class="card-tags">筛选 · 图表 · 导出 · AI分析</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("进入数据分析 →", key="goto_data", width='stretch', type="primary"):
        st.switch_page("pages/1_数据分析.py")

with c2:
    st.markdown("""
    <div class="feature-card" style="background:linear-gradient(135deg,#f0fff4 0%,#dcffe6 100%);">
        <div class="card-icon">📋</div>
        <div class="card-title" style="color:#54A24B;">测试报告</div>
        <div class="card-desc">测试报告管理与分析<br>问题追踪与状态统计</div>
        <div class="card-tags">创建 · 编辑 · 筛选 · 统计</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("进入测试报告 →", key="goto_report", width='stretch', type="primary"):
        st.switch_page("pages/3_测试报告分析.py")

with c3:
    st.markdown("""
    <div class="feature-card" style="background:linear-gradient(135deg,#fff4f0 0%,#ffe6d5 100%);">
        <div class="card-icon">📝</div>
        <div class="card-title" style="color:#E57A1F;">联调总结</div>
        <div class="card-desc">联调进度汇总与问题追踪<br>厂家维度问题分析</div>
        <div class="card-tags">新建 · 分析 · 统计</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("进入联调总结 →", key="goto_jd", width='stretch', type="primary"):
        st.switch_page("pages/6_联调总结.py")

st.markdown("---")
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;color:#aaa;font-size:0.8rem;">
    <span>💡 版本 v2.7</span>
    <span>数据分析 · 智能洞察 · 配置管理 · 测试报告 · 联调总结</span>
</div>
""", unsafe_allow_html=True)
