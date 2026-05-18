import streamlit as st
import pandas as pd
from pathlib import Path
from utils.styles import (
    inject_global_css, render_kpi_card, render_section_title, render_sidebar_nav,
    PRIMARY, SUCCESS, WARNING, INFO,
)

st.set_page_config(page_title="Work Analytics", layout="wide", page_icon="📊", menu_items=None)
inject_global_css()

with st.sidebar:
    render_sidebar_nav("首页")

st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
    <span style="font-size:2rem;">📊</span>
    <h1 style="margin:0;font-size:1.8rem;color:#333;">胜宏科技工作分析系统</h1>
</div>
<p style="color:#888;font-size:0.9rem;margin:0 0 0 44px;">工作记录 · 数据分析 · 智能洞察 · 测试报告</p>
""", unsafe_allow_html=True)

st.markdown("---")

OUTPUT_FILE = Path("任务级数据.xlsx")
REPORT_DIR = Path("report")

has_data = OUTPUT_FILE.exists()
has_reports = REPORT_DIR.exists() and any(f.suffix == ".txt" and "模板" not in f.name for f in REPORT_DIR.glob("*.txt"))

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
        report_count = len([f for f in REPORT_DIR.glob("*.txt") if "模板" not in f.name])
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
    if st.button("进入数据分析 →", key="goto_data", use_container_width=True, type="primary"):
        st.switch_page("pages/1_数据分析.py")

with c2:
    st.markdown("""
    <div class="feature-card" style="background:linear-gradient(135deg,#f0fff4 0%,#dcffe6 100%);">
        <div class="card-icon">📋</div>
        <div class="card-title" style="color:#54A24B;">测试报告</div>
        <div class="card-desc">报告管理、问题追踪<br>状态统计与趋势分析</div>
        <div class="card-tags">创建 · 编辑 · 筛选 · 统计</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("进入测试报告 →", key="goto_report", use_container_width=True, type="primary"):
        st.switch_page("pages/3_测试报告分析.py")

with c3:
    st.markdown("""
    <div class="feature-card" style="background:linear-gradient(135deg,#fff8f0 0%,#ffe8d0 100%);">
        <div class="card-icon">⚙️</div>
        <div class="card-title" style="color:#F58518;">系统配置</div>
        <div class="card-desc">设备线体、任务类型、AI 配置<br>项目名称与配置备份</div>
        <div class="card-tags">增删改查 · 正则校验 · 备份</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("进入系统配置 →", key="goto_config", use_container_width=True, type="primary"):
        st.switch_page("pages/5_系统配置.py")

st.markdown("---")
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;color:#aaa;font-size:0.8rem;">
    <span>💡 版本 v2.2</span>
    <span>数据分析 · 智能洞察 · 配置管理 · 测试报告</span>
</div>
""", unsafe_allow_html=True)
