import os
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger


class SkillLoader:
    def __init__(self, skills_dir: Optional[str] = None):
        if skills_dir is None:
            skills_dir = Path(__file__).parent / "novel_settings" / "skills"
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, str] = {}
        self._load_skills()
    
    def _load_skills(self):
        if not self.skills_dir.exists():
            logger.warning(f"[SkillLoader] 技能目录不存在: {self.skills_dir}")
            return
        
        skill_files = list(self.skills_dir.glob("*.md"))
        logger.info(f"[SkillLoader] 发现 {len(skill_files)} 个技能文件")
        
        for skill_file in skill_files:
            skill_name = skill_file.stem
            try:
                with open(skill_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.skills[skill_name] = content
                logger.info(f"[SkillLoader] 加载技能: {skill_name}")
            except Exception as e:
                logger.error(f"[SkillLoader] 加载技能失败 {skill_name}: {e}")
    
    def get_skill(self, skill_name: str) -> Optional[str]:
        return self.skills.get(skill_name)
    
    def list_skills(self) -> List[str]:
        return list(self.skills.keys())
    
    def get_all_skills(self) -> Dict[str, str]:
        return self.skills.copy()
    
    def build_system_prompt(self, skill_names: Optional[List[str]] = None) -> str:
        if skill_names is None:
            skill_names = self.list_skills()
        
        prompt_parts = []
        prompt_parts.append("你是一位专业的网文创作助手，拥有以下专业技能：\n")
        
        for skill_name in skill_names:
            skill_content = self.get_skill(skill_name)
            if skill_content:
                prompt_parts.append(f"\n## {skill_name}\n")
                prompt_parts.append(skill_content)
        
        prompt_parts.append("\n请根据以上技能指导，为用户提供专业的网文创作帮助。")
        
        return "\n".join(prompt_parts)


_skill_loader_instance: Optional[SkillLoader] = None


def get_skill_loader() -> SkillLoader:
    global _skill_loader_instance
    if _skill_loader_instance is None:
        _skill_loader_instance = SkillLoader()
    return _skill_loader_instance


__all__ = ["SkillLoader", "get_skill_loader"]
