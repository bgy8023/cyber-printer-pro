import os
import json
import time
import tempfile
from filelock import FileLock
from .logger import logger

class SimpleMemoryPalace:
    def __init__(self, novel_name="默认小说"):
        self.base_dir = os.path.join("novel_settings", novel_name)
        os.makedirs(self.base_dir, exist_ok=True)
        self.dynamic_file = os.path.join(self.base_dir, "03-动态剧情记忆.json")
        self.lock_file = self.dynamic_file + ".lock"
        
        self._clear_stale_lock()
        self.lock = FileLock(self.lock_file, timeout=15)
        self._init_fixed_memory()

    def _clear_stale_lock(self):
        if os.path.exists(self.lock_file) and (time.time() - os.path.getmtime(self.lock_file) > 600):
            logger.warning(f"🚨 清除超时僵尸锁: {self.lock_file}")
            try: os.unlink(self.lock_file)
            except: pass

    def _init_fixed_memory(self):
        self.fixed_memory = {}
        for key, fname in [("outline", "00-全本大纲.md"), ("character", "01-人物档案.md"), ("worldview", "02-世界观设定.md")]:
            fpath = os.path.join(self.base_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8") as f: self.fixed_memory[key] = f.read()

    def get_fixed_prompt(self):
        return "\n".join([f"## {k.upper()}\n{v}" for k, v in self.fixed_memory.items() if v])

    def get_dynamic_prompt(self):
        if not os.path.exists(self.dynamic_file): return "无前置剧情"
        with open(self.dynamic_file, 'r', encoding="utf-8") as f:
            data = json.load(f)
            return "\n".join([f"第{c['num']}章: {c['summary']}" for c in data.get("chapters", [])[-3:]])

    def safe_update(self, chapter_num, summary, word_count):
        with self.lock:
            data = {"chapters": []}
            if os.path.exists(self.dynamic_file):
                with open(self.dynamic_file, 'r', encoding="utf-8") as f: data = json.load(f)
            
            data["chapters"] = [c for c in data["chapters"] if c["num"] != chapter_num]
            data["chapters"].append({"num": chapter_num, "summary": summary, "words": word_count})
            data["chapters"].sort(key=lambda x: x["num"])
            
            with tempfile.NamedTemporaryFile('w', dir=self.base_dir, delete=False, encoding="utf-8") as tf:
                json.dump(data, tf, ensure_ascii=False, indent=2)
                temp_name = tf.name
            os.replace(temp_name, self.dynamic_file)
            logger.info(f"✅ 章节 {chapter_num} 记忆已原子化落盘")
