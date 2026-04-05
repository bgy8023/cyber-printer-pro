"""
人设校验工具 - 检查小说内容是否符合人物设定
"""

import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from loguru import logger


class CharacterValidator:
    """人设校验器"""
    
    def __init__(self, character_file: Optional[str] = None):
        self.character_file = character_file
        self.characters = {}
        if character_file:
            self._load_characters(character_file)
    
    def _load_characters(self, file_path: str):
        """从文件加载人物设定"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.characters = self._parse_character_content(content)
            logger.info(f"[CharacterValidator] 已加载 {len(self.characters)} 个人物设定")
        except Exception as e:
            logger.error(f"[CharacterValidator] 加载人物设定失败: {e}")
    
    def _parse_character_content(self, content: str) -> Dict:
        """解析人物设定内容"""
        characters = {}
        lines = content.split('\n')
        
        current_char = None
        for line in lines:
            line = line.strip()
            
            char_match = re.match(r'^[#\*]*\s*([^\s#*].+?)\s*[：:]\s*', line)
            if char_match and len(line) < 50:
                char_name = char_match.group(1).strip()
                if char_name and len(char_name) < 20:
                    current_char = char_name
                    characters[current_char] = {'name': current_char, 'traits': [], 'dialogue_style': ''}
            elif current_char:
                if line:
                    characters[current_char]['traits'].append(line)
        
        return characters
    
    def validate_content(
        self, 
        content: str, 
        chapter_num: int = 1
    ) -> Dict:
        """校验章节内容的人设一致性"""
        results = {
            'chapter_num': chapter_num,
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'character_mentions': {}
        }
        
        if not self.characters:
            results['warnings'].append("未加载人物设定，跳过详细校验")
            return results
        
        mentioned_chars = self._find_mentioned_characters(content)
        results['character_mentions'] = mentioned_chars
        
        for char_name, mention_count in mentioned_chars.items():
            if char_name in self.characters:
                issues = self._check_character_consistency(content, char_name)
                if issues:
                    results['issues'].extend(issues)
                    results['is_valid'] = False
            else:
                results['warnings'].append(f"未设定的人物: {char_name}（出现 {mention_count} 次）")
        
        return results
    
    def _find_mentioned_characters(self, content: str) -> Dict[str, int]:
        """找出内容中提到的人物"""
        mentions = {}
        
        for char_name in self.characters.keys():
            count = content.count(char_name)
            if count > 0:
                mentions[char_name] = count
        
        return mentions
    
    def _check_character_consistency(self, content: str, char_name: str) -> List[str]:
        """检查单个人物的一致性"""
        issues = []
        
        char_data = self.characters[char_name]
        
        dialogue_pattern = f'[{char_name}][：:](.+?)(?=[\\n\\r]|$)'
        dialogues = re.findall(dialogue_pattern, content)
        
        if dialogues:
            char_traits = ' '.join(char_data['traits']).lower()
            
            for dialogue in dialogues[:3]:
                dialogue_lower = dialogue.lower()
                
                if '温和' in char_traits and ('骂' in dialogue_lower or '滚' in dialogue_lower):
                    issues.append(f"{char_name}: 对话风格与温和人设不符")
                
                if '高冷' in char_traits and len(dialogue) > 50:
                    issues.append(f"{char_name}: 高冷人设话太多")
        
        return issues
    
    def get_report(self, results: Dict) -> str:
        """生成校验报告"""
        report = []
        report.append("=" * 60)
        report.append(f"人设校验报告 - 第 {results['chapter_num']} 章")
        report.append("=" * 60)
        
        if results['is_valid']:
            report.append("✅ 人设一致性校验通过")
        else:
            report.append("❌ 发现人设问题")
        
        if results['character_mentions']:
            report.append(f"\n📊 人物提及统计:")
            for char, count in results['character_mentions'].items():
                report.append(f"  - {char}: {count} 次")
        
        if results['issues']:
            report.append(f"\n❌ 问题列表:")
            for issue in results['issues']:
                report.append(f"  - {issue}")
        
        if results['warnings']:
            report.append(f"\n⚠️ 警告列表:")
            for warning in results['warnings']:
                report.append(f"  - {warning}")
        
        report.append("=" * 60)
        return '\n'.join(report)


__all__ = ["CharacterValidator"]
