"""问题追踪管理模块"""
import uuid
from datetime import datetime, timedelta
from utils.config import Config

_config = Config()

PROBLEM_STATES = ["待处理", "排查中", "已解决"]


def load_problems() -> list:
    return _config.load_problems()


def save_problems(problems: list):
    _config.save_problems(problems)


def create_problem(description: str, category: str, line: str, source: str = "", date: str = "") -> dict:
    """创建新问题"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return {
        "id": str(uuid.uuid4())[:8],
        "description": description,
        "category": category,
        "line": line,
        "source": source,
        "status": "待处理",
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "created_at": now,
        "updated_at": now,
        "history": [{
            "status": "待处理",
            "time": now,
            "note": "问题创建"
        }]
    }


def update_problem_status(problem_id: str, new_status: str, note: str = "") -> bool:
    """更新问题状态"""
    problems = load_problems()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    for p in problems:
        if p["id"] == problem_id:
            p["status"] = new_status
            p["updated_at"] = now
            p["history"].append({
                "status": new_status,
                "time": now,
                "note": note or f"状态变更为 {new_status}"
            })
            save_problems(problems)
            return True
    return False


def delete_problem(problem_id: str) -> bool:
    """删除问题"""
    problems = load_problems()
    for i, p in enumerate(problems):
        if p["id"] == problem_id:
            problems.pop(i)
            save_problems(problems)
            return True
    return False


def add_problem(description: str, category: str, line: str, source: str = "", date: str = "") -> dict:
    """添加问题到问题库"""
    problems = load_problems()
    new_prob = create_problem(description, category, line, source, date)
    problems.insert(0, new_prob)
    save_problems(problems)
    return new_prob


def search_problems(keyword: str = "", status: str = "", category: str = "", line: str = "") -> list:
    """搜索问题"""
    problems = load_problems()
    results = problems
    if keyword:
        kw = keyword.lower()
        results = [p for p in results if kw in p.get("description", "").lower() or kw in p.get("category", "").lower()]
    if status:
        results = [p for p in results if p.get("status") == status]
    if category:
        results = [p for p in results if p.get("category") == category]
    if line:
        results = [p for p in results if line in p.get("line", "")]
    return results


def get_pending_problems(days: int = 7) -> list:
    """获取近 N 天未解决的问题"""
    problems = load_problems()
    pending = [p for p in problems if p.get("status") != "已解决"]
    return pending


def get_weekly_summary() -> dict:
    """获取本周问题汇总"""
    problems = load_problems()
    today = datetime.now()
    week_start = today.isoweekday()
    week_days = []
    for i in range(7):
        day = today - timedelta(days=today.isoweekday() - 1 - i)
        week_days.append(day.strftime("%Y-%m-%d"))

    total = len(problems)
    pending = len([p for p in problems if p.get("status") != "已解决"])
    resolved = len([p for p in problems if p.get("status") == "已解决"])
    investigating = len([p for p in problems if p.get("status") == "排查中"])

    by_category = {}
    for p in problems:
        cat = p.get("category", "其他")
        by_category[cat] = by_category.get(cat, 0) + 1

    by_line = {}
    for p in problems:
        line = p.get("line", "未知")
        by_line[line] = by_line.get(line, 0) + 1

    return {
        "total": total,
        "pending": pending,
        "resolved": resolved,
        "investigating": investigating,
        "by_category": by_category,
        "by_line": by_line,
        "recent_pending": [p for p in problems if p.get("status") != "已解决"][:10]
    }
