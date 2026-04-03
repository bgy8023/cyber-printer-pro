import os
import json
import time
from typing import Dict, List, Optional
from .logger import logger
from .file_lock import FileLock

class SimpleMemoryPalace:
    """
    简化版双层记忆宫殿
    L1 固定记忆层：novel_settings/下的00-全本大纲.md、01-人物档案.md（只读，绝对不允许修改）
    L2 动态记忆层：自动生成的03-动态剧情记忆.json（可写，每章更新）
    """
    def __init__(self, novel_name: str = "默认小说"):
        self.novel_name = novel_name
        self.base_dir = os.path.join("novel_settings", novel_name)
        os.makedirs(self.base_dir, exist_ok=True)
        
        # L1 固定记忆（只读）
        self.fixed_memory: Dict[str, str] = {}
        self._load_fixed_memory()
        
        # L2 动态记忆（可写）
        self.dynamic_memory: Dict = {
            "generated_chapters": [],
            "last_update": ""
        }
        self._load_dynamic_memory()
        
        logger.info(f"✅ 简化版双层记忆宫殿初始化完成，小说：{novel_name}")

    def _load_fixed_memory(self):
        """加载只读固定记忆：大纲、人物、世界观"""
        fixed_files = {
            "outline": "00-全本大纲.md",
            "character": "01-人物档案.md",
            "worldview": "02-世界观设定.md"
        }

        for key, filename in fixed_files.items():
            file_path = os.path.join(self.base_dir, filename)
            if not os.path.exists(file_path):
                default_file = os.path.join("novel_settings", "番茄爆款写作心法", filename)
                if os.path.exists(default_file):
                    import shutil
                    shutil.copy(default_file, file_path)
                    logger.info(f"📋 已从默认模板复制：{filename}")
            
            if os.path.exists(file_path):
                try:
                    with FileLock(file_path):
                        with open(file_path, "r", encoding="utf-8") as f:
                            self.fixed_memory[key] = f.read()
                            logger.info(f"✅ 固定记忆加载完成：{key}")
                except Exception as e:
                    logger.error(f"❌ 固定记忆加载失败：{filename}", exc_info=True)

    def get_fixed_prompt(self) -> str:
        """获取固定记忆完整prompt，用于生成时强制约束"""
        prompt_parts = ["【小说核心固定设定（必须严格遵守）】"]
        for key, content in self.fixed_memory.items():
            if content:
                prompt_parts.append(f"\n## {key.upper()}\n{content}")
        return "\n".join(prompt_parts)

    def get_character_names(self) -> List[str]:
        """从固定记忆中提取核心人物名，用于硬约束检查"""
        import re
        character_content = self.fixed_memory.get("character", "")
        if not character_content:
            return []
        names = []
        lines = character_content.split('\n')
        for line in lines:
            if '：' in line or ':' in line:
                parts = re.split(r'[：:]', line, 1)
                if len(parts) > 1:
                    name_part = parts[1].strip()
                    name = re.split(r'[\s\-]', name_part)[0]
                    if name:
                        names.append(name)
        return names

    def _load_dynamic_memory(self):
        """加载动态记忆"""
        dynamic_file = os.path.join(self.base_dir, "03-动态剧情记忆.json")
        if os.path.exists(dynamic_file):
            try:
                with FileLock(dynamic_file):
                    with open(dynamic_file, "r", encoding="utf-8") as f:
                        self.dynamic_memory = json.load(f)
                logger.info("✅ 动态记忆加载完成")
            except Exception as e:
                logger.error(f"❌ 动态记忆加载失败：{str(e)}", exc_info=True)

    def _save_dynamic_memory(self):
        """保存动态记忆"""
        dynamic_file = os.path.join(self.base_dir, "03-动态剧情记忆.json")
        try:
            with FileLock(dynamic_file):
                with open(dynamic_file, "w", encoding="utf-8") as f:
                    json.dump(self.dynamic_memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 动态记忆保存失败：{str(e)}", exc_info=True)

    def update_chapter_memory(self, chapter_num: int, chapter_summary: str, word_count: int):
        """更新单章生成后的动态记忆"""
        chapter_info = {
            "chapter_num": chapter_num,
            "summary": chapter_summary,
            "word_count": word_count,
            "generate_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.dynamic_memory["generated_chapters"] = [
            c for c in self.dynamic_memory["generated_chapters"] if c["chapter_num"] != chapter_num
        ]
        self.dynamic_memory["generated_chapters"].append(chapter_info)
        self.dynamic_memory["generated_chapters"].sort(key=lambda x: x["chapter_num"])
        self.dynamic_memory["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        self._save_dynamic_memory()
        logger.info(f"✅ 第{chapter_num}章动态记忆更新完成")

    def get_previous_summary(self, max_chapters: int = 2) -> str:
        """获取前几章的剧情摘要，用于承上启下"""
        chapters = sorted(self.dynamic_memory["generated_chapters"], key=lambda x: x["chapter_num"], reverse=True)
        recent = chapters[:max_chapters]
        recent.reverse()
        
        if not recent:
            return "本书开篇，无前置剧情"
        
        parts = ["【前情提要】"]
        for c in recent:
            parts.append(f"第{c['chapter_num']}章：{c['summary']}")
        return "\n".join(parts)

_memory_instance: Optional[SimpleMemoryPalace] = None

def get_memory_palace(novel_name: str = "默认小说") -> SimpleMemoryPalace:
    global _memory_instance
    if _memory_instance is None or _memory_instance.novel_name != novel_name:
        _memory_instance = SimpleMemoryPalace(novel_name)
    return _memory_instance
