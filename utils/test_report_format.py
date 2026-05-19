"""测试报告与联调总结格式定义、版本解析与辅助函数。"""
import re
import json
from copy import deepcopy

from utils.config import Config

NUMBERED_MARKERS = ("①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩")


REPORT_FORMATS = {
    "test_report": {
        "v1": {
            "categories": ["投收板机", "自动化物流（海康）", "主线设备", "软件集成（SIE）", "生产", "工艺", "维护", "IT"],
            "field_labels": {
                "date": "日期",
                "lines": "线体",
                "today_plan": "今日计划",
                "duration": "测试总时长",
                "actual_scene": "实际场景",
                "work_order": "工单",
                "process": "流程",
                "problem_summary": "问题汇总",
                "todo": "待办项",
                "test_result": "测试结果",
                "completion": "今日计划实际是否完成",
                "tomorrow_plan": "明日计划",
                "coordination": "需要协调事项",
            },
        },
        "v2": {
            "categories": ["投收板机", "自动化物流（海康）", "主线设备", "软件集成（SIE）", "生产", "工艺", "维护", "IT"],
            "field_labels": {
                "date": "日期",
                "lines": "线体",
                "today_plan": "今日计划",
                "duration": "测试总时长",
                "actual_scene": "实际场景",
                "work_order": "工单",
                "process": "流程",
                "problem_summary": "问题汇总",
                "todo": "待办项",
                "test_result": "测试结果",
                "completion": "今日计划实际是否完成",
                "tomorrow_plan": "明日计划",
                "coordination": "需要协调事项",
            },
            "number_prefix_required": True,
        },
    },
    "joint_debug_summary": {
        "v1": {
            "issue_keys": ["machine", "logistics", "main", "sie", "other", "production", "process", "maintenance"],
            "field_labels": {
                "date": "日期",
                "actual_start_date": "实际开始联调日期",
                "plan_date": "计划完成日期",
                "line": "线体",
                "status": "状态",
                "total_hours": "可测试时间总计",
                "time_range": "明细时间段",
                "test_scene": "测试场景",
                "flow_detail": "明细流程",
                "lot_numbers": "现场正式工单LOT号",
                "personnel": "联调人员",
                "coordination": "需要协调事项",
                "next_scene": "明日测试场景",
                "next_flow": "明日明细流程",
                "next_line": "明日测试线体",
            },
            "issue_label_map": {
                "machine": "投收板机",
                "logistics": "自动化物流（海康）",
                "main": "主线设备",
                "sie": "软件集成（SIE）",
                "other": "其他",
                "production": "生产",
                "process": "工艺",
                "maintenance": "维护",
            },
        },
        "v2": {
            "issue_keys": ["machine", "logistics", "main", "sie", "other", "production", "process", "maintenance"],
            "field_labels": {
                "date": "日期",
                "actual_start_date": "实际开始联调日期",
                "plan_date": "计划完成日期",
                "line": "线体",
                "status": "状态",
                "total_hours": "可测试时间总计",
                "time_range": "明细时间段",
                "test_scene": "测试场景",
                "flow_detail": "明细流程",
                "lot_numbers": "现场正式工单LOT号",
                "personnel": "联调人员",
                "coordination": "需要协调事项",
                "next_scene": "明日测试场景",
                "next_flow": "明日明细流程",
                "next_line": "明日测试线体",
            },
            "issue_label_map": {
                "machine": "投收板机",
                "logistics": "自动化物流（海康）",
                "main": "主线设备",
                "sie": "软件集成（SIE）",
                "other": "其他",
                "production": "生产",
                "process": "工艺",
                "maintenance": "维护",
            },
            "number_prefix_required": True,
        },
    },
}


TEMPLATE_TYPES = list(REPORT_FORMATS.keys())


def get_template_types():
    return TEMPLATE_TYPES


def get_available_versions(template_type="test_report"):
    if template_type not in REPORT_FORMATS:
        template_type = "test_report"
    return list(REPORT_FORMATS[template_type].keys())


def get_available_version_options(template_type="test_report"):
    return get_available_versions(template_type) + ["custom"]


def get_active_config_for_type(template_type):
    cfg = Config().load_report_format_config()
    if template_type not in cfg:
        cfg[template_type] = {"version": "v1", "custom_field_labels": {}, "custom_categories": []}
    return cfg[template_type]


def load_active_format_for_type(template_type, version=None, custom_config=None):
    cfg = custom_config or get_active_config_for_type(template_type)
    version = version or cfg.get("version", "v1")
    if version == "custom":
        base = deepcopy(REPORT_FORMATS[template_type]["v1"])
    else:
        base = deepcopy(REPORT_FORMATS[template_type].get(version, REPORT_FORMATS[template_type]["v1"]))
    custom_categories = cfg.get("custom_categories", [])
    custom_labels = cfg.get("custom_field_labels", {})
    if custom_categories:
        base["categories"] = custom_categories if "categories" in base else base.get("issue_keys", [])
    if custom_labels:
        base["field_labels"] = {**base.get("field_labels", {}), **custom_labels}
    base["version"] = version
    base["template_type"] = template_type
    return base


def load_active_report_format(version=None, custom_config=None):
    return load_active_format_for_type("test_report", version=version, custom_config=custom_config)


def get_categories(version=None, custom_config=None):
    return load_active_report_format(version=version, custom_config=custom_config).get("categories", [])


def get_problem_modules(version=None, custom_config=None):
    fmt = load_active_report_format(version=version, custom_config=custom_config)
    cats = fmt.get("categories", [])
    return cats + (["其他"] if cats else [])


def get_field_labels(version=None, custom_config=None):
    return load_active_report_format(version=version, custom_config=custom_config).get("field_labels", {})


def get_format_option(name: str, default=None, version=None, custom_config=None):
    return load_active_report_format(version=version, custom_config=custom_config).get(name, default)


def get_issue_keys(template_type="joint_debug_summary", version=None, custom_config=None):
    fmt = load_active_format_for_type(template_type, version=version, custom_config=custom_config)
    return fmt.get("issue_keys", [])


def get_issue_label_map(template_type="joint_debug_summary", version=None, custom_config=None):
    fmt = load_active_format_for_type(template_type, version=version, custom_config=custom_config)
    return fmt.get("issue_label_map", {})


def build_issue_labels(vendors: dict, template_type="joint_debug_summary", version=None, custom_config=None):
    label_map = get_issue_label_map(template_type, version=version, custom_config=custom_config)
    keys = get_issue_keys(template_type, version=version, custom_config=custom_config)
    result = {}
    for key in keys:
        base_label = label_map.get(key, key)
        vendor = vendors.get(key, "")
        if vendor:
            result[key] = f"{base_label}（{vendor}）"
        else:
            result[key] = base_label
    return result


def is_numbered_line(text: str) -> bool:
    return bool(text) and text.startswith(NUMBERED_MARKERS)


def strip_number_prefix(text: str) -> str:
    if not text:
        return ""
    return text[2:].strip() if is_numbered_line(text.strip()) else text.strip()


def split_line_names(value) -> list:
    if value is None:
        return []
    parts = [part.strip() for part in str(value).split(",") if part.strip()]
    unique_parts = []
    for part in parts:
        if part not in unique_parts:
            unique_parts.append(part)
    return unique_parts


def split_report_block_items(value) -> list:
    if value is None:
        return []
    items = []
    for raw_line in str(value).splitlines():
        line = raw_line.strip()
        if not line or line == "无":
            continue
        items.append(strip_number_prefix(line))
    return items


def parse_problem_summary_to_map(summary: str, categories=None) -> dict:
    categories = categories or get_categories()
    result = {cat: "" for cat in categories}
    if not summary:
        return result
    current_cat = None
    pending_lines = []
    for raw_line in str(summary).splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        cat_match = re.match(r"^([^：:]+)[：:]\s*(.*)$", stripped)
        if cat_match:
            cat_name = cat_match.group(1).strip()
            text = cat_match.group(2).strip()
            if cat_name in categories:
                if current_cat and pending_lines and not result.get(current_cat):
                    combined = "\n".join(pending_lines).strip()
                    if combined and combined != "无":
                        result[current_cat] = combined
                current_cat = cat_name
                pending_lines = [text] if text and text != "无" else []
                continue
        if current_cat and stripped != "无":
            pending_lines.append(strip_number_prefix(stripped))
    if current_cat and pending_lines and not result.get(current_cat):
        combined = "\n".join(pending_lines).strip()
        if combined and combined != "无":
            result[current_cat] = combined
    return result


def validate_report_content(content: str):
    fmt = load_active_report_format()
    labels = fmt.get("field_labels", {})
    missing = []
    coordination_label = labels.get("coordination", "需要协调事项")
    for key, label in labels.items():
        if key == "coordination":
            continue
        if f"【{label}】" not in content:
            missing.append(label)
    return {"ok": len(missing) == 0, "missing_fields": missing, "version": fmt.get("version", "v1")}


# backward-compatible exports
REPORT_CATEGORIES = REPORT_FORMATS["test_report"]["v1"]["categories"]
REPORT_PROBLEM_MODULES = REPORT_FORMATS["test_report"]["v1"]["categories"] + ["其他"]
FIELD_LABELS = REPORT_FORMATS["test_report"]["v1"]["field_labels"]
