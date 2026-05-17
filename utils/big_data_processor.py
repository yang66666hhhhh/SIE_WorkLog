import time
from pathlib import Path

import pandas as pd


class BigDataProcessor:
    """面向较大表格的分块读取和基础性能监控工具。"""

    def __init__(self, chunk_size=5000):
        self.chunk_size = chunk_size

    def read_csv_chunks(self, file_path, **kwargs):
        for chunk in pd.read_csv(file_path, chunksize=self.chunk_size, **kwargs):
            yield chunk

    def read_table(self, file_path, **kwargs):
        path = Path(file_path)
        if path.suffix.lower() == ".csv":
            return pd.concat(self.read_csv_chunks(path, **kwargs), ignore_index=True)
        return pd.read_excel(path, **kwargs)

    def profile(self, label, func, *args, **kwargs):
        started = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - started
        rows = len(result) if hasattr(result, "__len__") else None
        return {"label": label, "elapsed": elapsed, "rows": rows, "result": result}
