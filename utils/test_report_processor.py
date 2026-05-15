import re
import pandas as pd
from pathlib import Path


class TestReportProcessor:
    """自动化测试报告处理器 - 新版"""

    REPORT_DIR = Path("report")

    LINE_TYPES = ["VCP1", "VCP2", "PLB"]

    def __init__(self, report_dir=None):
        if report_dir:
            self.REPORT_DIR = Path(report_dir)

    def parse_report(self, file_path: Path) -> dict:
        """解析单个测试报告文件"""
        content = file_path.read_text(encoding="utf-8")

        result = {
            "文件名": file_path.name,
            "日期": self._extract_date(file_path.name),
            "线体": self._extract_line_from_filename(file_path.name),
            "可测试时间": self._extract_test_time(content),
            "明细时间段": self._extract_time_detail(content),
            "测试结果": self._extract_test_result(content),
            "计划完成情况": self._extract_plan_completion(content),
            "明日/下周计划": self._extract_next_plan(content),
            "需要协调事项": self._extract_coordination(content),
        }

        result["问题列表"] = self._extract_problems(content, result["线体"])

        return result

    def _extract_date(self, filename: str) -> str:
        """提取日期，从文件名提取，格式：2026-05-12 或 05.12"""
        match = re.search(r"(\d{4})-(\d{2})-(\d{2})", filename)
        if match:
            return f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
        match = re.search(r"(\d+)\.(\d+)", filename)
        if match:
            return f"2026.{int(match.group(1)):02d}.{int(match.group(2)):02d}"
        return ""

    def _extract_line_from_filename(self, filename: str) -> str:
        """从文件名提取线体，格式：vcp1_vcp2_plb"""
        filename_upper = filename.upper()
        lines = []
        if "VCP1" in filename_upper:
            lines.append("VCP1")
        if "VCP2" in filename_upper:
            lines.append("VCP2")
        if "PLB" in filename_upper:
            lines.append("PLB")
        return ", ".join(lines) if lines else "其他"

    def _extract_test_time(self, content: str) -> float:
        """提取可测试时间"""
        match = re.search(r"【生产线可测试时间总计：(\d+\.?\d*)小时】", content)
        if match:
            return float(match.group(1))
        return 0.0

    def _extract_time_detail(self, content: str) -> str:
        """提取明细时间段"""
        match = re.search(r"明细时间段：(.+)", content)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_problems(self, content: str, line_type_from_filename: str) -> list:
        """提取问题列表，返回结构化问题数据"""
        problems = []
        match = re.search(r"【问题汇总】([\s\S]*?)(?=【测试结果】|【今日计划实际是否完成】|【明日的测试计划】|【下周的测试计划】|$)", content)
        if not match:
            return problems

        problem_block = match.group(1)
        lines = problem_block.split("\n")

        categories = ["投收板机", "自动化物流（海康）", "主线设备", "软件集成（SIE）",
                      "生产/工艺", "生产", "工艺", "维护", "IT", "待办项"]

        def is_category_line(line):
            for cat in categories:
                if line.startswith(cat):
                    return True, cat
            return False, None

        def clean_text(text):
            text = re.sub(r"^\d+[.)、]\s*", "", text)
            return text.strip()

        current_source = None
        pending_texts = []

        for line in lines:
            stripped = line.strip()
            is_cat, cat_name = is_category_line(stripped)

            if is_cat:
                if current_source and pending_texts:
                    combined = "\n".join(pending_texts).strip()
                    status = self._extract_status(combined) if combined != "无" else "无"
                    if not (current_source == "其他" and status == "无"):
                        problems.append({
                            "线体": line_type_from_filename,
                            "来源": current_source,
                            "原始描述": combined,
                            "状态": status
                        })
                    pending_texts = []

                colon_pos = stripped.find("：")
                if colon_pos == -1:
                    colon_pos = stripped.find(":")

                if colon_pos != -1:
                    text_after = stripped[colon_pos+1:].strip()
                    current_source = cat_name
                    if text_after:
                        pending_texts = [clean_text(text_after)]
                    else:
                        pending_texts = []
                else:
                    current_source = cat_name
                    pending_texts = []

            elif line.startswith("\t") or line.startswith("  "):
                cleaned = clean_text(stripped)
                if cleaned:
                    pending_texts.append(cleaned)

            elif stripped.startswith("①") or stripped.startswith("②") or stripped.startswith("③") or stripped.startswith("④") or stripped.startswith("⑤"):
                if current_source and pending_texts:
                    combined = "\n".join(pending_texts).strip()
                    status = self._extract_status(combined) if combined != "无" else "无"
                    if not (current_source == "其他" and status == "无"):
                        problems.append({
                            "线体": line_type_from_filename,
                            "来源": current_source,
                            "原始描述": combined,
                            "状态": status
                        })
                current_source = "其他"
                pending_texts = [clean_text(stripped)]

            else:
                if current_source and pending_texts:
                    combined = " ".join(pending_texts).strip()
                    status = self._extract_status(combined) if combined != "无" else "无"
                    if not (current_source == "其他" and status == "无"):
                        problems.append({
                            "线体": line_type_from_filename,
                            "来源": current_source,
                            "原始描述": combined,
                            "状态": status
                        })
                current_source = "其他"
                pending_texts = [clean_text(stripped)] if stripped and stripped != "无" else []

        if current_source and pending_texts:
            combined = "\n".join(pending_texts).strip()
            status = self._extract_status(combined) if combined != "无" else "无"
            if not (current_source == "其他" and status == "无"):
                problems.append({
                    "线体": line_type_from_filename,
                    "来源": current_source,
                    "原始描述": combined,
                    "状态": status
                })

        return problems

    def _extract_line_type(self, text: str) -> str:
        """从问题描述中提取线体"""
        text_upper = text.upper()
        found = []
        if "VCP1" in text_upper:
            found.append("VCP1")
        if "VCP2" in text_upper:
            found.append("VCP2")
        if "PLB" in text_upper:
            found.append("PLB")
        return ", ".join(found) if found else "通用"

    def _extract_status(self, text: str) -> str:
        """从问题描述中提取状态"""
        if "已解决" in text or "已完成" in text or "已修复" in text:
            return "已解决"
        elif "排查" in text or "正在排查" in text:
            return "排查中"
        elif "待" in text or "尚未" in text or "未完成" in text:
            return "待处理"
        elif "无法" in text or "无心" in text or "无变化" in text:
            return "待处理"
        elif text.strip() == "无" or text == "无":
            return "无"
        else:
            return "待处理"

    def _extract_test_result(self, content: str) -> str:
        """提取测试结果"""
        match = re.search(r"【测试结果】\s*([\s\S]*?)(?=【今日计划实际是否完成】|【明日的测试计划】|【下周的测试计划】|$)", content)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_plan_completion(self, content: str) -> str:
        """提取计划完成情况"""
        match = re.search(r"【今日计划实际是否完成】\s*([\s\S]*?)(?=【明日的测试计划】|【下周的测试计划】|$)", content)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_next_plan(self, content: str) -> str:
        """提取明日/下周计划"""
        match = re.search(r"(【明日的测试计划】|【下周的测试计划】)\s*([\s\S]*?)(?=需要协调事项|$)", content, re.DOTALL)
        if match:
            return match.group(2).strip()
        return ""

    def _extract_coordination(self, content: str) -> str:
        """提取需要协调事项"""
        match = re.search(r"需要协调事项：(.+)", content)
        if match:
            return match.group(1).strip()
        return "无"

    def process_all(self) -> pd.DataFrame:
        """处理所有报告"""
        if not self.REPORT_DIR.exists():
            return pd.DataFrame()

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

    def get_problem_detail(self, df: pd.DataFrame) -> pd.DataFrame:
        """获取所有问题的扁平列表"""
        if df.empty:
            return pd.DataFrame()

        rows = []
        for _, row in df.iterrows():
            date = row.get("日期", "")
            for prob in row.get("问题列表", []):
                if prob.get("状态") != "无":
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
        for line in self.LINE_TYPES:
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
        daily_resolved = problems_df[problems_df["状态"] == "已解决"].groupby("日期").size().reset_index(name="已解决数")
        daily_pending = problems_df[problems_df["状态"] == "待处理"].groupby("日期").size().reset_index(name="待处理数")
        daily_investigating = problems_df[problems_df["状态"] == "排查中"].groupby("日期").size().reset_index(name="排查中数")

        result = daily.merge(daily_resolved, on="日期", how="left")
        result = result.merge(daily_pending, on="日期", how="left")
        result = result.merge(daily_investigating, on="日期", how="left")
        result = result.fillna(0)

        return result