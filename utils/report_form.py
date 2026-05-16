"""报告表单共享模块"""
import re
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

CATEGORIES = ["投收板机", "自动化物流（海康）", "主线设备", "软件集成（SIE）", "生产/工艺", "生产", "工艺", "维护", "IT"]
LINE_OPTIONS = ["VCP1", "VCP2", "PLB"]
REPORT_DIR = Path("report")


def parse_report_to_form(report_data):
    """将报告数据解析为表单格式"""
    form_data = {
        "report_date": report_data.get("日期", ""),
        "selected_lines": report_data.get("线体", "").split(", ") if report_data.get("线体") else [],
        "time_periods": parse_time_periods_from_duration(report_data.get("测试总时长", "")),
        "work_order": report_data.get("工单", ""),
        "today_plans": [],
        "actual_scenes": [],
        "processes": [],
        "problems": {cat: "" for cat in CATEGORIES},
        "todo_item": "",
        "test_results": [],
        "completions": [],
        "next_plan_scene": "",
        "next_plan_processes": [],
        "coordination": ""
    }

    today_plan = report_data.get("今日计划", "")
    if today_plan:
        lines = today_plan.split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) > 2 and (line.startswith("①") or line.startswith("②") or line.startswith("③")):
                form_data["today_plans"].append(line[2:].strip())
            elif line:
                form_data["today_plans"].append(line)

    actual_scene = report_data.get("实际场景", "")
    if actual_scene:
        lines = actual_scene.split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) > 2 and (line.startswith("①") or line.startswith("②") or line.startswith("③")):
                form_data["actual_scenes"].append(line[2:].strip())
            elif line:
                form_data["actual_scenes"].append(line)

    process_flow = report_data.get("流程", "")
    if process_flow:
        lines = process_flow.split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) > 2 and (line.startswith("①") or line.startswith("②") or line.startswith("③")):
                form_data["processes"].append(line[2:].strip())
            elif line:
                form_data["processes"].append(line)

    test_results = report_data.get("测试结果", "")
    if test_results:
        lines = test_results.split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) > 2 and (line.startswith("①") or line.startswith("②") or line.startswith("③")):
                form_data["test_results"].append(line[2:].strip())
            elif line:
                form_data["test_results"].append(line)

    completions = report_data.get("计划完成情况", "")
    if completions:
        lines = completions.split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) > 2 and (line.startswith("①") or line.startswith("②") or line.startswith("③")):
                form_data["completions"].append(line[2:].strip())
            elif line:
                form_data["completions"].append(line)

    tomorrow_plan = report_data.get("明日计划", "")
    if tomorrow_plan:
        lines = tomorrow_plan.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("测试场景："):
                form_data["next_plan_scene"] = line[5:].strip()
            elif line.startswith("明细流程："):
                continue
            elif line and len(line) > 2 and (line.startswith("①") or line.startswith("②") or line.startswith("③")):
                form_data["next_plan_processes"].append(line[2:].strip())
            elif "需要协调事项：" in line:
                form_data["coordination"] = line.split("需要协调事项：")[1].strip()

    coordination = report_data.get("需要协调事项", "")
    if coordination and not form_data["coordination"]:
        form_data["coordination"] = coordination

    todo_item = report_data.get("待办项", "")
    if todo_item:
        form_data["todo_item"] = todo_item

    return form_data


def parse_time_periods_from_duration(duration_str):
    if not duration_str:
        return []
    matches = re.findall(r'(\d{2}:\d{2})-(\d{2}:\d{2})', duration_str)
    periods = []
    for start, end in matches:
        periods.append({"start": start, "end": end})
    return periods if periods else []


def parse_time_periods(time_str):
    if not time_str:
        return []
    matches = re.findall(r'(\d{2}:\d{2})-(\d{2}:\d{2})', time_str)
    periods = []
    for start, end in matches:
        periods.append({"start": start, "end": end})
    return periods


def generate_report_content(date_str, lines, time_periods, work_order, today_plans,
                           actual_scenes, processes, problems, todo_item,
                           test_results, completions, next_plan_scene, next_plan_processes, coordination):
    total_minutes = 0
    time_display_parts = []
    for p in time_periods:
        try:
            start_min = int(p["start"].split(":")[0]) * 60 + int(p["start"].split(":")[1])
            end_min = int(p["end"].split(":")[0]) * 60 + int(p["end"].split(":")[1])
            if end_min > start_min:
                total_minutes += (end_min - start_min)
            time_display_parts.append(f"{p['start']}-{p['end']}")
        except:
            pass

    total_hours = total_minutes / 60.0
    time_display = f"{total_hours:.1f}小时（{', '.join(time_display_parts)}）" if time_display_parts else f"{total_hours:.1f}小时"

    content_parts = []
    content_parts.append(f"【日期】{date_str}")

    if len(today_plans) == 1:
        content_parts.append(f"【今日计划】{today_plans[0]}")
    elif len(today_plans) > 1:
        content_parts.append("【今日计划】")
        for i, item in enumerate(today_plans, 1):
            content_parts.append(f"\t{chr(9312 + i)} {item}")
    else:
        content_parts.append("【今日计划】")

    content_parts.append(f"【测试总时长】{time_display}")

    if len(actual_scenes) == 1:
        content_parts.append(f"【实际场景】{actual_scenes[0]}")
    elif len(actual_scenes) > 1:
        content_parts.append("【实际场景】")
        for i, item in enumerate(actual_scenes, 1):
            content_parts.append(f"\t{chr(9312 + i)} {item}")
    else:
        content_parts.append("【实际场景】")

    content_parts.append(f"【工单】{work_order if work_order else '无'}")

    if len(processes) == 1:
        content_parts.append(f"【流程】{processes[0]}")
    elif len(processes) > 1:
        content_parts.append("【流程】")
        for i, item in enumerate(processes, 1):
            content_parts.append(f"\t{chr(9312 + i)} {item}")
    else:
        content_parts.append("【流程】")

    content_parts.append("【问题汇总】")
    for cat in CATEGORIES:
        content = problems.get(cat, "").strip()
        if not content or content == "无":
            content_parts.append(f"\t{cat}：无")
        elif "\n" in content:
            content_parts.append(f"\t{cat}：")
            for line in content.split("\n"):
                line = line.strip()
                if line:
                    content_parts.append(f"\t\t{line}")
        else:
            content_parts.append(f"\t{cat}：{content}")

    content_parts.append(f"【待办项】{todo_item if todo_item else '无'}")

    if len(test_results) == 1:
        content_parts.append(f"【测试结果】{test_results[0]}")
    elif len(test_results) > 1:
        content_parts.append("【测试结果】")
        for i, item in enumerate(test_results, 1):
            content_parts.append(f"\t{chr(9312 + i)} {item}")
    else:
        content_parts.append("【测试结果】")

    if len(completions) == 1:
        content_parts.append(f"【今日计划实际是否完成】{completions[0]}")
    elif len(completions) > 1:
        content_parts.append("【今日计划实际是否完成】")
        for i, item in enumerate(completions, 1):
            content_parts.append(f"\t{chr(9312 + i)} {item}")
    else:
        content_parts.append("【今日计划实际是否完成】")

    content_parts.append("【明日计划】")
    content_parts.append(f"测试场景：{next_plan_scene if next_plan_scene else ''}")

    if next_plan_processes:
        content_parts.append("明细流程：")
        for i, item in enumerate(next_plan_processes, 1):
            content_parts.append(f"\t{chr(9312 + i)} {item}")

    content_parts.append(f"需要协调事项：{coordination if coordination else '无'}")

    return "\n".join(content_parts)


def render_report_form(report_data=None, mode="create", original_filename=None):
    is_edit = mode == "edit"
    title = "✏️ 编辑报告" if is_edit else "📝 新建报告"

    if is_edit and report_data:
        form_data = parse_report_to_form(report_data)
        filename = original_filename or report_data.get("文件名", "")
    else:
        form_data = {
            "report_date": datetime.now().date(),
            "selected_lines": LINE_OPTIONS[:1] if LINE_OPTIONS else [],
            "time_detail": "",
            "work_order": "",
            "today_plans": [],
            "actual_scenes": [],
            "processes": [],
            "problems": {cat: "" for cat in CATEGORIES},
            "todo_item": "",
            "test_results": [],
            "completions": [],
            "next_plan_scene": "",
            "next_plan_processes": [],
            "coordination": ""
        }
        filename = ""

    st.subheader(title)

    col_date, col_lines = st.columns([1, 2])
    with col_date:
        if is_edit and form_data.get("report_date"):
            try:
                default_date = pd.to_datetime(form_data["report_date"]).date()
            except:
                default_date = datetime.now().date()
        else:
            default_date = form_data.get("report_date", datetime.now().date())
        if isinstance(default_date, str):
            default_date = datetime.now().date()
        report_date = st.date_input("日期", value=default_date, format="YYYY-MM-DD")

    with col_lines:
        selected_lines = st.multiselect("线体", options=LINE_OPTIONS, default=form_data.get("selected_lines", []))

    st.markdown("##### 测试时间段")

    if "time_periods" not in st.session_state:
        init_periods = form_data.get("time_periods", [{"start": "09:30", "end": "12:00"}])
        st.session_state.time_periods = init_periods

    if st.button("➕ 添加时间段"):
        st.session_state.time_periods.append({"start": "14:30", "end": "18:00"})

    time_periods = st.session_state.time_periods
    new_periods = []

    cols_header = st.columns([4, 1, 4, 1])
    with cols_header[0]:
        st.markdown("**开始时间**")
    with cols_header[2]:
        st.markdown("**结束时间**")

    for i, p in enumerate(time_periods):
        cols = st.columns([4, 1, 4, 1])
        try:
            start_default = datetime.strptime(p.get("start", "09:30"), "%H:%M").time()
        except:
            start_default = datetime.strptime("09:30", "%H:%M").time()
        try:
            end_default = datetime.strptime(p.get("end", "12:00"), "%H:%M").time()
        except:
            end_default = datetime.strptime("12:00", "%H:%M").time()

        with cols[0]:
            start_time = st.time_input(f"开始{i}", value=start_default, key=f"time_start_{i}")
        with cols[2]:
            end_time = st.time_input(f"结束{i}", value=end_time, key=f"time_end_{i}")
        with cols[3]:
            if len(time_periods) > 1 and st.button("❌", key=f"del_time_{i}", help="删除"):
                st.session_state.time_periods.pop(i)
                st.rerun()

        new_periods.append({
            "start": start_time.strftime("%H:%M") if hasattr(start_time, 'strftime') else str(start_time)[:5],
            "end": end_time.strftime("%H:%M") if hasattr(end_time, 'strftime') else str(end_time)[:5]
        })

    time_periods = new_periods

    total_minutes = 0
    time_display_parts = []
    for p in time_periods:
        try:
            start_min = int(p["start"].split(":")[0]) * 60 + int(p["start"].split(":")[1])
            end_min = int(p["end"].split(":")[0]) * 60 + int(p["end"].split(":")[1])
            if end_min > start_min:
                total_minutes += (end_min - start_min)
            time_display_parts.append(f"{p['start']}-{p['end']}")
        except:
            pass

    total_hours = total_minutes / 60.0
    time_display = ", ".join(time_display_parts)

    col_hours, col_time = st.columns(2)
    with col_hours:
        st.metric("计算总时长", f"{total_hours:.1f} 小时")
    with col_time:
        st.metric("明细时间段", time_display if time_display else "-")

    st.markdown("---")
    st.subheader("📋 今日计划")
    today_plans = []
    for i in range(3):
        val = form_data["today_plans"][i] if i < len(form_data["today_plans"]) else ""
        p = st.text_input(
            f"计划{i+1}",
            value=val,
            placeholder="垂直电镀VCP1自动化测试（放板机）" if i == 0 else ""
        )
        if p:
            today_plans.append(p)

    st.markdown("---")
    st.subheader("📊 实际场景")
    actual_scenes = []
    for i in range(3):
        val = form_data["actual_scenes"][i] if i < len(form_data["actual_scenes"]) else ""
        s = st.text_input(
            f"场景{i+1}",
            value=val,
            placeholder="自动化测试：VCP1（测试环境）" if i == 0 else ""
        )
        if s:
            actual_scenes.append(s)

    st.markdown("---")
    st.subheader("📦 工单信息")
    work_order = st.text_input(
        "工单",
        value=form_data.get("work_order", ""),
        placeholder="M126041900006，共3528 PCS"
    )

    st.markdown("---")
    st.subheader("🔄 流程")
    processes = []
    for i in range(3):
        val = form_data["processes"][i] if i < len(form_data["processes"]) else ""
        p = st.text_input(
            f"流程{i+1}",
            value=val,
            placeholder="自动化：叫料→AGV送料→..." if i == 0 else ""
        )
        if p:
            processes.append(p)

    st.markdown("---")
    st.subheader("⚠️ 问题汇总")
    problems = {}
    for cat in CATEGORIES:
        val = form_data["problems"].get(cat, "")
        problems[cat] = st.text_area(
            cat,
            value=val,
            placeholder=f'{cat}相关问题',
            height=70
        )

    st.markdown("---")
    st.subheader("📋 待办项")
    todo_item = st.text_input(
        "待办项",
        value=form_data.get("todo_item", ""),
        placeholder="待处理事项描述"
    )

    st.markdown("---")
    st.subheader("📊 测试结果")
    test_results = []
    for i in range(3):
        val = form_data["test_results"][i] if i < len(form_data["test_results"]) else ""
        r = st.text_area(
            f"结果{i+1}",
            value=val,
            placeholder="自动化测试：...",
            height=60
        )
        if r:
            test_results.append(r)

    st.markdown("---")
    st.subheader("✅ 计划完成情况")
    completions = []
    for i in range(3):
        val = form_data["completions"][i] if i < len(form_data["completions"]) else ""
        c = st.text_area(
            f"完成情况{i+1}",
            value=val,
            placeholder="自动化测试：尚未完成",
            height=60
        )
        if c:
            completions.append(c)

    st.markdown("---")
    st.subheader("📅 明日计划")
    next_plan_scene = st.text_input(
        "测试场景",
        value=form_data.get("next_plan_scene", ""),
        placeholder="VCP1/VCP2线放板机全流程（测试环境）"
    )

    next_plan_processes = []
    for i in range(3):
        val = form_data["next_plan_processes"][i] if i < len(form_data["next_plan_processes"]) else ""
        p = st.text_input(
            f"明细流程{i+1}",
            value=val,
            placeholder="放板机：叫料→AGV送料→..." if i == 0 else ""
        )
        if p:
            next_plan_processes.append(p)

    coordination = st.text_input(
        "需要协调事项",
        value=form_data.get("coordination", ""),
        placeholder="需要IT帮忙做工艺跳站"
    )

    st.markdown("---")

    col_back, col_save = st.columns(2)

    with col_back:
        if is_edit:
            if st.button("← 返回报告列表", use_container_width=True):
                return "back"
        else:
            if st.button("← 返回Dashboard", use_container_width=True):
                return "back"

    with col_save:
        submit_text = "💾 保存修改" if is_edit else "💾 生成报告"
        submitted = st.button(submit_text, use_container_width=True, type="primary")

        if submitted:
            if not selected_lines:
                st.error("⚠️ 请至少选择一个线体")
                return None

            with st.spinner("正在保存报告..."):
                date_str = report_date.strftime("%Y-%m-%d")

                if is_edit and filename:
                    save_filename = filename
                else:
                    lines_str = "_".join([l.lower() for l in selected_lines])
                    save_filename = f"{date_str}_{lines_str}.txt"

                content = generate_report_content(
                    date_str, selected_lines, time_periods, work_order,
                    today_plans, actual_scenes, processes, problems, todo_item,
                    test_results, completions, next_plan_scene, next_plan_processes, coordination
                )

                file_path = REPORT_DIR / save_filename
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    st.success(f"✅ {'报告已保存' if is_edit else '报告已生成'}：{save_filename}")
                    st.balloons()
                    return save_filename
                except Exception as e:
                    st.error(f"❌ 保存失败：{e}")
                    return None

    return None
