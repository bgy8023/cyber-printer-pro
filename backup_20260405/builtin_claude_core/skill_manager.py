from enum import Enum
from .logger import logger

class WritingSkill(Enum):
    TOMATO = "番茄爆款"
    QIDIAN = "起点男频"
    SWEET = "女频甜文"
    SUSPENSE = "悬疑"

class SkillManager:
    def __init__(self):
        self.current_skill = WritingSkill.TOMATO

    def set_skill(self, skill: WritingSkill):
        self.current_skill = skill
        logger.info(f"🎯 已切换写作技能：{skill.value}")

    def get_prompt(self):
        if self.current_skill == WritingSkill.TOMATO:
            return "节奏快、爽点密、短段落、强情绪"
        if self.current_skill == WritingSkill.QIDIAN:
            return "宏大世界观、升级线清晰、长线爽点"
        if self.current_skill == WritingSkill.SWEET:
            return "甜宠、细腻、情绪流、细节拉满"
        if self.current_skill == WritingSkill.SUSPENSE:
            return "悬念前置、反转密集、氛围压抑"
        return ""

skill_manager = SkillManager()
