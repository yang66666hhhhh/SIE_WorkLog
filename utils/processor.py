import pandas as pd
import numpy as np
import re
import logging
from pathlib import Path
from utils.config import Config

logger = logging.getLogger(__name__)


class WorkRecordProcessor:

    def __init__(self):
        self.config = Config()
        self.project = self.config.load_project_name()

        raw_rules = self.config.load_task_rules()
        self.task_rules = {k: re.compile(v) for k, v in raw_rules.items()}
        self.equipment_dict = self.config.load_equipment()

    def normalize_columns(self, df):
        col_map = {}
        self.work_columns = []

        for col in df.columns:
            name = str(col)
            if "日期" in name:
                col_map[col] = "日期"
            elif "备注" in name:
                col_map[col] = "备注"
            elif "问题描述" in name:
                col_map[col] = "问题描述"
            elif "工作项" in name:
                col_map[col] = name
                self.work_columns.append(name)

        df = df.rename(columns=col_map)

        if "日期" not in df.columns:
            raise ValueError("缺少日期列")
        if not self.work_columns:
            raise ValueError("缺少工作项列（MSAP工作项/HDI二处工作项）")
        if "备注" not in df.columns:
            df["备注"] = ""
        if "问题描述" not in df.columns:
            df["问题描述"] = ""

        return df

    def parse_date(self, val):
        try:
            dt = pd.to_datetime(val)
            if pd.isna(dt):
                return pd.NaT
            return dt.normalize()
        except (ValueError, TypeError):
            return pd.NaT

    def split_tasks(self, text):
        if not isinstance(text, str):
            return []
        lines = text.split("\n")
        clean = []
        for line in lines:
            line = line.strip()
            if not line or len(line) < 2:
                continue
            line = re.sub(r"^\d+[、.）)\s]+", "", line).strip()
            if not line or len(line) < 2:
                continue
            clean.append(line)
        return clean

    def match_equipment(self, text):
        text = str(text).lower()
        for name, keywords in self.equipment_dict.items():
            for k in keywords:
                if k.lower() in text:
                    return name
        return "未知"

    def match_type(self, text):
        for t, pattern in self.task_rules.items():
            if re.search(pattern, str(text)):
                return t
        return "其他"

    def extract_problem_for_source(self, problem_desc, source):
        if not isinstance(problem_desc, str) or not problem_desc.strip():
            return ""

        source_upper = source.upper()
        if "MSAP" in source_upper:
            pattern = r"MSAP[：:]\s*(.*?)(?:；|;|$)"
        elif "HDI" in source_upper:
            pattern = r"HDI[：:]\s*(.*?)(?:；|;|$)"
        else:
            return problem_desc.strip()

        match = re.search(pattern, problem_desc, re.DOTALL)
        if match:
            desc = match.group(1).strip()
            return desc if desc else ""

        return problem_desc.strip()

    def task_weight(self, text):
        text = str(text)
        if any(k in text for k in ["调试", "开发", "异常", "问题"]):
            return 1.5
        elif any(k in text for k in ["配置", "搭建"]):
            return 1.2
        elif any(k in text for k in ["学习", "会议", "培训"]):
            return 0.8
        else:
            return 1.0

    def process(self, input_file, output_file="任务级数据.xlsx"):
        if not Path(input_file).exists():
            raise FileNotFoundError(f"输入文件不存在: {input_file}")

        df = pd.read_excel(input_file)
        df = self.normalize_columns(df)

        df["日期"] = df["日期"].apply(self.parse_date)
        df = df.dropna(subset=["日期"])

        task_rows = []
        task_id = 1
        DAY_HOURS = 8

        for _, row in df.iterrows():
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
                weights = [self.task_weight(t) for t in tasks]
                total_weight = sum(weights)

                problem_for_source = self.extract_problem_for_source(problem_desc_raw, source)

                for t, w in zip(tasks, weights):
                    hours = (w / total_weight) * DAY_HOURS if total_weight else 0
                    task_rows.append({
                        "任务ID": f"T{task_id:05d}",
                        "日期": date,
                        "星期": date.day_name(),
                        "任务内容": t,
                        "来源": source,
                        "线体/设备": self.match_equipment(t),
                        "任务类型": self.match_type(t),
                        "工时": round(hours, 2),
                        "问题描述": problem_for_source,
                        "项目": self.project,
                        "备注": row["备注"],
                    })
                    task_id += 1

        df_task = pd.DataFrame(task_rows)
        if df_task.empty:
            logger.warning("未生成任何任务，请检查输入数据")
            return df_task

        df_task["月份"] = df_task["日期"].dt.to_period("M").astype(str)
        df_task["周"] = df_task["日期"].dt.isocalendar().week
        df_task["是否周末"] = df_task["日期"].dt.weekday >= 5

        daily = df_task.groupby("日期")["工时"].transform("sum")
        df_task["日总工时"] = daily
        df_task["任务占比"] = df_task["工时"] / daily.replace(0, np.nan)

        df_task = df_task.sort_values(["日期", "任务ID"])
        df_task.to_excel(output_file, index=False)

        logger.info(f"完成，生成 {len(df_task)} 条任务（来源：{', '.join(self.work_columns)}）")
        return df_task
