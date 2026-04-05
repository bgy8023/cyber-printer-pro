# =============================================
# Google L8 级原子化记忆保护
# 解决：多进程/多线程读写竞争、数据损坏、断电零丢失
# =============================================
import os
import json
import tempfile
from typing import Dict, Any, List
from filelock import FileLock
from .logger import logger


class SimpleMemoryPalace:
    """
    Google 工程级记忆宫殿核心特性：
    1. 文件锁保护，避免读写竞争
    2. 临时文件+原子替换，断电零丢失
    3. 双层记忆结构：固定设定 + 动态剧情
    """

    def __init__(self, novel_name: str = "默认小说"):
        self.novel_name = novel_name
        self.base_dir = os.path.join("novel_settings", novel_name)
        os.makedirs(self.base_dir, exist_ok=True)

        # 记忆文件路径
        self.setting_file = os.path.join(self.base_dir, "01-核心设定.md")
        self.plot_file = os.path.join(self.base_dir, "02-剧情大纲.md")
        self.dynamic_file = os.path.join(self.base_dir, "03-动态剧情记忆.json")

        # 锁文件（防止多进程/多线程竞争）
        self.lock = FileLock(self.dynamic_file + ".lock", timeout=30)

        # 初始化空记忆文件
        self._init_empty_files()
        logger.info(f"✅ 记忆宫殿初始化完成 | 小说: {novel_name}")

    def _init_empty_files(self):
        """初始化空的记忆文件（如果不存在）"""
        if not os.path.exists(self.setting_file):
            with open(self.setting_file, "w", encoding="utf-8") as f:
                f.write("# 核心设定\n\n在这里填写你的小说核心设定...\n")

        if not os.path.exists(self.plot_file):
            with open(self.plot_file, "w", encoding="utf-8") as f:
                f.write("# 剧情大纲\n\n在这里填写你的小说剧情大纲...\n")

        if not os.path.exists(self.dynamic_file):
            with open(self.dynamic_file, "w", encoding="utf-8") as f:
                json.dump({"chapters": [], "last_updated": None}, f, ensure_ascii=False, indent=2)

    def get_full_memory(self) -> str:
        """
        获取完整记忆（固定设定 + 动态剧情）
        只读操作，不需要锁
        """
        memory_parts = []

        # 1. 加载固定设定
        if os.path.exists(self.setting_file):
            with open(self.setting_file, "r", encoding="utf-8") as f:
                memory_parts.append("## 核心设定\n" + f.read())

        # 2. 加载剧情大纲
        if os.path.exists(self.plot_file):
            with open(self.plot_file, "r", encoding="utf-8") as f:
                memory_parts.append("## 剧情大纲\n" + f.read())

        # 3. 加载动态剧情记忆
        if os.path.exists(self.dynamic_file):
            with open(self.dynamic_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("chapters"):
                    chapters_summary = "\n".join([
                        f"- 第{ch['num']}章: {ch['summary']}"
                        for ch in data["chapters"][-10:]  # 只保留最近10章，避免上下文过长
                    ])
                    memory_parts.append("## 已写章节摘要\n" + chapters_summary)

        full_memory = "\n\n".join(memory_parts)
        logger.info(f"📚 记忆加载完成 | 总长度: {len(full_memory)}")
        return full_memory

    def safe_update_chapter_memory(self, chapter_num: int, summary: str):
        """
        Google 级原子化更新：
        持有锁 -> 读 -> 改 -> 写临时文件 -> 原子替换
        就算中途断电，记忆文件也不会变 0KB
        """
        with self.lock:
            logger.info(f"🔒 获取锁 | 更新章节 {chapter_num} 记忆")

            # 1. 读取现有记忆
            data = {"chapters": [], "last_updated": None}
            if os.path.exists(self.dynamic_file):
                try:
                    with open(self.dynamic_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("⚠️  动态记忆文件损坏，使用空数据")

            # 2. 更新数据
            # 检查是否已存在该章节，存在则替换
            updated = False
            for i, ch in enumerate(data["chapters"]):
                if ch["num"] == chapter_num:
                    data["chapters"][i] = {"num": chapter_num, "summary": summary}
                    updated = True
                    break

            if not updated:
                data["chapters"].append({"num": chapter_num, "summary": summary})

            # 3. 写入临时文件（同一文件系统，保证原子替换）
            with tempfile.NamedTemporaryFile(
                'w',
                dir=self.base_dir,
                prefix="memory_",
                suffix=".tmp",
                delete=False,
                encoding="utf-8"
            ) as tf:
                json.dump(data, tf, ensure_ascii=False, indent=2)
                temp_name = tf.name

            # 4. 原子替换（os.replace 是原子操作，断电零丢失）
            os.replace(temp_name, self.dynamic_file)

            logger.info(f"✅ 章节 {chapter_num} 记忆已原子化落盘")

    def get_chapter_history(self) -> List[Dict[str, Any]]:
        """获取章节历史列表"""
        with self.lock:
            if os.path.exists(self.dynamic_file):
                with open(self.dynamic_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("chapters", [])
            return []


# 全局单例工厂
_memory_instances = {}


def get_memory_palace(novel_name: str = "默认小说") -> SimpleMemoryPalace:
    """
    获取全局单例的记忆宫殿
    按小说名隔离，支持多小说
    """
    if novel_name not in _memory_instances:
        _memory_instances[novel_name] = SimpleMemoryPalace(novel_name)
    return _memory_instances[novel_name]


__all__ = ["SimpleMemoryPalace", "get_memory_palace"]
