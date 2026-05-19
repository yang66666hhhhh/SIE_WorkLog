"""测试报告格式定义与辅助函数。

后续如果测试报告字段名、问题模块、序号规则变化，优先只改这里。
"""
import re

REPORT_CATEGORIES = [
    "投收板机",
    "自动化物流（海康）",
    "主线设备",
    "软件集成（SIE）",
    "生产/工艺",
    "生产",
    "工艺",
    "维护",
    "IT",
]

REPORT_PROBLEM_MODULES = REPORT_CATEGORIES + ["其他"]
NUMBERED_MARKERS = ("①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩")

FIELD_LABELS = {
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
}


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
    categories = categories or REPORT_CATEGORIES
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
