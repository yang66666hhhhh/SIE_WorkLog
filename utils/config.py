import json
import hashlib
import base64
from pathlib import Path
from functools import lru_cache


class Config:

    DEFAULT_EQUIPMENT = {
        "镍钯金": ["镍钯金", "镍钯"],
        "大族": ["大族", "han's"],
        "VCP1": ["vcp1", "tkc", "tck"],
        "VCP2": ["vcp2"],
        "安美特PLB": ["plb", "安美特"],
        "LDD棕化线（HDI）": ["ldd棕化线（hdi）", "hdi"],
        "LDD棕化线（MSAP）": ["ldd棕化线（msap）", "msap", "撕铜箔"],
        "LDD去棕化（MSAP）": ["ldd去棕化（msap）", "去棕化MSAP"],
    }

    DEFAULT_TASK_RULES = {
        "学习": "学习|培训",
        "调试": "调试|联调|测试|异常|问题",
        "配置": "配置|搭建",
        "分析": "分析|整理|梳理",
    }

    DEFAULT_AI_CONFIG = {
        "provider": "openai",
        "api_key": "",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-3.5-turbo",
        "enabled": False
    }

    DEFAULT_REPORT_FORMAT_CONFIG = {
        "test_report": {
            "version": "v1",
            "custom_field_labels": {},
            "custom_categories": [],
        },
        "joint_debug_summary": {
            "version": "v1",
            "custom_field_labels": {},
            "custom_categories": [],
        },
    }

    DEFAULT_PROJECT_NAME = "胜宏科技HDI二处工业物联网平台实施项目2026"

    _CONFIG_REGISTRY = {
        "equipment": ("equipment.json", "DEFAULT_EQUIPMENT"),
        "task_rules": ("task_rules.json", "DEFAULT_TASK_RULES"),
        "ai_config": ("ai_config.json", "DEFAULT_AI_CONFIG"),
    }

    DEFAULT_PROBLEMS = []

    _OBFUSCATION_KEY = "SIE_WorkLog_2026"

    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

    def _config_path(self, filename):
        return self.config_dir / filename

    def _load_config(self, filename, default_attr):
        path = self._config_path(filename)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        default = getattr(self, default_attr)
        self._save_config(filename, default)
        return default.copy() if isinstance(default, dict) else default

    def _save_config(self, filename, data):
        path = self._config_path(filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._invalidate_cache(filename)

    @staticmethod
    def _obfuscate(text: str) -> str:
        if not text:
            return ""
        encoded = base64.b64encode(text.encode()).decode()
        shifted = encoded[-3:] + encoded[:-3]
        key_pad = base64.b64encode(Config._OBFUSCATION_KEY.encode()).decode()[:6]
        return f"enc_{key_pad}_{shifted}"

    @staticmethod
    def _deobfuscate(text: str) -> str:
        if not text or not text.startswith("enc_"):
            return text
        try:
            parts = text[4:].split("_", 1)
            if len(parts) != 2:
                return text
            shifted = parts[1]
            encoded = shifted[3:] + shifted[:3]
            return base64.b64decode(encoded).decode()
        except Exception:
            return text

    @lru_cache(maxsize=8)
    def _cached_load(self, filename, default_attr):
        return self._load_config(filename, default_attr)

    def _invalidate_cache(self, filename=None):
        self._cached_load.cache_clear()

    def load_equipment(self) -> dict:
        return self._cached_load("equipment.json", "DEFAULT_EQUIPMENT")

    def save_equipment(self, data: dict):
        self._save_config("equipment.json", data)

    def load_task_rules(self) -> dict:
        return self._cached_load("task_rules.json", "DEFAULT_TASK_RULES")

    def save_task_rules(self, data: dict):
        self._save_config("task_rules.json", data)

    def load_problems(self) -> list:
        return self._load_config("problems.json", "DEFAULT_PROBLEMS")

    def save_problems(self, data: list):
        self._save_config("problems.json", data)

    def load_ai_config(self) -> dict:
        config = self._cached_load("ai_config.json", "DEFAULT_AI_CONFIG")
        if "api_key" in config and config["api_key"]:
            config["api_key"] = self._deobfuscate(config["api_key"])
        return config

    def save_ai_config(self, data: dict):
        save_data = data.copy()
        if "api_key" in save_data and save_data["api_key"]:
            save_data["api_key"] = self._obfuscate(save_data["api_key"])
        self._save_config("ai_config.json", save_data)

    def load_report_format_config(self) -> dict:
        raw = self._cached_load("report_format.json", "DEFAULT_REPORT_FORMAT_CONFIG")
        if "test_report" not in raw:
            raw = {
                "test_report": {
                    "version": raw.get("version", "v1"),
                    "custom_field_labels": raw.get("custom_field_labels", {}),
                    "custom_categories": raw.get("custom_categories", []),
                },
                "joint_debug_summary": {
                    "version": "v1",
                    "custom_field_labels": {},
                    "custom_categories": [],
                },
            }
        return raw

    def save_report_format_config(self, data: dict):
        self._save_config("report_format.json", data)

    def load_project_name(self) -> str:
        path = self._config_path("project.json")
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("project_name", self.DEFAULT_PROJECT_NAME)
        self.save_project_name(self.DEFAULT_PROJECT_NAME)
        return self.DEFAULT_PROJECT_NAME

    def save_project_name(self, name: str):
        path = self._config_path("project.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"project_name": name}, f, ensure_ascii=False, indent=2)

    def config_hash(self) -> str:
        equipment = json.dumps(self.load_equipment(), ensure_ascii=False, sort_keys=True)
        task_rules = json.dumps(self.load_task_rules(), ensure_ascii=False, sort_keys=True)
        return hashlib.md5((equipment + task_rules).encode()).hexdigest()

    def load_config_hash(self) -> str:
        path = self.config_dir / "config_hash.txt"
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
        return ""

    def save_config_hash(self, hash_val: str):
        path = self.config_dir / "config_hash.txt"
        path.write_text(hash_val, encoding="utf-8")

    def validate_regex(self, pattern: str) -> tuple:
        try:
            import re
            re.compile(pattern)
            return True, ""
        except re.error as e:
            return False, str(e)
