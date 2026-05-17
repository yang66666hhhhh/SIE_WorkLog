import hashlib
import pickle
import sqlite3
import time
from collections import OrderedDict
from pathlib import Path


class IntelligentCache:
    """轻量多层缓存：内存 LRU + SQLite 磁盘缓存。"""

    def __init__(self, cache_dir=".cache", max_memory_items=16, default_ttl=3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_memory_items = max_memory_items
        self.default_ttl = default_ttl
        self._memory = OrderedDict()
        self._db_path = self.cache_dir / "intelligent_cache.sqlite3"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_items (
                    key TEXT PRIMARY KEY,
                    value BLOB NOT NULL,
                    expires_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )

    def build_key(self, *parts):
        raw = "|".join(str(part) for part in parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def build_file_key(self, file_path, *parts):
        path = Path(file_path)
        stat = path.stat()
        return self.build_key(path.resolve(), stat.st_mtime_ns, stat.st_size, *parts)

    def get(self, key):
        now = time.time()
        if key in self._memory:
            expires_at, value = self._memory.pop(key)
            if expires_at > now:
                self._memory[key] = (expires_at, value)
                return value

        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT value, expires_at FROM cache_items WHERE key = ?",
                (key,),
            ).fetchone()

        if not row:
            return None

        value_blob, expires_at = row
        if expires_at <= now:
            self.delete(key)
            return None

        value = pickle.loads(value_blob)
        self._remember(key, expires_at, value)
        return value

    def set(self, key, value, ttl=None):
        expires_at = time.time() + (self.default_ttl if ttl is None else ttl)
        value_blob = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache_items (key, value, expires_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (key, value_blob, expires_at, time.time()),
            )
        self._remember(key, expires_at, value)

    def delete(self, key):
        self._memory.pop(key, None)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM cache_items WHERE key = ?", (key,))

    def clear_expired(self):
        now = time.time()
        self._memory = OrderedDict(
            (key, item) for key, item in self._memory.items() if item[0] > now
        )
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM cache_items WHERE expires_at <= ?", (now,))

    def _remember(self, key, expires_at, value):
        self._memory[key] = (expires_at, value)
        while len(self._memory) > self.max_memory_items:
            self._memory.popitem(last=False)
