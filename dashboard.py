import streamlit as st

st.set_page_config(page_title="Work Analytics", layout="wide", page_icon="📊", menu_items=None)

pages = {
    "🏠 首页": [
        st.Page("pages/0_首页.py", title="系统首页", icon="🏠"),
    ],
    "📊 数据分析": [
        st.Page("pages/1_数据分析.py", title="数据分析", icon="📊"),
    ],
    "🔍 问题追踪": [
        st.Page("pages/2_问题追踪.py", title="问题追踪", icon="🔍"),
    ],
    "📋 测试报告": [
        st.Page("pages/3_测试报告分析.py", title="报告分析", icon="📄"),
        st.Page("pages/4_新建报告.py", title="新建报告", icon="📝"),
    ],
    "📝 联调总结": [
        st.Page("pages/6_联调总结.py", title="新建总结", icon="📝"),
        st.Page("pages/7_联调总结分析.py", title="总结分析", icon="📊"),
    ],
    "⚙️ 系统配置": [
        st.Page("pages/5_系统配置.py", title="系统配置", icon="⚙️"),
    ],
}

pg = st.navigation(pages, position="top")
pg.run()
