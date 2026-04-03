# 代码级硬约束一致性检查器
import re
from typing import Dict, List, Optional
from .logger import logger

class ConsistencyCheckResult:
    def __init__(self):
        self.passed: bool = True
        self.failed_items: List[str] = []
        self.rewrite_suggestion: str = ""

class HardRuleConsistencyChecker:
    """代码级硬约束校验器，不依赖LLM，绝对可靠"""
    def __init__(self):
        self.forbidden_keywords = [
            "违规题材", "敏感内容", "色情", "暴力", "政治", "违法",
            "AI", "作为人工智能", "我是AI", "语言模型"
        ]
        self.required_keywords: List[str] = []

    def load_rules_from_memory(self, character_names: List[str]):
        """从记忆宫殿中加载硬约束规则"""
        self.required_keywords = character_names
        logger.info(f"✅ 硬约束规则加载完成，核心人物：{self.required_keywords}")

    def check(self, content: str) -> ConsistencyCheckResult:
        """执行硬约束检查"""
        result = ConsistencyCheckResult()
        
        # 检查核心人物是否消失
        for name in self.required_keywords:
            if name and name not in content:
                result.passed = False
                result.failed_items.append(f"严重问题：核心人物「{name}」在本章中消失，人设崩塌")
        
        # 检查违规内容
        for keyword in self.forbidden_keywords:
            if keyword in content:
                result.passed = False
                result.failed_items.append(f"合规问题：内容包含禁止的「{keyword}」内容")
        
        # 检查内容长度
        if len(content.strip()) < 100:
            result.passed = False
            result.failed_items.append("内容过短，生成失败")
        
        if not result.passed:
            result.rewrite_suggestion = "请修复以下问题后重新生成：\n" + "\n".join(result.failed_items)
            logger.error(f"❌ 硬约束检查失败：{result.failed_items}")
        else:
            logger.info("✅ 硬约束检查通过")
        
        return result
