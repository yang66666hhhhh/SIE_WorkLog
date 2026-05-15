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

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("### 🔍 数据分析")
    st.write("工时趋势 · 任务分布 · 设备分析")
    st.caption("工作数据分析、图表洞察")
    if st.button("进入", key="goto_data", use_container_width=True):
        st.switch_page("pages/1_数据分析.py")

with c2:
    st.markdown("### ⚙️ 系统配置")
    st.write("设备线体 · 任务类型 · AI配置")
    st.caption("管理设备关键词、任务分类规则")
    if st.button("进入", key="goto_config", use_container_width=True):
        st.switch_page("pages/2_系统配置.py")

with c3:
    st.markdown("### 📋 测试报告分析")
    st.write("自动化测试 · 问题汇总")
    st.caption("分析现有测试报告")
    if st.button("进入", key="goto_test", use_container_width=True):
        st.switch_page("pages/3_测试报告分析.py")

with c4:
    st.markdown("### 📝 新建报告")
    st.write("创建报告 · 预览生成")
    st.caption("新建测试报告文件")
    if st.button("进入", key="goto_new", use_container_width=True):
        st.switch_page("pages/4_新建报告.py")

st.markdown("---")
st.caption("💡 版本 v2.2 | 数据分析 · 智能洞察 · 配置管理 · 测试报告")
