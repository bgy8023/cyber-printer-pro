import os
import time
from typing import Optional
from .logger import logger
from .file_lock import FileLock
from .memory_palace_simple import get_memory_palace

class AutoDream:
    def __init__(self, novel_name: str = "默认小说"):
        self.novel_name = novel_name
        self.memory = get_memory_palace(novel_name)
        self.base_dir = self.memory.base_dir
        self.note_file = os.path.join(self.base_dir, "04-剧情巩固笔记.md")

    def consolidate(self):
        """执行一次梦游：自动梳理时间线、人物、伏笔"""
        logger.info("🌙 AutoDream 开始后台记忆巩固...")

        fixed = self.memory.fixed_memory
        outline = fixed.get("outline", "")
        character = fixed.get("character", "")

        chapters = self.memory.dynamic_memory.get("generated_chapters", [])
        chapters_sorted = sorted(chapters, key=lambda x: x["chapter_num"])

        timeline = "\n".join([
            f"第{c['chapter_num']}章：{c['summary']}（{c['word_count']}字）"
            for c in chapters_sorted
        ])

        content = f"""
# 《{self.novel_name}》AutoDream 剧情巩固笔记
生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}

## 一、核心设定摘要
{outline[:500]}...

## 二、人物档案
{character[:500]}...

## 三、已生成剧情时间线
{timeline}

## 四、状态
已生成 {len(chapters_sorted)} 章
最后更新：{self.memory.dynamic_memory.get('last_update', '')}
"""

        with FileLock(self.note_file):
            with open(self.note_file, "w", encoding="utf-8") as f:
                f.write(content.strip())

        logger.info("✅ AutoDream 记忆巩固完成")
        return True

_autodream_instance: Optional[AutoDream] = None

def get_autodream(novel_name: str = "默认小说"):
    global _autodream_instance
    if _autodream_instance is None or _autodream_instance.novel_name != novel_name:
        _autodream_instance = AutoDream(novel_name)
    return _autodream_instance
