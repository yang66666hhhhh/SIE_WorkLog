"""联调总结新建/编辑表单页"""
import streamlit as st
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import report_db
from utils.test_report_format import (
    build_issue_labels,
    get_issue_keys,
    get_issue_label_map,
    TEMPLATE_TYPES,
)
from utils.styles import inject_global_css

st.set_page_config(
    page_title="联调总结",
    layout="wide",
    page_icon="📝",
    menu_items=None,
)
inject_global_css()

TEMPLATE_TYPE = "joint_debug_summary"
REPORT_DIR = Path("report/joint_debug")


def _default_date():
    return datetime.now().strftime("%Y-%m-%d")


def _fmt_short(d):
    if not d:
        return "XX/XX"
    parts = str(d).split("-")
    if len(parts) >= 3:
        return f"{parts[1]}/{parts[2]}"
    return "XX/XX"


def _build_labels(vendors):
    label_map = get_issue_label_map(TEMPLATE_TYPE)
    keys = get_issue_keys(TEMPLATE_TYPE)
    result = {}
    for key in keys:
        base = label_map.get(key, key)
        vendor = vendors.get(key, "")
        result[key] = f"{base}（{vendor}）" if vendor else base
    return result


def _generate_content(data):
    vendors = data.get("vendors", {})
    labels = _build_labels(vendors)
    keys = get_issue_keys(TEMPLATE_TYPE)

    d = _fmt_short(data.get("date", ""))
    plan_d = _fmt_short(data.get("plan_date", ""))
    actual_d = _fmt_short(data.get("actual_start_date", ""))
    line = data.get("line", "XXX")
    personnel = data.get("personnel", "")
    status = data.get("status", "")
    total_hours = data.get("total_hours", "")
    time_range = data.get("time_range", "")
    test_scene = data.get("test_scene", "")
    flow_detail = data.get("flow_detail", "")
    lot_numbers = data.get("lot_numbers", "")
    coordination = data.get("coordination", "")
    todo_today = data.get("todo_today", "无")
    next_line = data.get("next_line", "")
    next_scene = data.get("next_scene", "")
    next_flow = data.get("next_flow", "")
    todo_next = data.get("todo_next", "无")
    issues_today = data.get("issues_today", {})
    issues_next = data.get("issues_next", {})

    header = f"{{{d}}}{line}(数采，配方下发，自动化)测试进度汇总："
    if personnel:
        header += f"\n联调人员：{personnel}"

    out = [header]
    out.append(f"计划完成日期：{plan_d}")
    out.append(f"实际开始联调日期：{actual_d}")
    out.append(f"状态：{status}")
    out.append(f"生产线可测试时间总计{total_hours}小时：")
    out.append(f"明细时间段：{time_range}")
    out.append("")
    out.append(f"测试场景：{test_scene}")
    out.append("")
    out.append("明细流程：")
    out.append(flow_detail)
    out.append("")
    out.append("现场正式工单LOT号：")
    out.append(lot_numbers)
    out.append("")
    out.append("问题汇总：")
    for key in keys:
        label = labels.get(key, key)
        val = issues_today.get(key, "无")
        out.append(f"{label}：{val}")
    out.append(f"待办项：{todo_today or '无'}")
    out.append("")
    out.append(f"明日的测试计划：{next_line}(数采，配方下发，自动化)测试")
    out.append(f"测试场景：{next_scene}")
    out.append("明细流程：")
    out.append(next_flow)
    out.append("")
    out.append(f"需要协调事项：{coordination}")
    for key in keys:
        label = labels.get(key, key)
        val = issues_next.get(key, "无")
        out.append(f"{label}：{val}")
    out.append(f"待办项：{todo_next or '无'}")
    return "\n".join(out)


def _collect_form(vendors):
    keys = get_issue_keys(TEMPLATE_TYPE)
    issues_today = {}
    issues_next = {}
    for key in keys:
        issues_today[key] = st.session_state.get(f"issue_today_{key}", "无")
        issues_next[key] = st.session_state.get(f"issue_next_{key}", "无")
    return {
        "vendors": vendors,
        "issues_today": issues_today,
        "issues_next": issues_next,
    }


def _make_filename(date_str, line):
    date_part = date_str.replace("-", "") if date_str else "nodate"
    line_slug = line.replace(" ", "_") if line else "xxx"
    return f"JD_{date_part}_{line_slug}.txt"


# =====================
# Main
# =====================
st.title("📝 联调总结")

mode = st.session_state.get("joint_debug_mode", "create")
edit_filename = st.session_state.get("joint_debug_edit_file", "")

if mode == "edit" and edit_filename:
    report = report_db.get_report_by_filename(edit_filename)
    if report:
        raw_meta = report.get("metadata_json", "{}")
        try:
            edit_data = json.loads(raw_meta)
        except Exception:
            edit_data = {}
        edit_data["filename"] = edit_filename
        edit_data["content"] = report.get("content", "")
    else:
        edit_data = {}
else:
    edit_data = {}
    mode = "create"

is_edit = mode == "edit"

col_form, col_right = st.columns([3, 2])

with col_form:
    with st.form("joint_debug_form", clear_on_submit=False):
        c_top = st.columns(3)
        with c_top[0]:
            date_val = edit_data.get("date", _default_date())[:10] if edit_data.get("date") else _default_date()
            try:
                default_d = datetime.strptime(date_val, "%Y-%m-%d").date()
            except Exception:
                default_d = datetime.now().date()
            date = st.date_input("日期", value=default_d, format="YYYY-MM-DD")
        with c_top[1]:
            actual_val = edit_data.get("actual_start_date", _default_date())[:10] if edit_data.get("actual_start_date") else _default_date()
            try:
                default_as = datetime.strptime(actual_val, "%Y-%m-%d").date()
            except Exception:
                default_as = datetime.now().date()
            actual_start = st.date_input("实际开始联调日期", value=default_as, format="YYYY-MM-DD")
        with c_top[2]:
            plan_val = edit_data.get("plan_date", _default_date())[:10] if edit_data.get("plan_date") else _default_date()
            try:
                default_p = datetime.strptime(plan_val, "%Y-%m-%d").date()
            except Exception:
                default_p = datetime.now().date()
            plan_date = st.date_input("计划完成日期", value=default_p, format="YYYY-MM-DD")

        line_opts = ["内层前处理八线", "内层前处理七线", "其他"]
        default_line = edit_data.get("line", "内层前处理八线") if edit_data else "内层前处理八线"
        line_idx = line_opts.index(default_line) if default_line in line_opts else 0
        line = st.selectbox("线体", options=line_opts, index=line_idx)

        personnel = st.text_input("联调人员", value=edit_data.get("personnel", "") if edit_data else "")

        c_vendor = st.columns(3)
        with c_vendor[0]:
            vm = st.text_input("收放板机厂家", value=edit_data.get("vendors", {}).get("machine", "成泰") if edit_data else "成泰")
        with c_vendor[1]:
            vl = st.text_input("自动化物流厂家", value=edit_data.get("vendors", {}).get("logistics", "海康") if edit_data else "海康")
        with c_vendor[2]:
            vma = st.text_input("主线设备厂家", value=edit_data.get("vendors", {}).get("main", "") if edit_data else "")

        c_vendor2 = st.columns(2)
        with c_vendor2[0]:
            vs = st.text_input("软件集成厂家", value=edit_data.get("vendors", {}).get("sie", "") if edit_data else "")
        with c_vendor2[1]:
            vo = st.text_input("其他厂家", value=edit_data.get("vendors", {}).get("other", "") if edit_data else "")

        vendors = {"machine": vm, "logistics": vl, "main": vma, "sie": vs, "other": vo}

        c_status = st.columns([2, 1, 1])
        with c_status[0]:
            status_opts = ["测试中，完成", "测试中", "测试中，部分完成", "已完成"]
            default_status = edit_data.get("status", "测试中，完成") if edit_data else "测试中，完成"
            status_idx = status_opts.index(default_status) if default_status in status_opts else 0
            status = st.selectbox("状态", options=status_opts, index=status_idx)
        with c_status[1]:
            total_hours = st.text_input("可测试时间总计（小时）", value=edit_data.get("total_hours", "3.5") if edit_data else "3.5")
        with c_status[2]:
            time_range = st.text_input("明细时间段", value=edit_data.get("time_range", "14:30 - 18:00") if edit_data else "14:30 - 18:00")

        test_scene = st.text_area(
            "测试场景",
            value=edit_data.get("test_scene", "（正式环境）内层前处理八线放板机全流程") if edit_data else "（正式环境）内层前处理八线放板机全流程",
            height=60,
        )
        flow_detail = st.text_area(
            "明细流程",
            value=edit_data.get("flow_detail", "设备叫料，AGV送料，AGV安全交互，配方下发，放板请求，TrackIn，退空载，AGV取空载，AGV送空载入线边仓全流程") if edit_data
            else "设备叫料，AGV送料，AGV安全交互，配方下发，放板请求，TrackIn，退空载，AGV取空载，AGV送空载入线边仓全流程",
            height=80,
        )
        lot_numbers = st.text_area(
            "现场正式工单LOT号",
            value=edit_data.get("lot_numbers", "D626051101480、D626051101481；总计960PCS") if edit_data
            else "D626051101480、D626051101481；总计960PCS",
            height=60,
        )

        st.markdown("**今日问题汇总**")
        keys = get_issue_keys(TEMPLATE_TYPE)
        labels = _build_labels(vendors)
        issues_today = {}
        for key in keys:
            label = labels.get(key, key)
            default_val = "无"
            if edit_data and edit_data.get("issues_today"):
                default_val = edit_data["issues_today"].get(key, "无")
            issues_today[key] = st.text_input(label, value=default_val, key=f"jt_{key}")

        todo_today = st.text_input(
            "待办项",
            value=edit_data.get("todo_today", "无") if edit_data else "无",
        )

        st.markdown("---")
        st.markdown("**明日测试计划**")
        next_line = st.text_input(
            "明日测试线体",
            value=edit_data.get("next_line", "内层前处理八线") if edit_data else "内层前处理八线",
        )
        next_scene = st.text_area(
            "明日测试场景",
            value=edit_data.get("next_scene", "内层前处理八线收放板机全流程测试") if edit_data else "内层前处理八线收放板机全流程测试",
            height=60,
        )
        next_flow = st.text_area(
            "明日明细流程",
            value=edit_data.get("next_flow", "放板机：设备叫料，AGV送料，AGV安全交互，配方下发，放板请求，TrackIn，退空载，AGV取空载，AGV送空载入线边仓全流程\n收板机：叫空载，AGV安全交互，接收批次配方信息，TrackOut，退满载，AGV取满载，AGV送满载入库") if edit_data
            else "放板机：设备叫料，AGV送料，AGV安全交互，配方下发，放板请求，TrackIn，退空载，AGV取空载，AGV送空载入线边仓全流程\n收板机：叫空载，AGV安全交互，接收批次配方信息，TrackOut，退满载，AGV取满载，AGV送满载入库",
            height=100,
        )
        coordination = st.text_input(
            "需要协调事项",
            value=edit_data.get("coordination", "无") if edit_data else "无",
        )

        st.markdown("**明日问题预计**")
        issues_next = {}
        for key in keys:
            label = labels.get(key, key)
            default_val = "无"
            if edit_data and edit_data.get("issues_next"):
                default_val = edit_data["issues_next"].get(key, "无")
            issues_next[key] = st.text_input(f"明日{label}", value=default_val, key=f"jn_{key}")

        todo_next = st.text_input(
            "明日待办项",
            value=edit_data.get("todo_next", "无") if edit_data else "无",
        )

        st.markdown("---")
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if is_edit:
                submitted = st.form_submit_button("💾 保存修改", use_container_width=True, type="primary")
            else:
                submitted = st.form_submit_button("💾 生成并保存", use_container_width=True, type="primary")
        with c_btn2:
            if is_edit:
                if st.form_submit_button("← 返回列表", use_container_width=True):
                    st.session_state.joint_debug_mode = "create"
                    st.session_state.joint_debug_edit_file = ""
                    st.rerun()

        if submitted:
            form_data = {
                "date": date.strftime("%Y-%m-%d"),
                "actual_start_date": actual_start.strftime("%Y-%m-%d"),
                "plan_date": plan_date.strftime("%Y-%m-%d"),
                "line": line,
                "personnel": personnel,
                "vendors": vendors,
                "status": status,
                "total_hours": total_hours,
                "time_range": time_range,
                "test_scene": test_scene,
                "flow_detail": flow_detail,
                "lot_numbers": lot_numbers,
                "issues_today": issues_today,
                "todo_today": todo_today,
                "next_line": next_line,
                "next_scene": next_scene,
                "next_flow": next_flow,
                "coordination": coordination,
                "issues_next": issues_next,
                "todo_next": todo_next,
            }
            content = _generate_content(form_data)
            filename = _make_filename(form_data["date"], form_data["line"])

            if is_edit and edit_filename:
                save_filename = edit_filename
            else:
                save_filename = filename

            metadata_json = json.dumps(form_data, ensure_ascii=False)
            report_db.report_to_db(
                filename=save_filename,
                date=form_data["date"],
                lines=form_data["line"],
                content=content,
                template_type=TEMPLATE_TYPE,
                metadata_json=metadata_json,
            )

            REPORT_DIR.mkdir(exist_ok=True)
            (REPORT_DIR / save_filename).write_text(content, encoding="utf-8")

            st.success(f"✅ 已保存：{save_filename}")
            if not is_edit:
                st.balloons()
            st.session_state.joint_debug_mode = "create"
            st.session_state.joint_debug_edit_file = ""
            st.rerun()

# =====================
# Right panel: Preview + History
# =====================
with col_right:
    st.markdown("**📄 预览**")
    preview_data = {
        "date": date.strftime("%Y-%m-%d") if 'date' in locals() else _default_date(),
        "actual_start_date": actual_start.strftime("%Y-%m-%d") if 'actual_start' in locals() else _default_date(),
        "plan_date": plan_date.strftime("%Y-%m-%d") if 'plan_date' in locals() else _default_date(),
        "line": line if 'line' in locals() else "XXX",
        "personnel": personnel if 'personnel' in locals() else "",
        "vendors": vendors if 'vendors' in locals() else {},
        "status": status if 'status' in locals() else "",
        "total_hours": total_hours if 'total_hours' in locals() else "",
        "time_range": time_range if 'time_range' in locals() else "",
        "test_scene": test_scene if 'test_scene' in locals() else "",
        "flow_detail": flow_detail if 'flow_detail' in locals() else "",
        "lot_numbers": lot_numbers if 'lot_numbers' in locals() else "",
        "coordination": coordination if 'coordination' in locals() else "",
        "todo_today": todo_today if 'todo_today' in locals() else "无",
        "next_line": next_line if 'next_line' in locals() else "",
        "next_scene": next_scene if 'next_scene' in locals() else "",
        "next_flow": next_flow if 'next_flow' in locals() else "",
        "todo_next": todo_next if 'todo_next' in locals() else "无",
        "issues_today": issues_today if 'issues_today' in locals() else {},
        "issues_next": issues_next if 'issues_next' in locals() else {},
    }
    preview_text = _generate_content(preview_data)
    st.text_area("预览内容", value=preview_text, height=400, disabled=True, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**📚 历史联调总结**")

    all_reports = report_db.get_all_reports(template_type=TEMPLATE_TYPE)
    if not all_reports:
        st.info("暂无联调总结记录")
    else:
        for r in all_reports[:20]:
            with st.container():
                col_r1, col_r2 = st.columns([4, 1])
                with col_r1:
                    st.markdown(f"**📅 {r.get('date', '')}** · {r.get('lines', '')}")
                    meta_raw = r.get("metadata_json", "{}")
                    try:
                        meta = json.loads(meta_raw)
                        st.caption(f"状态: {meta.get('status', '-')}")
                    except Exception:
                        pass
                with col_r2:
                    if st.button("✏️", key=f"edit_{r['filename']}", help="编辑"):
                        st.session_state.joint_debug_mode = "edit"
                        st.session_state.joint_debug_edit_file = r["filename"]
                        st.rerun()
                    if st.button("🗑️", key=f"del_{r['filename']}", help="删除"):
                        report_db.delete_report(r["filename"])
                        st.toast("已删除")
                        st.rerun()
                st.divider()
