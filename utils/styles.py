from html import escape

import streamlit as st

PRIMARY = "#4C78A8"
PRIMARY_LIGHT = "#6B9FD2"
SUCCESS = "#54A24B"
WARNING = "#F58518"
DANGER = "#E45756"
INFO = "#667eea"
NEUTRAL = "#9D7559"

STATUS_COLORS = {"已解决": SUCCESS, "待处理": DANGER, "排查中": WARNING}
STATUS_ICONS = {"已解决": "✅", "待处理": "⚠️", "排查中": "🔍"}
LINE_COLORS = {"VCP1": "#667eea", "VCP2": "#f093fb", "PLB": "#4facfe", "其他": "#888"}
SOURCE_COLORS = {"MSAP": PRIMARY, "HDI二处": WARNING}


def inject_global_css():
    st.html("""
    <style>
        [data-testid="stSidebarNav"], [data-testid="stSidebarNavLinks"] {
            display: none !important;
        }
    </style>
    """)
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8f9fa 0%, #eaeef3 100%);
        }
        [data-testid="stSidebar"] .sidebar-title {
            font-size: 15px;
            font-weight: 700;
            color: #4C78A8;
            letter-spacing: 0.5px;
            padding: 4px 0 8px 0;
            border-bottom: 2px solid #4C78A8;
            margin-bottom: 12px;
        }
        .kpi-card {
            border-radius: 12px;
            padding: 20px 16px;
            text-align: center;
            color: white;
            margin-bottom: 8px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.08);
            transition: transform 0.15s ease;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        }
        .kpi-value {
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.2;
        }
        .kpi-label {
            font-size: 0.85rem;
            opacity: 0.9;
            margin-top: 6px;
        }
        .kpi-delta {
            font-size: 0.8rem;
            margin-top: 4px;
            opacity: 0.85;
        }
        .section-title {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 24px 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #e8ecf0;
        }
        .section-title .icon {
            font-size: 1.4rem;
        }
        .section-title .text {
            font-size: 1.15rem;
            font-weight: 700;
            color: #333;
        }
        .section-title .bar {
            width: 4px;
            height: 22px;
            border-radius: 2px;
            background: #4C78A8;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
        }
        .empty-state .icon {
            font-size: 3rem;
            margin-bottom: 12px;
        }
        .empty-state .title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #555;
            margin-bottom: 8px;
        }
        .empty-state .desc {
            font-size: 0.9rem;
            color: #999;
        }
        .feature-card {
            border-radius: 14px;
            padding: 24px 20px;
            text-align: center;
            transition: all 0.2s ease;
            border: 2px solid transparent;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        .feature-card:hover {
            border-color: #4C78A8;
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(76,120,168,0.15);
        }
        .feature-card .card-icon {
            font-size: 2.5rem;
            margin-bottom: 12px;
        }
        .feature-card .card-title {
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .feature-card .card-desc {
            font-size: 0.85rem;
            color: #666;
            line-height: 1.5;
        }
        .feature-card .card-tags {
            font-size: 0.75rem;
            color: #999;
            margin-top: 10px;
        }
        .problem-card {
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 10px 14px;
            margin-bottom: 8px;
            background: #fafafa;
        }
        .problem-card:hover {
            background: #f0f4f8;
        }
        .status-badge {
            padding: 3px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 500;
            display: inline-block;
        }
        .report-summary {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 10px;
        }
        .report-summary-row {
            border: 1px solid #edf0f3;
            border-radius: 8px;
            padding: 10px 12px;
            background: #fbfcfd;
        }
        .report-summary-row.has-issue {
            border-left: 4px solid #F58518;
            background: #fffaf3;
        }
        .report-summary-row.is-empty {
            background: #fafafa;
        }
        .report-summary-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 6px;
        }
        .report-summary-module {
            color: #333;
            font-size: 0.88rem;
            font-weight: 700;
        }
        .report-summary-status {
            color: #999;
            font-size: 0.76rem;
            white-space: nowrap;
        }
        .report-summary-items {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .report-summary-item {
            color: #444;
            font-size: 0.86rem;
            line-height: 1.45;
            word-break: break-word;
        }
        .report-summary-empty {
            color: #aaa;
            font-size: 0.84rem;
        }
        .report-detail-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 4px 0 12px;
        }
        .report-detail-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border: 1px solid #e7ebef;
            border-radius: 7px;
            padding: 5px 9px;
            background: #f8fafc;
            color: #4a5560;
            font-size: 0.82rem;
            line-height: 1.3;
        }
        .report-detail-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin-top: 12px;
        }
        .report-detail-block {
            border: 1px solid #edf0f3;
            border-radius: 8px;
            padding: 10px 12px;
            background: #ffffff;
        }
        .report-detail-block.wide {
            grid-column: 1 / -1;
        }
        .report-detail-title {
            color: #4C78A8;
            font-size: 0.84rem;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .report-detail-list {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .report-detail-item {
            color: #444;
            font-size: 0.86rem;
            line-height: 1.45;
            word-break: break-word;
        }
        .report-detail-empty {
            color: #aaa;
            font-size: 0.84rem;
        }
        .filter-summary {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 4px 0 14px;
        }
        .filter-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border: 1px solid #e7ebef;
            border-radius: 7px;
            padding: 6px 10px;
            background: #f8fafc;
            color: #4a5560;
            font-size: 0.82rem;
            line-height: 1.3;
        }
        .chart-note {
            color: #7a8491;
            font-size: 0.82rem;
            margin: -4px 0 8px;
        }
        .rank-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .rank-row {
            border: 1px solid #edf0f3;
            border-radius: 8px;
            padding: 9px 11px;
            background: #fbfcfd;
        }
        .rank-head {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            color: #344054;
            font-size: 0.86rem;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .rank-bar {
            height: 7px;
            border-radius: 999px;
            background: #edf2f7;
            overflow: hidden;
        }
        .rank-fill {
            height: 100%;
            border-radius: 999px;
            background: #4C78A8;
        }
        .rank-meta {
            color: #8a94a3;
            font-size: 0.76rem;
            margin-top: 4px;
        }
        .config-overview {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin: 6px 0 16px;
        }
        .config-overview-card {
            border: 1px solid #edf0f3;
            border-radius: 8px;
            padding: 12px 14px;
            background: #fbfcfd;
        }
        .config-overview-label {
            color: #7a8491;
            font-size: 0.78rem;
            margin-bottom: 6px;
        }
        .config-overview-value {
            color: #26323f;
            font-size: 1.1rem;
            font-weight: 800;
            line-height: 1.25;
        }
        .config-overview-note {
            color: #9aa3af;
            font-size: 0.74rem;
            margin-top: 5px;
        }
        .config-tag-list {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }
        .config-tag {
            display: inline-flex;
            align-items: center;
            border: 1px solid #e7ebef;
            border-radius: 6px;
            padding: 3px 7px;
            background: #f8fafc;
            color: #4a5560;
            font-size: 0.78rem;
        }
        @media (max-width: 760px) {
            .report-detail-grid {
                grid-template-columns: 1fr;
            }
            .config-overview {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
    </style>
    """, unsafe_allow_html=True)


def render_kpi_card(value, label, icon, color, delta=None):
    delta_html = ""
    if delta:
        delta_color = "#fff9" if delta.startswith("↑") or delta.startswith("+") else "#fffa"
        delta_html = f'<div class="kpi-delta" style="color:{delta_color}">{delta}</div>'
    st.markdown(f"""
    <div class="kpi-card" style="background: linear-gradient(135deg, {color} 0%, {color}cc 100%);">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{icon} {label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_section_title(icon, title):
    st.markdown(f"""
    <div class="section-title">
        <div class="bar"></div>
        <span class="icon">{icon}</span>
        <span class="text">{title}</span>
    </div>
    """, unsafe_allow_html=True)


def render_empty_state(icon, title, description):
    st.markdown(f"""
    <div class="empty-state">
        <div class="icon">{icon}</div>
        <div class="title">{title}</div>
        <div class="desc">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_nav(current_page="首页"):
    pages = [
        ("🏠 首页", "首页", "dashboard"),
        ("📊 数据分析", "数据分析", "pages/1_数据分析"),
        ("🔍 问题追踪", "问题追踪", "pages/2_问题追踪"),
        ("📋 测试报告", "测试报告", "pages/3_测试报告分析"),
        ("⚙️ 系统配置", "系统配置", "pages/5_系统配置"),
    ]
    for label, name, page in pages:
        is_active = name == current_page
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, type=btn_type, width='stretch', key=f"nav_{page}"):
            st.switch_page(f"{page}.py")


def render_problem_card(line_name, status, description, date=None):
    sc = STATUS_COLORS.get(status, "#888")
    lc = LINE_COLORS.get(line_name, "#888")
    si = STATUS_ICONS.get(status, "📋")
    safe_line = escape(str(line_name))
    safe_status = escape(str(status))
    safe_desc = escape(str(description).replace(chr(10), " · "))
    date_html = ""
    if date:
        date_html = f'<span class="status-badge" style="background:#eef4ff;color:#4C78A8;min-width:78px;text-align:center;">📅 {escape(str(date))}</span>'
    st.markdown(
        f'<div class="problem-card">'
        f'<div style="display:flex;align-items:center;gap:12px;">'
        f'{date_html}'
        f'<span class="status-badge" style="background:{lc}20;color:{lc};min-width:55px;text-align:center;">{safe_line}</span>'
        f'<span class="status-badge" style="background:{sc}18;color:{sc};min-width:55px;text-align:center;">{si} {safe_status}</span>'
        f'<span style="color:#444;font-size:0.88rem;flex:1;line-height:1.4;">{safe_desc}</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
