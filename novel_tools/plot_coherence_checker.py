"""
剧情连贯检测工具 - 检查小说内容的剧情连贯性
"""

import re
from typing import Dict, List, Optional
from loguru import logger


class PlotCoherenceChecker:
    """剧情连贯检测器"""
    
    def __init__(self):
        self.plot_points = []
        self.previous_content = ""
    
    def check_coherence(
        self, 
        content: str, 
        chapter_num: int = 1,
        previous_chapters: Optional[List[str]] = None
    ) -> Dict:
        """检查章节内容的剧情连贯性"""
        results = {
            'chapter_num': chapter_num,
            'is_coherent': True,
            'issues': [],
            'warnings': [],
            'plot_summary': '',
            'key_events': []
        }
        
        key_events = self._extract_key_events(content)
        results['key_events'] = key_events
        
        if previous_chapters:
            coherence_issues = self._check_continuity(content, previous_chapters)
            if coherence_issues:
                results['issues'].extend(coherence_issues)
                results['is_coherent'] = False
        
        plot_warnings = self._check_plot_quality(content)
        if plot_warnings:
            results['warnings'].extend(plot_warnings)
        
        results['plot_summary'] = self._generate_plot_summary(content, key_events)
        
        return results
    
    def _extract_key_events(self, content: str) -> List[str]:
        """提取关键事件"""
        events = []
        
        patterns = [
            r'(.{20,50}?[！。!?])(?=[\\s\\n]|$)',
        ]
        
        sentences = re.split(r'[！。!?]', content)
        
        for sentence in sentences[:20]:
            sentence = sentence.strip()
            if len(sentence) > 10:
                if any(keyword in sentence for keyword in 
                       ['杀', '死', '突破', '获得', '得到', '发现', '知道', 
                        '明白', '醒悟', '震惊', '愤怒', '高兴', '喜', '悲']):
                    events.append(sentence)
        
        return events[:10]
    
    def _check_continuity(self, content: str, previous_chapters: List[str]) -> List[str]:
        """检查与前序章节的连续性"""
        issues = []
        
        if not previous_chapters:
            return issues
        
        previous_content = '\n'.join(previous_chapters[-2:])
        
        names_in_previous = self._extract_names(previous_content)
        names_in_current = self._extract_names(content)
        
        for name in names_in_previous:
            if name not in names_in_current and len(name) > 1:
                if previous_content.count(name) > 5:
                    issues.append(f"重要人物「{name}」在前序章节频繁出现，本章未提及")
        
        return issues
    
    def _extract_names(self, content: str) -> List[str]:
        """提取可能的人名"""
        names = []
        
        patterns = [
            r'[「\"](.{2,4})[」\"]：',
            r'(.{2,4})说：',
            r'(.{2,4})心想：',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) <= 4 and match not in names:
                    names.append(match)
        
        return list(set(names))
    
    def _check_plot_quality(self, content: str) -> List[str]:
        """检查剧情质量"""
        warnings = []
        
        paragraphs = content.split('\n\n')
        
        if len(paragraphs) < 3:
            warnings.append("段落太少，可能影响阅读体验")
        
        short_paragraphs = [p for p in paragraphs if len(p.strip()) < 20]
        if len(short_paragraphs) > len(paragraphs) * 0.5:
            warnings.append("短句过多，可能影响剧情连贯性")
        
        dialogue_count = content.count('：')
        if dialogue_count > len(content) / 50:
            warnings.append("对话占比过高，可能影响叙事节奏")
        
        return warnings
    
    def _generate_plot_summary(self, content: str, key_events: List[str]) -> str:
        """生成剧情摘要"""
        summary_parts = []
        
        if key_events:
            summary_parts.append("本章关键事件：")
            for i, event in enumerate(key_events[:5], 1):
                summary_parts.append(f"  {i}. {event}")
        
        return '\n'.join(summary_parts)
    
    def get_report(self, results: Dict) -> str:
        """生成检测报告"""
        report = []
        report.append("=" * 60)
        report.append(f"剧情连贯检测报告 - 第 {results['chapter_num']} 章")
        report.append("=" * 60)
        
        if results['is_coherent']:
            report.append("✅ 剧情连贯性检测通过")
        else:
            report.append("❌ 发现剧情连贯性问题")
        
        if results['key_events']:
            report.append(f"\n📋 关键事件:")
            for event in results['key_events']:
                report.append(f"  - {event}")
        
        if results['plot_summary']:
            report.append(f"\n📝 剧情摘要:")
            report.append(results['plot_summary'])
        
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


__all__ = ["PlotCoherenceChecker"]
