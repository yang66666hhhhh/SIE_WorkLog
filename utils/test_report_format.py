"""测试报告格式定义、版本解析与辅助函数。"""
import re
from copy import deepcopy

from utils.config import Config

NUMBERED_MARKERS = ("①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩")

REPORT_FORMATS = {
    "v1": {
        "categories": ["投收板机", "自动化物流（海康）", "主线设备", "软件集成（SIE）", "生产/工艺", "生产", "工艺", "维护", "IT"],
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
        "categories": ["投收板机", "自动化物流（海康）", "主线设备", "软件集成（SIE）", "生产/工艺", "生产", "工艺", "维护", "IT"],
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
}


def get_available_versions():
    return list(REPORT_FORMATS.keys())


def get_available_version_options():
    return get_available_versions() + ["custom"]


def load_active_report_format(version=None, custom_config=None):
    cfg = custom_config or Config().load_report_format_config()
    version = version or cfg.get("version", "v1")
    if version == "custom":
        base = deepcopy(REPORT_FORMATS["v1"])
    else:
        base = deepcopy(REPORT_FORMATS.get(version, REPORT_FORMATS["v1"]))

    custom_categories = cfg.get("custom_categories", [])
    custom_labels = cfg.get("custom_field_labels", {})
    if custom_categories:
        base["categories"] = custom_categories
    if custom_labels:
        base["field_labels"].update(custom_labels)
    base["problem_modules"] = base["categories"] + ["其他"]
    base["version"] = version
    return base


def get_categories(version=None, custom_config=None):
    return load_active_report_format(version=version, custom_config=custom_config)["categories"]


def get_problem_modules(version=None, custom_config=None):
    return load_active_report_format(version=version, custom_config=custom_config)["problem_modules"]


def get_field_labels(version=None, custom_config=None):
    return load_active_report_format(version=version, custom_config=custom_config)["field_labels"]


def get_format_option(name: str, default=None, version=None, custom_config=None):
    return load_active_report_format(version=version, custom_config=custom_config).get(name, default)


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
    labels = fmt["field_labels"]
    missing = []
    for label in labels.values():
        if f"【{label}】" not in content and label not in (labels["coordination"],):
            missing.append(label)
    return {"ok": len(missing) == 0, "missing_fields": missing, "version": fmt["version"]}


# backward-compatible exports (deprecated - loaded once at import time with v1 defaults)
REPORT_CATEGORIES = REPORT_FORMATS["v1"]["categories"]
REPORT_PROBLEM_MODULES = REPORT_FORMATS["v1"]["categories"] + ["其他"]
FIELD_LABELS = REPORT_FORMATS["v1"]["field_labels"]
