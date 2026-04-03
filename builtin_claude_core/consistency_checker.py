import re
from typing import Dict, List, Optional
from .logger import logger

class ConsistencyCheckResult:
    def __init__(self):
        self.passed: bool = True
        self.failed_items: List[str] = []
        self.rewrite_suggestion: str = ""

class HardRuleConsistencyChecker:
    """
    代码级硬约束一致性检查器
    不依赖LLM，绝对可靠，先做硬检查，再做LLM检查
    """
    def __init__(self):
        self.forbidden_keywords = ["违规题材", "敏感内容", "禁止出现的词汇"]
        self.required_keywords: List[str] = []

    def load_rules_from_memory(self, memory_dir: str):
        """从记忆宫殿中加载硬约束规则"""
        import os
        character_file = os.path.join(memory_dir, "01-人物档案.md")
        if os.path.exists(character_file):
            with open(character_file, "r", encoding="utf-8") as f:
                content = f.read()
                # 提取核心人物名
                character_matches = re.findall(r"主角：(.+?) -", content)
                self.required_keywords.extend([name.strip() for name in character_matches if name.strip()])
        logger.info(f"✅ 硬约束规则加载完成，核心人物：{self.required_keywords}")

    def check(self, content: str) -> ConsistencyCheckResult:
        """执行硬约束检查"""
        result = ConsistencyCheckResult()
        
        # 1. 检查核心人物是否消失
        for name in self.required_keywords:
            if name and name not in content:
                result.passed = False
                result.failed_items.append(f"严重问题：核心人物「{name}」在本章中消失")
        
        # 2. 检查违规内容
        for keyword in self.forbidden_keywords:
            if keyword in content:
                result.passed = False
                result.failed_items.append(f"合规问题：内容包含禁止的「{keyword}」")
        
        if not result.passed:
            result.rewrite_suggestion = "请修复以下问题后再生成：\n" + "\n".join(result.failed_items)
        
        return result
