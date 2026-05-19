"""问题追踪管理模块（SQLite 存储）"""
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from utils.config import Config

DB_PATH = Path("config/problems.db")
PROBLEM_STATES = ["待处理", "排查中", "已解决"]
_config = Config()


def _get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row):
    return dict(row) if row is not None else None


def _init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = _get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS problems (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            line TEXT NOT NULL,
            source TEXT DEFAULT '',
            status TEXT NOT NULL,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS problem_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT NOT NULL,
            status TEXT NOT NULL,
            time TEXT NOT NULL,
            note TEXT DEFAULT '',
            FOREIGN KEY(problem_id) REFERENCES problems(id)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_problem_status ON problems(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_problem_category ON problems(category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_problem_line ON problems(line)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_problem_date ON problems(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_problem_history_pid ON problem_history(problem_id)")
    conn.commit()
    conn.close()


def _migrate_from_json_if_needed():
    conn = _get_conn()
    count = conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
    conn.close()
    if count > 0:
        return

    old = _config.load_problems()
    if not old:
        return

    conn = _get_conn()
    for p in old:
        conn.execute(
            """
            INSERT OR REPLACE INTO problems
            (id, description, category, line, source, status, date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                p.get("id") or str(uuid.uuid4())[:8],
                p.get("description", ""),
                p.get("category", "其他"),
                p.get("line", ""),
                p.get("source", ""),
                p.get("status", "待处理"),
                p.get("date", datetime.now().strftime("%Y-%m-%d")),
                p.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M")),
                p.get("updated_at", datetime.now().strftime("%Y-%m-%d %H:%M")),
            ),
        )
        for h in p.get("history", []):
            conn.execute(
                "INSERT INTO problem_history (problem_id, status, time, note) VALUES (?, ?, ?, ?)",
                (
                    p.get("id") or str(uuid.uuid4())[:8],
                    h.get("status", p.get("status", "待处理")),
                    h.get("time", datetime.now().strftime("%Y-%m-%d %H:%M")),
                    h.get("note", ""),
                ),
            )
    conn.commit()
    conn.close()


def _attach_history(problem: dict) -> dict:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT status, time, note FROM problem_history WHERE problem_id = ? ORDER BY id ASC",
        (problem["id"],),
    ).fetchall()
    conn.close()
    problem["history"] = [dict(r) for r in rows]
    return problem


def load_problems() -> list:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM problems ORDER BY date DESC, updated_at DESC").fetchall()
    conn.close()
    return [_attach_history(dict(r)) for r in rows]


def count_problems(keyword: str = "", status: str = "", category: str = "", line: str = "") -> int:
    conn = _get_conn()
    query = "SELECT COUNT(*) FROM problems WHERE 1=1"
    params = []
    if keyword:
        query += " AND (LOWER(description) LIKE ? OR LOWER(category) LIKE ?)"
        kw = f"%{keyword.lower()}%"
        params.extend([kw, kw])
    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)
    if line:
        query += " AND line LIKE ?"
        params.append(f"%{line}%")
    total = conn.execute(query, params).fetchone()[0]
    conn.close()
    return total


def create_problem(description: str, category: str, line: str, source: str = "", date: str = "") -> dict:
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
        "history": [{"status": "待处理", "time": now, "note": "问题创建"}],
    }


def add_problem(description: str, category: str, line: str, source: str = "", date: str = "") -> dict:
    p = create_problem(description, category, line, source, date)
    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO problems (id, description, category, line, source, status, date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (p["id"], p["description"], p["category"], p["line"], p["source"], p["status"], p["date"], p["created_at"], p["updated_at"]),
    )
    conn.execute(
        "INSERT INTO problem_history (problem_id, status, time, note) VALUES (?, ?, ?, ?)",
        (p["id"], "待处理", p["created_at"], "问题创建"),
    )
    conn.commit()
    conn.close()
    return p


def search_problems(keyword: str = "", status: str = "", category: str = "", line: str = "", page: int = 1, page_size: int | None = None) -> list:
    conn = _get_conn()
    query = "SELECT * FROM problems WHERE 1=1"
    params = []
    if keyword:
        query += " AND (LOWER(description) LIKE ? OR LOWER(category) LIKE ?)"
        kw = f"%{keyword.lower()}%"
        params.extend([kw, kw])
    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)
    if line:
        query += " AND line LIKE ?"
        params.append(f"%{line}%")
    query += " ORDER BY date DESC, updated_at DESC"
    if page_size:
        offset = (page - 1) * page_size
        query += " LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_attach_history(dict(r)) for r in rows]


def update_problem_status(problem_id: str, new_status: str, note: str = "") -> bool:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = _get_conn()
    cur = conn.execute("UPDATE problems SET status = ?, updated_at = ? WHERE id = ?", (new_status, now, problem_id))
    if cur.rowcount <= 0:
        conn.close()
        return False
    conn.execute(
        "INSERT INTO problem_history (problem_id, status, time, note) VALUES (?, ?, ?, ?)",
        (problem_id, new_status, now, note or f"状态变更为 {new_status}"),
    )
    conn.commit()
    conn.close()
    return True


def delete_problem(problem_id: str) -> bool:
    conn = _get_conn()
    conn.execute("DELETE FROM problem_history WHERE problem_id = ?", (problem_id,))
    cur = conn.execute("DELETE FROM problems WHERE id = ?", (problem_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def get_pending_problems(days: int = 7, limit: int = 10) -> list:
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM problems WHERE status != '已解决' AND date >= ? ORDER BY date DESC, updated_at DESC LIMIT ?",
        (cutoff, limit),
    ).fetchall()
    conn.close()
    return [_attach_history(dict(r)) for r in rows]


def get_weekly_summary() -> dict:
    conn = _get_conn()
    problems = [dict(r) for r in conn.execute("SELECT * FROM problems").fetchall()]
    conn.close()

    total = len(problems)
    pending = len([p for p in problems if p.get("status") != "已解决"])
    resolved = len([p for p in problems if p.get("status") == "已解决"])
    investigating = len([p for p in problems if p.get("status") == "排查中"])

    by_category = {}
    by_line = {}
    for p in problems:
        cat = p.get("category", "其他")
        line = p.get("line", "未知")
        by_category[cat] = by_category.get(cat, 0) + 1
        by_line[line] = by_line.get(line, 0) + 1

    return {
        "total": total,
        "pending": pending,
        "resolved": resolved,
        "investigating": investigating,
        "by_category": by_category,
        "by_line": by_line,
        "recent_pending": get_pending_problems(days=7, limit=10),
    }


_init_db()
_migrate_from_json_if_needed()
