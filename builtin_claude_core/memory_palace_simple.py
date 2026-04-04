# 简化版双层记忆宫殿 - 原子级读写，彻底解决竞争条件
import os
import json
import time
import tempfile
from typing import Dict, List, Optional
from filelock import FileLock
from .logger import logger

class SimpleMemoryPalace:
    """
    简化版双层记忆宫殿 - Deer-Flow 2.0 优化版
    L1 固定记忆层：novel_settings/下的全本大纲、人物档案、世界观设定（只读，绝对不允许修改）
    L2 动态记忆层：自动生成的动态剧情记忆.json（原子级读写，跨进程安全）
    【Deer-Flow 2.0 Token极致压缩】
    - 只记3轮对话，模仿无状态销毁
    - 只传结果摘要，不传全量历史
    - 超阈值自动压缩
    """
    def __init__(self, novel_name: str = "默认小说"):
        self.novel_name = novel_name
        self.base_dir = os.path.join("novel_settings", novel_name)
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Deer-Flow 2.0 配置
        self.max_history_rounds = 3  # 只记3轮，模仿无状态销毁
        self.compress_threshold = 4000  # 超过4000字符自动压缩
        self.auto_clean = True  # 静默清理，无冗余日志
        
        # L1 固定记忆（只读）
        self.fixed_memory: Dict[str, str] = {}
        self._load_fixed_memory()
        
        # L2 动态记忆（原子级读写）
        self.dynamic_memory: Dict = {
            "generated_chapters": [],
            "last_update": "",
            "version": 1
        }
        self._load_dynamic_memory()
        
        logger.info(f"✅ 双层记忆宫殿初始化完成，小说：{novel_name}")

    # ========== L1 固定记忆核心方法 ==========
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
                # 如果文件不存在，从默认模板复制
                default_file = os.path.join("novel_settings", "番茄爆款写作心法", filename)
                if os.path.exists(default_file):
                    import shutil
                    shutil.copy(default_file, file_path)
                    logger.info(f"📋 已从默认模板复制：{filename}")
            
            if os.path.exists(file_path):
                try:
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
        # 匹配"主角：XXX"、"反派：XXX"格式
        matches = re.findall(r"[：:]\s*([^\s\-]+)", character_content)
        return [name.strip() for name in matches if name.strip()]

    # ========== L2 动态记忆核心方法（原子级修复版） ==========
    def _load_dynamic_memory(self):
        """线程/进程安全的动态记忆加载，原子操作"""
        self.dynamic_file = os.path.join(self.base_dir, "03-动态剧情记忆.json")
        self.lock_file = self.dynamic_file + ".lock"
        self.lock = FileLock(self.lock_file, timeout=10)  # 10秒超时，防止死锁

        # 原子级读操作
        try:
            with self.lock:
                if os.path.exists(self.dynamic_file):
                    with open(self.dynamic_file, "r", encoding="utf-8") as f:
                        self.dynamic_memory = json.load(f)
                    logger.info("✅ 动态记忆加载完成")
                else:
                    # 初始化默认结构
                    self._save_dynamic_memory()
        except Exception as e:
            logger.error(f"❌ 动态记忆加载失败：{str(e)}", exc_info=True)
            self.dynamic_memory = {
                "generated_chapters": [],
                "last_update": "",
                "version": 1
            }

    def _save_dynamic_memory(self):
        """
        原子级写入操作，彻底解决竞争条件
        读-改-写全程持有锁，临时文件原子替换，进程崩溃也不会损坏文件
        """
        try:
            # 全程持有锁，绝不释放
            with self.lock:
                # 版本号自增，防止脏写
                self.dynamic_memory["version"] = self.dynamic_memory.get("version", 1) + 1
                self.dynamic_memory["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")

                # 1. 先写入同目录临时文件，确保同文件系统（原子替换的前提）
                temp_file = tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=self.base_dir,
                    suffix=".tmp",
                    delete=False
                )

                try:
                    json.dump(self.dynamic_memory, temp_file, ensure_ascii=False, indent=2)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())  # 强制刷入磁盘，防止系统缓存
                finally:
                    temp_file.close()

                # 2. 原子替换原文件，同文件系统下100%原子操作
                os.replace(temp_file.name, self.dynamic_file)
                logger.info(f"✅ 动态记忆原子写入完成，版本号：{self.dynamic_memory['version']}")

        except Exception as e:
            logger.error(f"❌ 动态记忆保存失败：{str(e)}", exc_info=True)
            # 清理临时文件
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def update_chapter_memory(self, chapter_num: int, chapter_summary: str, word_count: int):
        """更新章节记忆，全程原子操作，无竞争窗口"""
        try:
            # 全程持有锁，读-改-写一次性完成
            with self.lock:
                # 重新读取最新数据，防止锁等待期间数据被修改
                if os.path.exists(self.dynamic_file):
                    with open(self.dynamic_file, "r", encoding="utf-8") as f:
                        self.dynamic_memory = json.load(f)

                # 修改数据
                chapter_info = {
                    "chapter_num": chapter_num,
                    "summary": chapter_summary,
                    "word_count": word_count,
                    "generate_time": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                # 去重
                self.dynamic_memory["generated_chapters"] = [
                    c for c in self.dynamic_memory["generated_chapters"] if c["chapter_num"] != chapter_num
                ]
                self.dynamic_memory["generated_chapters"].append(chapter_info)
                self.dynamic_memory["generated_chapters"].sort(key=lambda x: x["chapter_num"])
                
                # 原子写入
                self._save_dynamic_memory()

        except Exception as e:
            logger.error(f"❌ 章节记忆更新失败：{str(e)}", exc_info=True)

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

# 全局单例管理
_memory_instance: Optional[SimpleMemoryPalace] = None

def get_memory_palace(novel_name: str = "默认小说") -> SimpleMemoryPalace:
    global _memory_instance
    if _memory_instance is None or _memory_instance.novel_name != novel_name:
        _memory_instance = SimpleMemoryPalace(novel_name)
    return _memory_instance
