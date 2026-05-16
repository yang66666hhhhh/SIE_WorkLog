import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.report_form import render_report_form
from utils.styles import inject_global_css, render_sidebar_nav

st.set_page_config(page_title="新建测试报告", layout="wide", page_icon="📝")
inject_global_css()

with st.sidebar:
    render_sidebar_nav("测试报告")

st.title("📝 新建测试报告")

result = render_report_form(report_data=None, mode="create")
if result == "back":
    st.switch_page("pages/3_测试报告分析.py")
