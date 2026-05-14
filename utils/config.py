import json
import hashlib
from pathlib import Path


class Config:
    """配置读写管理"""

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

    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.equipment_path = self.config_dir / "equipment.json"
        self.task_rules_path = self.config_dir / "task_rules.json"
        self.ai_config_path = self.config_dir / "ai_config.json"

    DEFAULT_AI_CONFIG = {
        "provider": "openai",
        "api_key": "",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-3.5-turbo",
        "enabled": False
    }

    def load_equipment(self) -> dict:
        if self.equipment_path.exists():
            with open(self.equipment_path, "r", encoding="utf-8") as f:
                return json.load(f)
        self.save_equipment(self.DEFAULT_EQUIPMENT)
        return self.DEFAULT_EQUIPMENT.copy()

    def save_equipment(self, data: dict):
        with open(self.equipment_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_task_rules(self) -> dict:
        if self.task_rules_path.exists():
            with open(self.task_rules_path, "r", encoding="utf-8") as f:
                return json.load(f)
        self.save_task_rules(self.DEFAULT_TASK_RULES)
        return self.DEFAULT_TASK_RULES.copy()

    def save_task_rules(self, data: dict):
        with open(self.task_rules_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_ai_config(self) -> dict:
        if self.ai_config_path.exists():
            with open(self.ai_config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        self.save_ai_config(self.DEFAULT_AI_CONFIG)
        return self.DEFAULT_AI_CONFIG.copy()

    def save_ai_config(self, data: dict):
        with open(self.ai_config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

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
