import streamlit as st

st.set_page_config(page_title="Work Analytics", layout="wide", page_icon="📊")

st.markdown("""
<style>
    .help-box {
        background: #f0f7ff;
        border-left: 4px solid #4C78A8;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .feature-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-top: 10px;
    }
    @media (max-width: 768px) {
        .stColumn {
            padding: 0px 5px;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 胜宏科技工作分析系统")

st.markdown("""
<div class="help-box">
💡 <b>使用帮助</b><br>
• 左侧导航栏可切换页面<br>
• 数据分析页面支持筛选、导出功能<br>
• 系统配置可管理设备线和任务类型
</div>
""", unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    st.markdown("### 🔍 数据分析")
    st.write("工时趋势 · 任务分布 · 设备分析 · AI洞察")
    st.caption("查看工作数据统计、分析图表、智能建议")
    if st.button("进入", key="goto_data", use_container_width=True):
        st.switch_page("pages/1_数据分析.py")

with c2:
    st.markdown("### ⚙️ 系统配置")
    st.write("设备线体 · 任务类型 · AI配置")
    st.caption("管理设备关键词、任务分类规则")
    if st.button("进入", key="goto_config", use_container_width=True):
        st.switch_page("pages/2_系统配置.py")

st.markdown("---")
st.caption("💡 版本 v2.1 | 数据分析 · 智能洞察 · 配置管理")
