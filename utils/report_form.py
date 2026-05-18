"""报告表单共享模块"""
import re
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

CATEGORIES = ["投收板机", "自动化物流（海康）", "主线设备", "软件集成（SIE）", "生产/工艺", "生产", "工艺", "维护", "IT"]
from utils.config import Config
from utils import report_db
_config = Config()
LINE_OPTIONS = list(_config.load_equipment().keys())
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

    problem_summary = report_data.get("问题汇总", "")
    if problem_summary:
        lines = problem_summary.split("\n")
        current_cat = None
        pending_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            cat_match = re.match(r"^([^：：]+)[：:]\s*(.*)$", stripped)
            if cat_match:
                cat_name = cat_match.group(1).strip()
                text = cat_match.group(2).strip()
                if cat_name in CATEGORIES:
                    if current_cat and pending_lines and form_data["problems"].get(current_cat, "") == "":
                        combined = "\n".join(pending_lines).strip()
                        if combined and combined != "无":
                            form_data["problems"][current_cat] = combined
                    current_cat = cat_name
                    pending_lines = [text] if text and text != "无" else []
                    continue
            if current_cat and stripped not in ("无", "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"):
                if stripped.startswith(("①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩")):
                    stripped = stripped[2:].strip()
                pending_lines.append(stripped)
        if current_cat and pending_lines and form_data["problems"].get(current_cat, "") == "":
            combined = "\n".join(pending_lines).strip()
            if combined and combined != "无":
                form_data["problems"][current_cat] = combined

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


def format_numbered_items(items):
    """生成报告中的序号列表。"""
    return [f"\t{chr(9311 + i)} {item}" for i, item in enumerate(items, 1)]


def calculate_time_periods(time_periods):
    """计算时间段总分钟数和展示文本。"""
    total_minutes = 0
    time_display_parts = []
    for p in time_periods:
        try:
            start_hour, start_minute = [int(part) for part in p["start"].split(":")]
            end_hour, end_minute = [int(part) for part in p["end"].split(":")]
        except (KeyError, TypeError, ValueError):
            continue

        start_min = start_hour * 60 + start_minute
        end_min = end_hour * 60 + end_minute
        if end_min > start_min:
            total_minutes += end_min - start_min
        time_display_parts.append(f"{p['start']}-{p['end']}")

    return total_minutes, time_display_parts


def generate_report_content(date_str, lines, time_periods, work_order, today_plans,
                           actual_scenes, processes, problems, todo_item,
                           test_results, completions, next_plan_scene, next_plan_processes, coordination):
    total_minutes, time_display_parts = calculate_time_periods(time_periods)

    total_hours = total_minutes / 60.0
    time_display = f"{total_hours:.1f}小时（{', '.join(time_display_parts)}）" if time_display_parts else f"{total_hours:.1f}小时"

    content_parts = []
    content_parts.append(f"【日期】{date_str}")

    if len(today_plans) == 1:
        content_parts.append(f"【今日计划】{today_plans[0]}")
    elif len(today_plans) > 1:
        content_parts.append("【今日计划】")
        content_parts.extend(format_numbered_items(today_plans))
    else:
        content_parts.append("【今日计划】")

    content_parts.append(f"【测试总时长】{time_display}")

    if len(actual_scenes) == 1:
        content_parts.append(f"【实际场景】{actual_scenes[0]}")
    elif len(actual_scenes) > 1:
        content_parts.append("【实际场景】")
        content_parts.extend(format_numbered_items(actual_scenes))
    else:
        content_parts.append("【实际场景】")

    content_parts.append(f"【工单】{work_order if work_order else '无'}")

    if len(processes) == 1:
        content_parts.append(f"【流程】{processes[0]}")
    elif len(processes) > 1:
        content_parts.append("【流程】")
        content_parts.extend(format_numbered_items(processes))
    else:
        content_parts.append("【流程】")

    content_parts.append("【问题汇总】")
    for cat in CATEGORIES:
        content = problems.get(cat, "").strip()
        if not content or content == "无":
            content_parts.append(f"\t{cat}：无")
        else:
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            if len(lines) == 1:
                content_parts.append(f"\t{cat}：{lines[0]}")
            else:
                content_parts.append(f"\t{cat}：")
                content_parts.extend(format_numbered_items(lines))

    content_parts.append(f"【待办项】{todo_item if todo_item else '无'}")

    if len(test_results) == 1:
        content_parts.append(f"【测试结果】{test_results[0]}")
    elif len(test_results) > 1:
        content_parts.append("【测试结果】")
        content_parts.extend(format_numbered_items(test_results))
    else:
        content_parts.append("【测试结果】")

    if len(completions) == 1:
        content_parts.append(f"【今日计划实际是否完成】{completions[0]}")
    elif len(completions) > 1:
        content_parts.append("【今日计划实际是否完成】")
        content_parts.extend(format_numbered_items(completions))
    else:
        content_parts.append("【今日计划实际是否完成】")

    content_parts.append("【明日计划】")
    content_parts.append(f"测试场景：{next_plan_scene if next_plan_scene else ''}")

    if next_plan_processes:
        content_parts.append("明细流程：")
        content_parts.extend(format_numbered_items(next_plan_processes))

    content_parts.append(f"需要协调事项：{coordination if coordination else '无'}")

    return "\n".join(content_parts)


def render_report_form(report_data=None, mode="create", original_filename=None):
    is_edit = mode == "edit"
    title = "✏️ 编辑报告" if is_edit else "📝 新建报告"
    form_key = f"{mode}:{original_filename or 'new'}"

    draft_key = f"draft_{form_key}"

    if is_edit and report_data:
        form_data = parse_report_to_form(report_data)
        filename = original_filename or report_data.get("文件名", "")
        if draft_key in st.session_state:
            saved = st.session_state[draft_key]
            if isinstance(saved, dict):
                form_data = saved
    else:
        if draft_key in st.session_state and isinstance(st.session_state[draft_key], dict):
            form_data = st.session_state[draft_key]
            form_data["report_date"] = datetime.now().date()
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

    if st.session_state.get("report_form_key") != form_key:
        st.session_state.report_form_key = form_key
        st.session_state.time_periods = form_data.get("time_periods", [{"start": "09:30", "end": "12:00"}])

    col_date, col_lines = st.columns([1, 2])
    with col_date:
        if is_edit and form_data.get("report_date"):
            try:
                default_date = pd.to_datetime(form_data["report_date"]).date()
            except (TypeError, ValueError):
                default_date = datetime.now().date()
        else:
            default_date = form_data.get("report_date", datetime.now().date())
        if isinstance(default_date, str):
            default_date = datetime.now().date()
        report_date = st.date_input("日期", value=default_date, format="YYYY-MM-DD")

    with col_lines:
        raw_defaults = form_data.get("selected_lines", [])
        valid_defaults = [x for x in raw_defaults if x in LINE_OPTIONS]
        if not valid_defaults and raw_defaults:
            for d in raw_defaults:
                matches = [opt for opt in LINE_OPTIONS if d in opt or opt in d]
                valid_defaults.extend(matches)
        valid_defaults = list(dict.fromkeys(valid_defaults))
        selected_lines = st.multiselect("线体", options=LINE_OPTIONS, default=valid_defaults)

    st.markdown("##### 测试时间段")

    if "time_periods" not in st.session_state:
        init_periods = form_data.get("time_periods", [{"start": "09:30", "end": "12:00"}])
        st.session_state.time_periods = init_periods

    if st.button("➕ 添加时间段"):
        st.session_state.time_periods.append({"start": "14:30", "end": "18:00"})
        st.rerun()

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
        except (TypeError, ValueError):
            start_default = datetime.strptime("09:30", "%H:%M").time()
        try:
            end_default = datetime.strptime(p.get("end", "12:00"), "%H:%M").time()
        except (TypeError, ValueError):
            end_default = datetime.strptime("12:00", "%H:%M").time()

        with cols[0]:
            start_time = st.time_input(f"开始{i}", value=start_default, key=f"{form_key}_time_start_{i}")
        with cols[2]:
            end_time = st.time_input(f"结束{i}", value=end_default, key=f"{form_key}_time_end_{i}")
        with cols[3]:
            if len(time_periods) > 1 and st.button("❌", key=f"del_time_{i}", help="删除"):
                st.session_state.time_periods.pop(i)
                st.rerun()

        new_periods.append({
            "start": start_time.strftime("%H:%M") if hasattr(start_time, 'strftime') else str(start_time)[:5],
            "end": end_time.strftime("%H:%M") if hasattr(end_time, 'strftime') else str(end_time)[:5]
        })

    time_periods = new_periods

    total_minutes, time_display_parts = calculate_time_periods(time_periods)

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
    optional_cat = "生产/工艺"
    for cat in CATEGORIES:
        val = form_data["problems"].get(cat, "")
        if cat == optional_cat and not val:
            continue
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

    with st.expander("👁️ 预览报告内容", expanded=False):
        preview_date = report_date.strftime("%Y-%m-%d")
        preview_content = generate_report_content(
            preview_date, selected_lines, time_periods, work_order,
            today_plans, actual_scenes, processes, problems, todo_item,
            test_results, completions, next_plan_scene, next_plan_processes, coordination
        )
        st.text_area("报告预览", value=preview_content, height=400, label_visibility="collapsed", disabled=True)

    col_back, col_save = st.columns(2)

    with col_back:
        if is_edit:
            if st.button("← 返回报告列表", width='stretch'):
                return "back"
        else:
            if st.button("← 返回Dashboard", width='stretch'):
                return "back"

    with col_save:
        submit_text = "💾 保存修改" if is_edit else "💾 生成报告"
        submitted = st.button(submit_text, width='stretch', type="primary")

        if submitted:
            errors = []
            warnings = []

            if not selected_lines:
                errors.append("请至少选择一个线体")
            if total_hours <= 0:
                errors.append("测试总时长必须大于 0")
            for i, p in enumerate(time_periods):
                try:
                    sh, sm = [int(x) for x in p["start"].split(":")]
                    eh, em = [int(x) for x in p["end"].split(":")]
                    if eh * 60 + em <= sh * 60 + sm:
                        errors.append(f"时间段 {i+1}：结束时间必须晚于开始时间")
                except (ValueError, KeyError):
                    errors.append(f"时间段 {i+1}：时间格式无效")
            if not today_plans:
                warnings.append("今日计划未填写")
            if not actual_scenes:
                warnings.append("实际场景未填写")
            if not problems or all(not v for v in problems.values()):
                warnings.append("问题汇总未填写")
            if not test_results:
                warnings.append("测试结果未填写")

            if warnings and not errors:
                for w in warnings:
                    st.warning(f"⚠️ {w}")

            if errors:
                for e in errors:
                    st.error(f"❌ {e}")
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
                    REPORT_DIR.mkdir(exist_ok=True)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    lines_str = ", ".join(selected_lines)
                    report_db.report_to_db(save_filename, date_str, lines_str, content)

                    if draft_key in st.session_state:
                        del st.session_state[draft_key]

                    st.success(f"✅ {'报告已保存' if is_edit else '报告已生成'}：{save_filename}")
                    st.balloons()
                    return save_filename
                except Exception as e:
                    st.error(f"❌ 保存失败：{e}")
    if not is_edit:
        st.session_state[draft_key] = {
            "report_date": report_date,
            "selected_lines": selected_lines,
            "time_periods": time_periods,
            "work_order": work_order,
            "today_plans": today_plans,
            "actual_scenes": actual_scenes,
            "processes": processes,
            "problems": problems,
            "todo_item": todo_item,
            "test_results": test_results,
            "completions": completions,
            "next_plan_scene": next_plan_scene,
            "next_plan_processes": next_plan_processes,
            "coordination": coordination,
        }

    return None
