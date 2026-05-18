"""测试报告 SQLite 数据库模块"""
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

DB_PATH = Path("config/reports.db")
BACKUP_DIR = Path("config/backups")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            date TEXT,
            lines TEXT,
            content TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            id TEXT PRIMARY KEY,
            report_id INTEGER,
            description TEXT,
            category TEXT,
            line TEXT,
            source TEXT,
            status TEXT,
            original_text TEXT,
            created_at TEXT,
            FOREIGN KEY (report_id) REFERENCES reports(id)
        )
    """)
    conn.commit()
    conn.close()


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def report_to_db(filename: str, date: str, lines: str, content: str) -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    cur = conn.execute(
        "SELECT id FROM reports WHERE filename = ?", (filename,)
    )
    existing = cur.fetchone()
    if existing:
        conn.execute(
            "UPDATE reports SET date=?, lines=?, content=?, updated_at=? WHERE filename=?",
            (date, lines, content, now, filename)
        )
        report_id = existing["id"]
    else:
        cur = conn.execute(
            "INSERT INTO reports (filename, date, lines, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (filename, date, lines, content, now, now)
        )
        report_id = cur.lastrowid
    conn.commit()
    conn.close()
    return report_id


def get_all_reports() -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM reports ORDER BY date DESC, id DESC"
    ).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def get_report_by_filename(filename: str) -> dict:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM reports WHERE filename = ?", (filename,)
    ).fetchone()
    conn.close()
    return row_to_dict(row)


def get_report_by_id(report_id: int) -> dict:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM reports WHERE id = ?", (report_id,)
    ).fetchone()
    conn.close()
    return row_to_dict(row)


def search_reports(keyword: str = "", date_from: str = "", date_to: str = "", line: str = "") -> list:
    conn = get_conn()
    query = "SELECT * FROM reports WHERE 1=1"
    params = []
    if keyword:
        query += " AND (content LIKE ? OR lines LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date <= ?"
        params.append(date_to)
    if line:
        query += " AND lines LIKE ?"
        params.append(f"%{line}%")
    query += " ORDER BY date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def delete_report(filename: str) -> bool:
    conn = get_conn()
    conn.execute("DELETE FROM reports WHERE filename = ?", (filename,))
    conn.commit()
    affected = conn.total_changes > 0
    conn.close()
    return affected


def get_problems_by_report(report_id: int) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM problems WHERE report_id = ?", (report_id,)
    ).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def search_all_problems(keyword: str = "", status: str = "", category: str = "") -> list:
    conn = get_conn()
    query = "SELECT p.*, r.date, r.lines FROM problems p JOIN reports r ON p.report_id = r.id WHERE 1=1"
    params = []
    if keyword:
        query += " AND (p.description LIKE ? OR p.original_text LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if status:
        query += " AND p.status = ?"
        params.append(status)
    if category:
        query += " AND p.category = ?"
        params.append(category)
    query += " ORDER BY r.date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def migrate_from_txt(report_dir: Path = Path("report")):
    """从 txt 文件迁移到数据库"""
    if not report_dir.exists():
        return {"migrated": 0, "errors": []}

    init_db()
    errors = []
    migrated = 0

    for txt_file in report_dir.glob("*.txt"):
        try:
            content = txt_file.read_text(encoding="utf-8")
            filename = txt_file.name

            date = ""
            import re
            date_match = re.search(r"【日期】(\d{4}-\d{2}-\d{2})", content)
            if date_match:
                date = date_match.group(1)

            lines = ""
            for line_name in ["VCP1", "VCP2", "PLB", "镍钯金", "大族", "安美特"]:
                if line_name.lower() in filename.lower():
                    lines += line_name + ", "
            lines = lines.rstrip(", ")

            report_to_db(filename, date, lines, content)
            migrated += 1
        except Exception as e:
            errors.append(f"{txt_file.name}: {str(e)}")

    return {"migrated": migrated, "errors": errors}


def backup_db():
    """备份数据库到 backup 目录"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"reports_{timestamp}.db"
    shutil.copy2(DB_PATH, backup_path)

    for old_backup in sorted(BACKUP_DIR.glob("reports_*.db"))[:-10]:
        old_backup.unlink()

    return backup_path


def export_db_json() -> Path:
    """导出数据库为 JSON 文件"""
    conn = get_conn()
    reports = conn.execute("SELECT * FROM reports ORDER BY date DESC").fetchall()
    problems = conn.execute("SELECT * FROM problems").fetchall()
    conn.close()

    data = {
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reports": [row_to_dict(r) for r in reports],
        "problems": [row_to_dict(p) for p in problems]
    }

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    export_path = BACKUP_DIR / f"reports_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return export_path


def import_db_json(import_path: Path) -> dict:
    """从 JSON 文件导入数据库"""
    with open(import_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    init_db()
    conn = get_conn()
    imported_reports = 0
    imported_problems = 0

    for r in data.get("reports", []):
        try:
            conn.execute(
                """INSERT OR REPLACE INTO reports (filename, date, lines, content, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (r["filename"], r.get("date", ""), r.get("lines", ""),
                 r.get("content", ""), r.get("created_at", ""), r.get("updated_at", ""))
            )
            imported_reports += 1
        except Exception:
            pass

    for p in data.get("problems", []):
        try:
            conn.execute(
                """INSERT OR REPLACE INTO problems
                   (id, report_id, description, category, line, source, status, original_text, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (p["id"], p.get("report_id"), p.get("description", ""), p.get("category", ""),
                 p.get("line", ""), p.get("source", ""), p.get("status", ""),
                 p.get("original_text", ""), p.get("created_at", ""))
            )
            imported_problems += 1
        except Exception:
            pass

    conn.commit()
    conn.close()
    return {"reports": imported_reports, "problems": imported_problems}


init_db()
