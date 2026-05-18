import re
from pathlib import Path

import numpy as np
import pandas as pd

from utils.processor import WorkRecordProcessor


class OptimizedWorkRecordProcessor(WorkRecordProcessor):
    """在保留原业务规则的基础上优化任务拆分和派生字段计算。"""

    TASK_PREFIX_RE = re.compile(r"^\d+[、.）)\s]+")

    def split_tasks(self, text):
        if not isinstance(text, str):
            return []
        lines = text.splitlines()
        tasks = []
        for line in lines:
            line = self.TASK_PREFIX_RE.sub("", line.strip()).strip()
            if len(line) >= 2:
                tasks.append(line)
        return tasks

    def match_type(self, text):
        text = str(text)
        for task_type, pattern in self.task_rules.items():
            if pattern.search(text):
                return task_type
        return "其他"

    def process(self, input_file, output_file="任务级数据.xlsx", progress_callback=None, raw_df=None):
        if raw_df is None:
            if not Path(input_file).exists():
                raise FileNotFoundError(f"输入文件不存在: {input_file}")
            raw_df = pd.read_excel(input_file, engine="openpyxl", dtype=str)

        df = self.normalize_columns(raw_df)
        df["日期"] = pd.to_datetime(df["日期"], errors="coerce").dt.normalize()
        df = df.dropna(subset=["日期"])

        total_rows = len(df)
        rows = []
        day_hours = 8
        for idx, (_, row) in enumerate(df.iterrows()):
            date = row["日期"]
            problem_desc_raw = row["问题描述"] if pd.notna(row["问题描述"]) else ""

            for col in self.work_columns:
                content = row[col]
                if pd.isna(content) or not isinstance(content, str) or not content.strip():
                    continue

                tasks = self.split_tasks(content)
                if not tasks:
                    continue

                source = col.replace("工作项", "")
                weights = np.array([self.task_weight(task) for task in tasks], dtype=float)
                total_weight = weights.sum()
                hours = np.round(weights / total_weight * day_hours, 2) if total_weight else np.zeros(len(tasks))
                problem_for_source = self.extract_problem_for_source(problem_desc_raw, source)

                for task, hour in zip(tasks, hours):
                    rows.append(
                        {
                            "日期": date,
                            "任务内容": task,
                            "来源": source,
                            "线体/设备": self.match_equipment(task),
                            "任务类型": self.match_type(task),
                            "工时": float(hour),
                            "问题描述": problem_for_source,
                            "项目": self.project,
                            "备注": row["备注"],
                        }
                    )

        if progress_callback and idx % max(1, total_rows // 20) == 0:
            progress_callback(idx, total_rows)

        df_task = pd.DataFrame(rows)
        if df_task.empty:
            return df_task

        df_task.insert(0, "任务ID", [f"T{i:05d}" for i in range(1, len(df_task) + 1)])
        df_task["星期"] = df_task["日期"].dt.day_name()
        df_task["月份"] = df_task["日期"].dt.to_period("M").astype(str)
        df_task["周"] = df_task["日期"].dt.isocalendar().week
        df_task["是否周末"] = df_task["日期"].dt.weekday >= 5

        daily = df_task.groupby("日期")["工时"].transform("sum")
        df_task["日总工时"] = daily
        df_task["任务占比"] = df_task["工时"] / daily.replace(0, np.nan)
        ordered_cols = [
            "任务ID", "日期", "星期", "任务内容", "来源", "线体/设备", "任务类型",
            "工时", "问题描述", "项目", "备注", "月份", "周", "是否周末", "日总工时", "任务占比",
        ]
        df_task = df_task[[col for col in ordered_cols if col in df_task.columns]]
        df_task = df_task.sort_values(["日期", "任务ID"])
        df_task.to_excel(output_file, index=False)
        return df_task
