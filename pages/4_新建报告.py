import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config import Config

st.set_page_config(page_title="新建测试报告", layout="wide", page_icon="📝")

st.title("📝 新建测试报告")

REPORT_DIR = Path("report")
CATEGORIES = ["投收板机", "自动化物流（海康）", "主线设备", "软件集成（SIE）", "生产/工艺", "生产", "工艺", "维护", "IT", "待办项"]

config = Config()
equipment = config.load_equipment()
LINE_OPTIONS = list(equipment.keys())

with st.expander("📋 填写说明", expanded=False):
    st.info("""
    1. 填写基本信息（日期、线体、测试时间）
    2. 填写问题汇总（每个来源的问题）
    3. 填写测试结果和计划完成情况
    4. 点击"预览"查看生成的内容
    5. 确认无误后点击"生成报告"
    """)

st.markdown("---")
st.subheader("📅 基本信息")

col_date, col_lines, col_time = st.columns(3)

with col_date:
    report_date = st.date_input("日期", value=datetime.now().date(), format="YYYY-MM-DD")

with col_lines:
    selected_lines = st.multiselect(
        "线体",
        options=LINE_OPTIONS,
        default=LINE_OPTIONS[0] if LINE_OPTIONS else None
    )

with col_time:
    test_hours = st.number_input("可测试时间（小时）", min_value=0.0, max_value=24.0, value=6.0, step=0.5)

time_detail = st.text_input("明细时间段", placeholder="9.30-12:00    14:30-18:00")

st.markdown("---")
st.subheader("📋 问题汇总")

problems = {}
for cat in CATEGORIES:
    problems[cat] = st.text_area(
        cat,
        placeholder=f"输入{cat}相关问题，多个问题用换行分隔",
        height=80
    )

st.markdown("---")
st.subheader("📊 测试结果与计划")

col_result, col_completion = st.columns(2)

with col_result:
    test_result = st.text_area("测试结果", placeholder="描述测试执行情况和结果", height=100)

with col_completion:
    completion_status = st.text_area("计划完成情况", placeholder="描述计划完成情况", height=100)

next_plan = st.text_area("明日/下周计划", placeholder="描述下一步测试计划", height=100)

coordination = st.text_input("需要协调事项", placeholder="如有需要协调的事项请填写")

st.markdown("---")

def generate_filename(date_str, lines):
    """生成文件名"""
    lines_str = "_".join(lines).lower()
    return f"{date_str}_{lines_str}.txt"

def generate_content(date_str, lines, hours, time_detail, problems, test_result, completion, next_plan, coordination):
    """生成报告内容"""
    lines_str = "、".join(lines)

    problem_lines = []
    for cat in CATEGORIES:
        content = problems.get(cat, "").strip()
        if content:
            lines_content = content.replace("\n", "\n\t")
            problem_lines.append(f"{cat}：\n\t{lines_content}")
        else:
            problem_lines.append(f"{cat}：无")

    problem_section = "\n".join(problem_lines)

    result = f"""【今日{{{date_str}}}计划】
\t{lines_str}自动化测试

【汇总如下】
【生产线可测试时间总计：{hours}小时】
明细时间段：{time_detail}

【测试场景】

【现场正式工单LOT号】

【明细流程】

【问题汇总】
{problem_section}

【测试结果】
\t{test_result}

【今日计划实际是否完成】
\t{completion}

【明日的测试计划】/【下周的测试计划】
{next_plan}
需要协调事项：{coordination if coordination else '无'}"""

    return result

preview_content = ""

col_preview, col_generate = st.columns(2)

with col_preview:
    if st.button("👁️ 预览", use_container_width=True):
        if not selected_lines:
            st.error("请至少选择一个线体")
        else:
            date_str = report_date.strftime("%m-%d")
            preview_content = generate_content(
                date_str, selected_lines, test_hours, time_detail,
                problems, test_result, completion_status, next_plan, coordination
            )

with col_generate:
    if st.button("💾 生成报告", use_container_width=True, type="primary"):
        if not selected_lines:
            st.error("请至少选择一个线体")
        else:
            date_str = report_date.strftime("%Y-%m-%d")
            filename = generate_filename(date_str, selected_lines)
            content = generate_content(
                report_date.strftime("%m-%d"), selected_lines, test_hours, time_detail,
                problems, test_result, completion_status, next_plan, coordination
            )

            file_path = REPORT_DIR / filename
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                st.success(f"✅ 报告已生成：{filename}")
            except Exception as e:
                st.error(f"生成失败：{e}")

if preview_content:
    with st.expander("👁️ 预览内容", expanded=True):
        st.text(preview_content)