import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.report_form import render_report_form

st.set_page_config(page_title="新建测试报告", layout="wide", page_icon="📝")

st.title("📝 新建测试报告")

render_report_form(report_data=None, mode="create")