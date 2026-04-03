# memory_palace.py - 双层记忆宫殿系统
# 固定记忆 + 动态记忆双层架构，彻底解决吃书问题

import os
import json
import re
from typing import Dict, List, Optional, Any
from .logger import logger


class MemoryPalace:
    """
    双层记忆宫殿核心类
    固定记忆：人设档案、世界观设定、全书大纲（不可变）
    动态记忆：已生成章节内容、已埋设伏笔、剧情节点（自动更新）
    """
    
    def __init__(self, memory_dir: Optional[str] = None):
        # 固定记忆（不可变）
        self.fixed_memory: Dict[str, Any] = {
            "characters": {},      # 人物档案
            "world_setting": "",   # 世界观设定
            "full_outline": "",    # 全书大纲
            "chapter_outlines": {} # 各章大纲
        }
        
        # 动态记忆（自动更新）
        self.dynamic_memory: Dict[str, Any] = {
            "chapters": {},        # 已生成章节 {chapter_num: {"name": "", "content": "", "summary": ""}}
            "foreshadowing": [],   # 已埋设伏笔 [{"content": "", "chapter": num, "resolved": False}]
            "plot_nodes": [],      # 关键剧情节点
            "current_chapter": 0   # 当前生成到第几章
        }
        
        self.memory_dir = memory_dir
        if memory_dir:
            self._init_memory_dir(memory_dir)
        
        logger.info("✅ 双层记忆宫殿系统初始化完成")
    
    def _init_memory_dir(self, memory_dir: str):
        """初始化记忆目录"""
        if not os.path.exists(memory_dir):
            os.makedirs(memory_dir, exist_ok=True)
            logger.info(f"📂 创建记忆目录：{memory_dir}")
        
        # 尝试加载已保存的记忆
        self.load_from_disk()
    
    def bind_novel(self, novel_name: str, base_dir: str = "./novels"):
        """绑定小说，创建独立的记忆空间"""
        novel_dir = os.path.join(base_dir, novel_name)
        self.memory_dir = novel_dir
        self._init_memory_dir(novel_dir)
        logger.info(f"📚 绑定小说：{novel_name}，记忆目录：{novel_dir}")
    
    # ========== 固定记忆管理 ==========
    
    def set_character(self, char_name: str, char_info: str):
        """设置人物档案（固定记忆）"""
        self.fixed_memory["characters"][char_name] = char_info
        logger.info(f"👤 保存人物档案：{char_name}")
    
    def set_world_setting(self, setting: str):
        """设置世界观设定（固定记忆）"""
        self.fixed_memory["world_setting"] = setting
        logger.info("🌍 保存世界观设定")
    
    def set_full_outline(self, outline: str):
        """设置全书大纲（固定记忆）"""
        self.fixed_memory["full_outline"] = outline
        logger.info("📋 保存全书大纲")
    
    def set_chapter_outline(self, chapter_num: int, outline: str):
        """设置单章大纲（固定记忆）"""
        self.fixed_memory["chapter_outlines"][str(chapter_num)] = outline
        logger.info(f"📝 保存第{chapter_num}章大纲")
    
    def get_character(self, char_name: str) -> Optional[str]:
        """获取人物档案"""
        return self.fixed_memory["characters"].get(char_name)
    
    def get_all_characters(self) -> Dict[str, str]:
        """获取所有人物档案"""
        return self.fixed_memory["characters"].copy()
    
    def get_world_setting(self) -> str:
        """获取世界观设定"""
        return self.fixed_memory["world_setting"]
    
    def get_full_outline(self) -> str:
        """获取全书大纲"""
        return self.fixed_memory["full_outline"]
    
    def get_chapter_outline(self, chapter_num: int) -> Optional[str]:
        """获取单章大纲"""
        return self.fixed_memory["chapter_outlines"].get(str(chapter_num))
    
    # ========== 动态记忆管理 ==========
    
    def add_chapter(self, chapter_num: int, chapter_name: str, content: str, summary: str = ""):
        """添加已生成章节（动态记忆）"""
        self.dynamic_memory["chapters"][str(chapter_num)] = {
            "name": chapter_name,
            "content": content,
            "summary": summary or self._auto_summarize(content)
        }
        self.dynamic_memory["current_chapter"] = max(
            self.dynamic_memory["current_chapter"],
            chapter_num
        )
        logger.info(f"📖 添加第{chapter_num}章记忆：{chapter_name}")
    
    def add_foreshadowing(self, content: str, chapter_num: int):
        """添加埋设的伏笔（动态记忆）"""
        self.dynamic_memory["foreshadowing"].append({
            "content": content,
            "chapter": chapter_num,
            "resolved": False
        })
        logger.info(f"🎯 添加伏笔（第{chapter_num}章）：{content[:50]}...")
    
    def resolve_foreshadowing(self, foreshadowing_idx: int):
        """标记伏笔已回收（动态记忆）"""
        if 0 <= foreshadowing_idx < len(self.dynamic_memory["foreshadowing"]):
            self.dynamic_memory["foreshadowing"][foreshadowing_idx]["resolved"] = True
            logger.info(f"✅ 伏笔已回收：{foreshadowing_idx}")
    
    def add_plot_node(self, node_content: str, chapter_num: int):
        """添加关键剧情节点（动态记忆）"""
        self.dynamic_memory["plot_nodes"].append({
            "content": node_content,
            "chapter": chapter_num
        })
        logger.info(f"📍 添加剧情节点（第{chapter_num}章）")
    
    def get_chapter(self, chapter_num: int) -> Optional[Dict]:
        """获取章节内容"""
        return self.dynamic_memory["chapters"].get(str(chapter_num))
    
    def get_all_chapters(self) -> Dict[str, Dict]:
        """获取所有章节"""
        return self.dynamic_memory["chapters"].copy()
    
    def get_unresolved_foreshadowing(self) -> List[Dict]:
        """获取未回收的伏笔"""
        return [f for f in self.dynamic_memory["foreshadowing"] if not f["resolved"]]
    
    def get_current_chapter(self) -> int:
        """获取当前章节数"""
        return self.dynamic_memory["current_chapter"]
    
    # ========== 提示词生成 ==========
    
    def get_full_fixed_prompt(self) -> str:
        """获取完整的固定记忆提示词"""
        prompt_parts = ["【固定记忆 - 不可变更】"]
        
        # 人物档案
        if self.fixed_memory["characters"]:
            prompt_parts.append("\n## 人物档案")
            for name, info in self.fixed_memory["characters"].items():
                prompt_parts.append(f"- {name}: {info}")
        
        # 世界观设定
        if self.fixed_memory["world_setting"]:
            prompt_parts.append("\n## 世界观设定")
            prompt_parts.append(self.fixed_memory["world_setting"])
        
        # 全书大纲
        if self.fixed_memory["full_outline"]:
            prompt_parts.append("\n## 全书大纲")
            prompt_parts.append(self.fixed_memory["full_outline"])
        
        return "\n".join(prompt_parts)
    
    def get_previous_plot_summary(self, max_chapters: int = 5) -> str:
        """获取前序剧情摘要"""
        chapters = sorted(
            [(int(num), data) for num, data in self.dynamic_memory["chapters"].items()],
            key=lambda x: x[0]
        )
        
        if not chapters:
            return "【前序剧情】暂无已生成章节"
        
        recent_chapters = chapters[-max_chapters:]
        prompt_parts = ["【前序剧情摘要】"]
        
        for chapter_num, data in recent_chapters:
            prompt_parts.append(f"\n## 第{chapter_num}章：{data['name']}")
            prompt_parts.append(data["summary"])
        
        return "\n".join(prompt_parts)
    
    def get_unresolved_foreshadowing_prompt(self) -> str:
        """获取未回收伏笔的提示词"""
        unresolved = self.get_unresolved_foreshadowing()
        if not unresolved:
            return "【未回收伏笔】暂无"
        
        prompt_parts = ["【未回收伏笔】"]
        for i, f in enumerate(unresolved):
            prompt_parts.append(f"{i+1}. (第{f['chapter']}章) {f['content']}")
        
        return "\n".join(prompt_parts)
    
    # ========== 兼容原有接口 ==========
    
    def load_memory(self, memory_dir: str):
        """兼容原有 load_memory 接口，从目录加载记忆"""
        self.memory_dir = memory_dir
        if not os.path.exists(memory_dir):
            logger.warning(f"⚠️ 记忆目录不存在：{memory_dir}")
            return
        
        logger.info(f"📂 从兼容接口加载记忆：{memory_dir}")
        for file in sorted(os.listdir(memory_dir)):
            if not file.endswith(".md"):
                continue
            
            file_path = os.path.join(memory_dir, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self._parse_compatible_memory_file(file, content)
            except Exception as e:
                logger.error(f"❌ 记忆文件加载失败：{file}，错误：{str(e)}", exc_info=True)
    
    def _parse_compatible_memory_file(self, filename: str, content: str):
        """解析兼容格式的记忆文件"""
        # 尝试提取主角
        main_char_match = re.search(r"主角[:：]\s*([^\n]+)", content)
        if main_char_match:
            self.set_character("主角", main_char_match.group(1).strip())
        
        # 尝试提取反派
        villain_match = re.search(r"反派[:：]\s*([^\n]+)", content)
        if villain_match:
            self.set_character("反派", villain_match.group(1).strip())
        
        # 尝试提取世界观
        world_setting_match = re.search(r"世界观[:：]\s*([\s\S]+?)(?=\n## |\n# |$)", content)
        if world_setting_match:
            self.set_world_setting(world_setting_match.group(1).strip())
        
        # 提取伏笔
        foreshadowing_list = re.findall(r"伏笔[:：]\s*([^\n]+)", content)
        # 尝试从文件名推断章节号
        chapter_num = 0
        chapter_match = re.search(r"第(\d+)章", filename)
        if chapter_match:
            chapter_num = int(chapter_match.group(1))
        for f in foreshadowing_list:
            self.add_foreshadowing(f, chapter_num)
        
        # 保存原始内容作为通用记忆
        if "人物" in filename or "人设" in filename:
            self.set_character(filename.replace(".md", ""), content)
        elif "世界观" in filename or "设定" in filename:
            self.set_world_setting(content)
        elif "大纲" in filename:
            self.set_full_outline(content)
    
    # ========== 持久化 ==========
    
    def save_to_disk(self):
        """保存记忆到磁盘"""
        if not self.memory_dir:
            logger.warning("⚠️ 未设置记忆目录，无法保存")
            return
        
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # 保存固定记忆
        fixed_path = os.path.join(self.memory_dir, "fixed_memory.json")
        with open(fixed_path, "w", encoding="utf-8") as f:
            json.dump(self.fixed_memory, f, ensure_ascii=False, indent=2)
        
        # 保存动态记忆
        dynamic_path = os.path.join(self.memory_dir, "dynamic_memory.json")
        with open(dynamic_path, "w", encoding="utf-8") as f:
            json.dump(self.dynamic_memory, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 记忆已保存到：{self.memory_dir}")
    
    def load_from_disk(self):
        """从磁盘加载记忆"""
        if not self.memory_dir:
            return
        
        # 保存原始状态，用于回退
        original_fixed_memory = self.fixed_memory.copy()
        original_dynamic_memory = self.dynamic_memory.copy()
        
        # 加载固定记忆
        fixed_path = os.path.join(self.memory_dir, "fixed_memory.json")
        if os.path.exists(fixed_path):
            try:
                with open(fixed_path, "r", encoding="utf-8") as f:
                    loaded_memory = json.load(f)
                # 验证加载的数据结构
                if isinstance(loaded_memory, dict) and all(key in loaded_memory for key in ["characters", "world_setting", "full_outline", "chapter_outlines"]):
                    self.fixed_memory = loaded_memory
                    logger.info("✅ 固定记忆已加载")
                else:
                    logger.error("❌ 固定记忆数据结构错误，使用默认值")
                    # 回退到原始状态
                    self.fixed_memory = original_fixed_memory
            except Exception as e:
                logger.error(f"❌ 加载固定记忆失败：{str(e)}")
                # 回退到原始状态
                self.fixed_memory = original_fixed_memory
        
        # 加载动态记忆
        dynamic_path = os.path.join(self.memory_dir, "dynamic_memory.json")
        if os.path.exists(dynamic_path):
            try:
                with open(dynamic_path, "r", encoding="utf-8") as f:
                    loaded_memory = json.load(f)
                # 验证加载的数据结构
                if isinstance(loaded_memory, dict) and all(key in loaded_memory for key in ["chapters", "foreshadowing", "plot_nodes", "current_chapter"]):
                    self.dynamic_memory = loaded_memory
                    logger.info("✅ 动态记忆已加载")
                else:
                    logger.error("❌ 动态记忆数据结构错误，使用默认值")
                    # 回退到原始状态
                    self.dynamic_memory = original_dynamic_memory
            except Exception as e:
                logger.error(f"❌ 加载动态记忆失败：{str(e)}")
                # 回退到原始状态
                self.dynamic_memory = original_dynamic_memory
    
    def _auto_summarize(self, content: str, max_length: int = 500) -> str:
        """自动生成章节摘要（改进版本）"""
        # 分割段落
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        
        if not paragraphs:
            return ""
        
        # 优先选择段落长度适中的内容
        # 通常第一章或重要段落会包含关键信息
        candidate_paragraphs = []
        
        # 先选择第一段（通常是章节开头）
        if paragraphs:
            candidate_paragraphs.append(paragraphs[0])
        
        # 再选择一些长度适中的段落
        for para in paragraphs[1:]:
            if 50 <= len(para) <= 300:  # 选择长度适中的段落
                candidate_paragraphs.append(para)
            if len(candidate_paragraphs) >= 3:
                break
        
        # 如果不够3段，再补一些
        if len(candidate_paragraphs) < 3 and len(paragraphs) > 3:
            for para in paragraphs[len(candidate_paragraphs):]:
                candidate_paragraphs.append(para)
                if len(candidate_paragraphs) >= 3:
                    break
        
        summary = "\n".join(candidate_paragraphs)
        
        if len(summary) > max_length:
            # 更智能的截断，避免在句子中间截断
            summary = summary[:max_length]
            # 找到最后一个句号、感叹号或问号
            last_punctuation = max(summary.rfind('。'), summary.rfind('！'), summary.rfind('？'), summary.rfind('.'), summary.rfind('!'), summary.rfind('?'))
            if last_punctuation > max_length * 0.8:
                summary = summary[:last_punctuation + 1]
            else:
                summary = summary + "..."
        
        return summary


# 全局单例
_memory_palace: Optional[MemoryPalace] = None


def get_memory_palace(memory_dir: Optional[str] = None) -> MemoryPalace:
    """获取记忆宫殿单例"""
    global _memory_palace
    if _memory_palace is None:
        _memory_palace = MemoryPalace(memory_dir)
    elif memory_dir is not None and _memory_palace.memory_dir != memory_dir:
        # 如果提供了新的 memory_dir 且与当前不同，更新单例
        _memory_palace.memory_dir = memory_dir
        _memory_palace._init_memory_dir(memory_dir)
    return _memory_palace
