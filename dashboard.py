import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(page_title="胜宏科技工作分析系统", layout="wide", page_icon="📊")

PAGES = {
    "1_数据分析.py": {"title": "数据分析", "icon": "📈", "desc": "工时趋势 · 任务分布 · 设备分析", "color": "#4C78A8"},
    "3_测试报告分析.py": {"title": "测试报告分析", "icon": "📋", "desc": "自动化测试 · 问题汇总", "color": "#E45756"},
    "4_新建报告.py": {"title": "新建报告", "icon": "📝", "desc": "创建报告 · 预览生成", "color": "#F58518"},
    "5_系统配置.py": {"title": "系统配置", "icon": "⚙️", "desc": "设备线体 · 任务类型 · AI配置", "color": "#54A24B"},
}

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .help-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin: 20px 0;
    }
    .help-box h3 {
        color: white;
        margin-bottom: 10px;
    }
    .help-box ul {
        margin-bottom: 0;
        padding-left: 20px;
    }
    .help-box li {
        margin: 5px 0;
    }
    div[data-testid="stHorizontalBlock"] > div {
        padding: 5px;
    }
    .feature-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 24px;
        border: 2px solid #e9ecef;
        transition: all 0.3s ease;
        height: 100%;
    }
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.1);
    }
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 12px;
    }
    .feature-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 8px;
        color: #262730;
    }
    .feature-desc {
        color: #6c757d;
        font-size: 0.9rem;
        margin-bottom: 16px;
    }
    .feature-btn {
        width: 100%;
    }
    .footer {
        text-align: center;
        color: #6c757d;
        font-size: 0.85rem;
        padding: 20px 0;
    }
    .report-count {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📊 胜宏科技工作分析系统</p>', unsafe_allow_html=True)

from utils.test_report_processor import TestReportProcessor
processor = TestReportProcessor()
df = processor.process_all()
report_count = len(df)

st.markdown(f'<div style="text-align:center;"><span class="report-count">📁 当前共有 {report_count} 份测试报告</span></div>', unsafe_allow_html=True)

st.markdown("""
<div class="help-box">
<h3>💡 快速开始</h3>
<ul>
<li><strong>数据分析</strong> - 查看工时趋势、任务分布、设备利用率</li>
<li><strong>系统配置</strong> - 管理设备线体、任务类型、AI设置</li>
<li><strong>测试报告分析</strong> - 分析自动化测试问题汇总，支持编辑</li>
<li><strong>新建报告</strong> - 创建新的测试报告文件</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("#### 选择功能模块")

cols = st.columns(len(PAGES))

for idx, (page_file, info) in enumerate(PAGES.items()):
    with cols[idx]:
        st.markdown(f"""
        <div class="feature-card">
            <div class="feature-icon">{info["icon"]}</div>
            <div class="feature-title">{info["title"]}</div>
            <div class="feature-desc">{info["desc"]}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"进入 →", key=f"goto_{page_file}", use_container_width=True):
            st.switch_page(f"pages/{page_file}")

st.markdown("")
st.markdown("")
st.markdown('<div class="footer">💡 使用左侧导航栏或上方按钮切换页面 | 数据存放在本地 report 目录 | 版本 v2.5</div>', unsafe_allow_html=True)