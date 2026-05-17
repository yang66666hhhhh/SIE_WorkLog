import re

import pandas as pd


class NaturalLanguageQuery:
    """针对任务数据的轻量中文查询解析器。"""

    def __init__(self, df):
        self.df = df.copy()

    def suggestions(self):
        return [
            "最近7天调试任务",
            "VCP1问题有哪些",
            "MSAP本月工时",
            "工时最高的设备",
            "包含PDA的任务",
        ]

    def query(self, text):
        text = str(text or "").strip()
        if not text:
            return self.df.head(0), "请输入查询内容"

        result = self.df.copy()
        result, notes = self._apply_filters(result, text)
        if any(word in text for word in ["最高", "最多", "top", "TOP"]):
            result = self._rank(result, text)
        return result, "；".join(notes) if notes else "已按关键词查询"

    def _apply_filters(self, df, text):
        notes = []
        upper_text = text.upper()

        if "日期" in df.columns:
            df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
            max_date = df["日期"].max()
            if "最近7天" in text and pd.notna(max_date):
                start = max_date - pd.Timedelta(days=6)
                df = df[df["日期"] >= start]
                notes.append(f"日期 >= {start.date()}")
            month_match = re.search(r"(\d{4})[-年](\d{1,2})", text)
            if month_match:
                month = f"{int(month_match.group(1)):04d}-{int(month_match.group(2)):02d}"
                df = df[df["日期"].dt.strftime("%Y-%m") == month]
                notes.append(f"月份 = {month}")
            elif "本月" in text and pd.notna(max_date):
                month = max_date.strftime("%Y-%m")
                df = df[df["日期"].dt.strftime("%Y-%m") == month]
                notes.append(f"月份 = {month}")

        for col in ["来源", "线体/设备", "任务类型"]:
            if col not in df.columns:
                continue
            matches = [value for value in df[col].dropna().unique() if str(value).upper() in upper_text]
            if matches:
                df = df[df[col].isin(matches)]
                notes.append(f"{col} = {', '.join(map(str, matches))}")

        keyword_cols = [col for col in ["任务内容", "问题描述", "备注"] if col in df.columns]
        if keyword_cols:
            keyword = self._extract_keyword(text)
            if keyword:
                mask = df[keyword_cols].astype(str).apply(
                    lambda col: col.str.contains(keyword, case=False, na=False)
                ).any(axis=1)
                filtered = df[mask]
                if not filtered.empty:
                    df = filtered
                    notes.append(f"关键词包含 {keyword}")

        return df, notes

    def _extract_keyword(self, text):
        match = re.search(r"包含(.+?)(?:的任务|任务|$)", text)
        if match:
            return match.group(1).strip()
        for token in ["PDA", "EAP", "VCP1", "VCP2", "PLB", "问题", "异常"]:
            if token.lower() in text.lower():
                return token
        return ""

    def _rank(self, df, text):
        if "设备" in text and "线体/设备" in df.columns:
            return df.groupby("线体/设备", as_index=False)["工时"].sum().sort_values("工时", ascending=False)
        if "类型" in text and "任务类型" in df.columns:
            return df.groupby("任务类型", as_index=False)["工时"].sum().sort_values("工时", ascending=False)
        if "来源" in text and "来源" in df.columns:
            return df.groupby("来源", as_index=False)["工时"].sum().sort_values("工时", ascending=False)
        return df.sort_values("工时", ascending=False) if "工时" in df.columns else df
