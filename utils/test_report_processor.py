import re
import pandas as pd
from pathlib import Path
from utils import report_db


class TestReportProcessor:
    """自动化测试报告处理器 - 新版格式"""

    REPORT_DIR = Path("report")

    CATEGORIES = ["投收板机", "自动化物流（海康）", "主线设备", "软件集成（SIE）", "生产/工艺", "生产", "工艺", "维护", "IT"]
    KNOWN_LINES = ["VCP1", "VCP2", "PLB"]

    def __init__(self, report_dir=None):
        if report_dir:
            self.REPORT_DIR = Path(report_dir)

    def parse_report(self, file_path: Path) -> dict:
        """解析单个测试报告文件"""
        content = file_path.read_text(encoding="utf-8")
        line_text = self._extract_line_from_filename(file_path.name)

        result = {
            "文件名": file_path.name,
            "日期": self._extract_date(content, file_path.name),
            "线体": line_text,
            "线体列表": self.split_line_names(line_text),
            "今日计划": self._extract_field(content, "今日计划"),
            "测试总时长": self._extract_field(content, "测试总时长"),
            "实际场景": self._extract_field(content, "实际场景"),
            "工单": self._extract_field(content, "工单"),
            "流程": self._extract_field(content, "流程"),
            "问题汇总": self._extract_field(content, "问题汇总"),
            "待办项": self._extract_field(content, "待办项"),
            "测试结果": self._extract_field(content, "测试结果"),
            "计划完成情况": self._extract_field(content, "今日计划实际是否完成"),
            "明日计划": self._extract_field(content, "明日计划"),
            "需要协调事项": self._extract_coordination(content),
        }

        result["问题列表"] = self._extract_problems_new(content, result["线体"])

        return result

    def _extract_date(self, content: str, fallback_filename: str = "") -> str:
        """提取日期"""
        match = re.search(r"【日期】(\d{4}-\d{2}-\d{2})", content)
        if match:
            return match.group(1)
        match = re.search(r"(\d{4}-\d{2}-\d{2})", fallback_filename)
        if match:
            return match.group(1)
        return ""

    def _extract_line_from_filename(self, filename: str) -> str:
        """从文件名提取线体"""
        filename_upper = filename.upper()
        lines = []
        for line in self.KNOWN_LINES:
            if line in filename_upper:
                lines.append(line)
        return ", ".join(lines) if lines else "其他"

    def split_line_names(self, line_text: str) -> list:
        """拆分逗号分隔的线体文本"""
        if not line_text:
            return []
        parts = [part.strip() for part in str(line_text).split(",") if part.strip()]
        unique_parts = []
        for part in parts:
            if part not in unique_parts:
                unique_parts.append(part)
        return unique_parts

    def _extract_field(self, content: str, field_name: str) -> str:
        """提取字段内容"""
        pattern = rf"【{field_name}】([\s\S]*?)(?=【|$)"
        match = re.search(pattern, content)
        if match:
            result = match.group(1)
            return result.strip() if result else ""
        return ""

    def _extract_coordination(self, content: str) -> str:
        """提取需要协调事项"""
        tomorrow_plan = self._extract_field(content, "明日计划")
        match = re.search(r"需要协调事项[:：](.+)", tomorrow_plan)
        if match:
            return match.group(1).strip()
        return "无"

    def _extract_problems_new(self, content: str, line_type: str) -> list:
        """提取问题列表（新版格式）"""
        problems = []
        problem_section = self._extract_field(content, "问题汇总")
        if not problem_section:
            return problems

        lines = problem_section.split("\n")
        current_module = None
        pending_texts = []

        def save_problem():
            nonlocal current_module, pending_texts
            if not current_module or not pending_texts:
                return
            combined = "\n".join(pending_texts).strip()
            if combined and combined != "无":
                problems.append({
                    "线体": line_type,
                    "来源": current_module,
                    "原始描述": combined,
                    "状态": self._extract_status(combined)
                })
            pending_texts = []

        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped:
                continue

            if stripped.startswith(("①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩")):
                if not current_module:
                    current_module = "其他"
                save_problem()
                pending_texts = [stripped]
                continue

            module_match = re.match(r"^(.+?)[：:]\s*(.*)$", stripped)
            if module_match and module_match.group(1).strip() in self.CATEGORIES:
                module_name = module_match.group(1).strip()
                text_after = module_match.group(2).strip()
                save_problem()
                current_module = module_name
                pending_texts = [text_after] if text_after and text_after != "无" else []
                continue

            if current_module:
                pending_texts.append(stripped)
            else:
                current_module = "其他"
                pending_texts = [stripped]

        save_problem()
        return problems

    def _extract_status(self, text: str) -> str:
        """从问题描述中提取状态"""
        if not text or text == "无":
            return "无"

        if any(k in text for k in ["已解决", "已完成", "已修复", "✅"]):
            return "已解决"
        if any(k in text for k in ["正在排查", "🔍"]):
            return "排查中"
        if any(k in text for k in ["待验证", "待调整", "待排查", "待确认", "待跟进", "⚠️", "🔁", "❌", "🛑", "待", "尚未", "未完成", "未测试", "占用", "阻塞"]):
            return "待处理"

        return "待处理"

    def process_all(self) -> pd.DataFrame:
        """处理所有报告，优先从数据库读取，fallback 到 txt 文件"""
        try:
            db_reports = report_db.get_all_reports()
        except Exception:
            db_reports = []

        if db_reports:
            rows = []
            for r in db_reports:
                parsed = self._parse_content(r.get("content", ""), r.get("filename", ""))
                parsed["文件名"] = r.get("filename", "")
                parsed["日期"] = r.get("date", "")
                parsed["线体"] = r.get("lines", "")
                rows.append(parsed)
            if rows:
                return pd.DataFrame(rows)

        if not self.REPORT_DIR.exists():
            return pd.DataFrame()

        report_db.migrate_from_txt(self.REPORT_DIR)

        reports = []
        for file in self.REPORT_DIR.glob("*.txt"):
            if "模板" in file.name:
                continue
            try:
                report = self.parse_report(file)
                reports.append(report)
            except Exception as e:
                print(f"Error parsing {file.name}: {e}")

        if not reports:
            return pd.DataFrame()

        return pd.DataFrame(reports)

    def _parse_content(self, content: str, filename: str) -> dict:
        """从数据库内容解析报告字段"""
        result = {
            "文件名": filename,
            "日期": "",
            "线体": "",
            "今日计划": self._extract_field(content, "今日计划"),
            "测试总时长": self._extract_field(content, "测试总时长"),
            "实际场景": self._extract_field(content, "实际场景"),
            "工单": self._extract_field(content, "工单"),
            "流程": self._extract_field(content, "流程"),
            "问题汇总": self._extract_field(content, "问题汇总"),
            "待办项": self._extract_field(content, "待办项"),
            "测试结果": self._extract_field(content, "测试结果"),
            "计划完成情况": self._extract_field(content, "今日计划实际是否完成"),
            "明日计划": self._extract_field(content, "明日计划"),
            "需要协调事项": self._extract_coordination(content),
        }

        result["线体列表"] = self.split_line_names(result.get("线体", ""))
        result["问题列表"] = self._extract_problems_new(content, result.get("线体", ""))

        date_match = re.search(r"【日期】(\d{4}-\d{2}-\d{2})", content)
        if date_match:
            result["日期"] = date_match.group(1)

        return result

    def get_problem_detail(self, df: pd.DataFrame) -> pd.DataFrame:
        """获取所有问题的扁平列表"""
        if df.empty:
            return pd.DataFrame()

        rows = []
        for _, row in df.iterrows():
            date = row.get("日期", "")
            for prob in row.get("问题列表", []):
                rows.append({
                    "日期": date,
                    "线体": prob.get("线体", ""),
                    "来源": prob.get("来源", "其他"),
                    "原始描述": prob.get("原始描述", ""),
                    "状态": prob.get("状态", "")
                })

        return pd.DataFrame(rows)

    def get_problem_stats(self, df: pd.DataFrame) -> dict:
        """获取问题统计"""
        if df.empty:
            return {}

        problems_df = self.get_problem_detail(df)
        if problems_df.empty:
            return {}

        total = len(problems_df)
        resolved = len(problems_df[problems_df["状态"] == "已解决"])
        pending = len(problems_df[problems_df["状态"] == "待处理"])
        investigating = len(problems_df[problems_df["状态"] == "排查中"])

        by_line = {}
        for line in ["VCP1", "VCP2", "PLB"]:
            line_df = problems_df[problems_df["线体"].str.contains(line, na=False)]
            by_line[line] = {
                "total": len(line_df),
                "resolved": len(line_df[line_df["状态"] == "已解决"]),
                "pending": len(line_df[line_df["状态"] == "待处理"]),
                "investigating": len(line_df[line_df["状态"] == "排查中"])
            }

        return {
            "total": total,
            "resolved": resolved,
            "pending": pending,
            "investigating": investigating,
            "by_line": by_line
        }

    def get_daily_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """获取每日问题统计"""
        if df.empty:
            return pd.DataFrame()

        problems_df = self.get_problem_detail(df)
        if problems_df.empty:
            return pd.DataFrame()

        daily = problems_df.groupby("日期").size().reset_index(name="问题数")
        daily_r = problems_df[problems_df["状态"] == "已解决"].groupby("日期").size().reset_index(name="已解决数")
        daily_p = problems_df[problems_df["状态"] == "待处理"].groupby("日期").size().reset_index(name="待处理数")

        result = daily.merge(daily_r, on="日期", how="left")
        result = result.merge(daily_p, on="日期", how="left")
        result = result.fillna(0)

        return result
