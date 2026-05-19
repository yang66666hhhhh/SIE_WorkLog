"""联调总结分析页"""
import streamlit as st
import pandas as pd
import json
from utils import report_db
from utils.styles import (
    inject_global_css, render_kpi_card, render_section_title,
    render_top_nav, PRIMARY, SUCCESS, WARNING, DANGER, INFO,
)

st.set_page_config(
    page_title="联调总结分析",
    layout="wide",
    page_icon="📊",
    menu_items=None,
)
inject_global_css()

TEMPLATE_TYPE = "joint_debug_summary"


def _parse_meta(raw):
    try:
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


def _load_reports():
    rows = report_db.get_all_reports(template_type=TEMPLATE_TYPE)
    records = []
    for r in rows:
        meta = _parse_meta(r.get("metadata_json", ""))
        records.append({
            "filename": r.get("filename", ""),
            "date": r.get("date", ""),
            "lines": r.get("lines", ""),
            "content": r.get("content", ""),
            **meta,
        })
    return pd.DataFrame(records)


@st.cache_data(ttl=120)
def load_data():
    df = _load_reports()
    if not df.empty and "lines" not in df.columns:
        df["lines"] = ""
    return df


st.title("📊 联调总结分析")

df = load_data()

if df.empty:
    st.info("暂无联调总结记录，请先创建。")
    if st.button("➕ 去新建联调总结"):
        st.switch_page("pages/6_联调总结.py")
    st.stop()

# KPI
total = len(df)
status_counts = df["status"].value_counts() if "status" in df.columns else pd.Series()
in_progress = status_counts.get("测试中", 0) + status_counts.get("测试中，完成", 0) + status_counts.get("测试中，部分完成", 0)
done = status_counts.get("已完成", 0)

col1, col2, col3, col4 = st.columns(4)
with col1: render_kpi_card(f"{total}", "总记录", "📋", PRIMARY)
with col2: render_kpi_card(f"{in_progress}", "进行中", "🔄", WARNING)
with col3: render_kpi_card(f"{done}", "已完成", "✅", SUCCESS)
total_hours = 0.0
if "total_hours" in df.columns:
    for v in df["total_hours"].dropna():
        try:
            total_hours += float(v)
        except Exception:
            pass
with col4: render_kpi_card(f"{total_hours:.1f}h", "累计可测试时长", "⏱️", INFO)

# Filters
with st.sidebar:
    st.markdown("**🔍 筛选条件**")
    all_lines = sorted(df["lines"].dropna().unique().tolist()) if "lines" in df.columns else []
    sel_lines = st.multiselect("线体", all_lines, default=all_lines)
    all_status = ["测试中", "测试中，完成", "测试中，部分完成", "已完成"]
    sel_status = st.multiselect("状态", all_status, default=all_status)

if "lines" in df.columns and "status" in df.columns:
    filtered = df[
        (df["lines"].isin(sel_lines)) &
        (df["status"].isin(sel_status))
    ]
else:
    filtered = df.copy()

render_section_title("📈", "统计分析")

tab1, tab2, tab3 = st.tabs(["按线体", "按状态", "按厂家问题"])

with tab1:
    if not filtered.empty and "lines" in filtered.columns:
        by_line = filtered.groupby("lines").size().reset_index(name="记录数")
        st.dataframe(by_line, hide_index=True, use_container_width=True)

with tab2:
    if not filtered.empty and "status" in filtered.columns:
        by_status = filtered["status"].value_counts().reset_index(name="记录数")
        by_status.columns = ["状态", "记录数"]
        st.dataframe(by_status, hide_index=True, use_container_width=True)

with tab3:
    if not filtered.empty:
        vendors = ["machine", "logistics", "main", "sie", "other"]
        vendor_labels = {
            "machine": "收放板机",
            "logistics": "自动化物流",
            "main": "主线设备",
            "sie": "软件集成",
            "other": "其他",
        }
        issues_data = []
        for _, row in filtered.iterrows():
            issues_today = row.get("issues_today", {}) or {}
            issues_next = row.get("issues_next", {}) or {}
            vendors_row = row.get("vendors", {}) or {}
            for vk in vendors:
                vlabel = f"{vendor_labels.get(vk, vk)}（{vendors_row.get(vk, '')}）"
                for ik in ["issues_today", "issues_next"]:
                    idict = row.get(ik, {}) or {}
                    val = idict.get(vk, "无")
                    if val and val != "无":
                        issues_data.append({
                            "线体": row.get("lines", ""),
                            "厂家": vlabel,
                            "问题": val,
                            "类型": "今日" if ik == "issues_today" else "明日预计",
                        })
        if issues_data:
            issues_df = pd.DataFrame(issues_data)
            st.dataframe(issues_df, hide_index=True, use_container_width=True)
        else:
            st.info("暂无问题记录")

render_section_title("📝", "明细记录")
records_sorted = filtered.sort_values("date", ascending=False)
for _, row in records_sorted.iterrows():
    with st.expander(f"📅 {row.get('date', '')} · {row.get('lines', '')} · {row.get('status', '')}"):
        col_dt, col_st = st.columns([1, 3])
        with col_dt:
            st.markdown(f"**日期**: {row.get('date', '-')}")
            st.markdown(f"**线体**: {row.get('lines', '-')}")
            st.markdown(f"**状态**: {row.get('status', '-')}")
            st.markdown(f"**计划完成**: {row.get('plan_date', '-')}")
        with col_st:
            st.markdown(f"**测试场景**: {row.get('test_scene', '-')}")
            st.markdown(f"**实际开始**: {row.get('actual_start_date', '-')}")
            st.markdown(f"**可测试时长**: {row.get('total_hours', '-')}h")
            st.markdown(f"**待办**: {row.get('todo_today', '-')}")
