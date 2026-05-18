import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.problem_tracker import (
    load_problems, add_problem, update_problem_status, delete_problem,
    search_problems, get_pending_problems, get_weekly_summary,
    PROBLEM_STATES
)
from utils.report_form import CATEGORIES
from utils.styles import inject_global_css, render_sidebar_nav

st.set_page_config(page_title="问题追踪", layout="wide", page_icon="🔍", menu_items=None)
inject_global_css()

with st.sidebar:
    render_sidebar_nav("问题追踪")


def render_problem_card(p: dict, show_history: bool = False):
    status = p.get("status", "待处理")
    status_color = {"待处理": "🔴", "排查中": "🟡", "已解决": "🟢"}.get(status, "⚪")
    st.markdown(f"**{status_color} {status}** · {p.get('category', '')} · {p.get('line', '')}")
    st.markdown(p.get("description", ""))
    st.caption(f"📅 {p.get('date', '')} · 创建于 {p.get('created_at', '')}")
    if show_history and p.get("history"):
        with st.expander("📋 变更历史"):
            for h in p.get("history", []):
                st.markdown(f"- **{h.get('status', '')}** @ {h.get('time', '')}: {h.get('note', '')}")


st.title("🔍 问题追踪")

tab_list, tab_add, tab_summary = st.tabs(["📋 问题列表", "➕ 添加问题", "📊 周汇总"])

# =====================
# 问题列表
# =====================
with tab_list:
    col_search1, col_search2, col_search3 = st.columns([2, 1, 1])
    with col_search1:
        kw = st.text_input("🔍 搜索问题", placeholder="输入关键词搜索...", key="prob_search")
    with col_search2:
        status_filter = st.selectbox("状态", ["全部"] + PROBLEM_STATES, key="prob_status_filter")
    with col_search3:
        cat_filter = st.selectbox("部门", ["全部"] + CATEGORIES, key="prob_cat_filter")

    all_probs = search_problems(
        keyword=kw,
        status="" if status_filter == "全部" else status_filter,
        category="" if cat_filter == "全部" else cat_filter
    )

    st.caption(f"共 {len(all_probs)} 条问题")

    if not all_probs:
        st.info("暂无问题记录")

    for p in all_probs:
        with st.container():
            render_problem_card(p, show_history=True)

            col_up, col_del = st.columns([1, 1])
            with col_up:
                current = p.get("status", "待处理")
                new_status = st.selectbox(
                    f"变更为", PROBLEM_STATES,
                    index=PROBLEM_STATES.index(current) if current in PROBLEM_STATES else 0,
                    key=f"status_{p['id']}"
                )
                if new_status != current:
                    note = st.text_input("备注", placeholder="状态变更说明...", key=f"note_{p['id']}")
                    if st.button("✅ 确认更新", key=f"up_{p['id']}"):
                        update_problem_status(p["id"], new_status, note)
                        st.rerun()

            with col_del:
                st.write("")
                st.write("")
                if st.button("🗑️ 删除", key=f"del_{p['id']}"):
                    delete_problem(p["id"])
                    st.rerun()

        st.divider()

# =====================
# 添加问题
# =====================
with tab_add:
    st.subheader("添加新问题")
    col_desc, col_cat = st.columns([3, 1])
    with col_desc:
        desc = st.text_area("问题描述", placeholder="详细描述问题...", height=100)
    with col_cat:
        category = st.selectbox("部门", CATEGORIES)
    col_line, col_src, col_date = st.columns([1, 1, 1])
    with col_line:
        line = st.text_input("线体", placeholder="VCP1/VCP2/PLB")
    with col_src:
        source = st.text_input("来源", placeholder="如：设备异常")
    with col_date:
        date = st.date_input("日期")

    if st.button("➕ 添加到问题库", type="primary", width='stretch'):
        if desc and category and line:
            add_problem(desc, category, line, source, date.strftime("%Y-%m-%d"))
            st.success("✅ 问题已添加")
            st.rerun()
        else:
            st.error("⚠️ 描述、部门、线体为必填项")

# =====================
# 周汇总
# =====================
with tab_summary:
    summary = get_weekly_summary()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("问题总数", summary["total"])
    col2.metric("待处理", summary["pending"])
    col3.metric("排查中", summary["investigating"])
    col4.metric("已解决", summary["resolved"])

    st.markdown("---")
    col_cat, col_line = st.columns(2)

    with col_cat:
        st.markdown("**📂 按部门分布**")
        by_cat = summary.get("by_category", {})
        if by_cat:
            for cat, cnt in sorted(by_cat.items(), key=lambda x: -x[1]):
                st.markdown(f"- {cat}: **{cnt}** 条")
        else:
            st.info("暂无数据")

    with col_line:
        st.markdown("**🏭 按线体分布**")
        by_line = summary.get("by_line", {})
        if by_line:
            for line, cnt in sorted(by_line.items(), key=lambda x: -x[1]):
                st.markdown(f"- {line}: **{cnt}** 条")
        else:
            st.info("暂无数据")

    st.markdown("---")
    st.markdown("**🔴 待处理问题（最近 10 条）**")
    pending = summary.get("recent_pending", [])
    if pending:
        for p in pending:
            with st.container():
                render_problem_card(p)
                st.divider()
    else:
        st.success("🎉 所有问题已解决！")
