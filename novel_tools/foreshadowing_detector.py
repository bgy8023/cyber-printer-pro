"""
伏笔检测工具 - 检测和管理小说中的伏笔
"""

import re
from typing import Dict, List, Optional, Tuple
from loguru import logger


class ForeshadowingDetector:
    """伏笔检测器"""
    
    def __init__(self):
        self.foreshadowings = []
        self.resolved_foreshadowings = []
    
    def detect_foreshadowings(
        self, 
        content: str, 
        chapter_num: int = 1
    ) -> Dict:
        """检测章节中的伏笔"""
        results = {
            'chapter_num': chapter_num,
            'detected_foreshadowings': [],
            'potential_foreshadowings': [],
            'foreshadowing_density': 0.0,
            'recommendations': []
        }
        
        detected = self._find_foreshadowing_patterns(content)
        results['detected_foreshadowings'] = detected
        
        potential = self._find_potential_foreshadowings(content)
        results['potential_foreshadowings'] = potential
        
        total_words = len(content)
        total_foreshadowings = len(detected) + len(potential)
        if total_words > 0:
            results['foreshadowing_density'] = total_foreshadowings / (total_words / 1000)
        
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _find_foreshadowing_patterns(self, content: str) -> List[Dict]:
        """查找明确的伏笔模式"""
        foreshadowings = []
        
        patterns = [
            (r'(.{10,30}?)(日后|将来|以后|总有一天|未来)(.{10,30}?)', '时间类伏笔'),
            (r'(.{10,30}?)(似乎|好像|仿佛|隐约|感觉)(.{10,30}?)', '不确定类伏笔'),
            (r'(.{10,30}?)(秘密|隐藏|隐瞒|不知道|不明白)(.{10,30}?)', '秘密类伏笔'),
            (r'(.{10,30}?)(有一天|将来某一天|到时候)(.{10,30}?)', '预言类伏笔'),
            (r'(.{10,30}?)(记住|别忘了|以后你会知道)(.{10,30}?)', '提醒类伏笔'),
        ]
        
        for pattern, foreshadow_type in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                full_text = ''.join(match)
                if len(full_text) < 100:
                    foreshadowings.append({
                        'type': foreshadow_type,
                        'content': full_text,
                        'chapter': None
                    })
        
        return foreshadowings
    
    def _find_potential_foreshadowings(self, content: str) -> List[Dict]:
        """查找潜在的伏笔"""
        potential = []
        
        item_patterns = [
            r'(.{5,20}?)(玉佩|项链|戒指|画卷|书信|信物|神秘)(.{5,20}?)',
            r'(.{5,20}?)(奇怪|异常|不对劲|有问题)(.{5,20}?)',
            r'(.{5,20}?)(传说|传闻|据说|传言)(.{5,20}?)',
        ]
        
        for pattern in item_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                full_text = ''.join(match)
                if len(full_text) < 80:
                    potential.append({
                        'type': '潜在伏笔',
                        'content': full_text,
                        'confidence': 'medium'
                    })
        
        return potential[:10]
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """生成伏笔建议"""
        recommendations = []
        
        density = results['foreshadowing_density']
        
        if density < 0.5:
            recommendations.append("伏笔密度偏低，建议增加 1-2 个伏笔")
        elif density > 3.0:
            recommendations.append("伏笔密度偏高，建议减少或合并一些伏笔")
        else:
            recommendations.append("伏笔密度适中，继续保持")
        
        if len(results['detected_foreshadowings']) == 0:
            recommendations.append("未检测到明确伏笔，建议埋设 1-2 个伏笔")
        
        if len(results['potential_foreshadowings']) > 5:
            recommendations.append("潜在伏笔较多，考虑将部分转化为明确伏笔")
        
        return recommendations
    
    def check_resolution(
        self, 
        current_content: str, 
        previous_foreshadowings: List[Dict]
    ) -> Dict:
        """检查伏笔回收情况"""
        results = {
            'resolved': [],
            'unresolved': [],
            'new_foreshadowings': []
        }
        
        for foreshadow in previous_foreshadowings:
            content = foreshadow.get('content', '')
            keywords = self._extract_keywords(content)
            
            resolved = False
            for keyword in keywords:
                if keyword and len(keyword) > 2:
                    if keyword in current_content:
                        resolved = True
                        break
            
            if resolved:
                results['resolved'].append(foreshadow)
            else:
                results['unresolved'].append(foreshadow)
        
        return results
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = []
        
        words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
        for word in words:
            if word not in keywords:
                keywords.append(word)
        
        return keywords[:5]
    
    def get_report(self, results: Dict) -> str:
        """生成检测报告"""
        report = []
        report.append("=" * 60)
        report.append(f"伏笔检测报告 - 第 {results['chapter_num']} 章")
        report.append("=" * 60)
        
        report.append(f"📊 伏笔密度: {results['foreshadowing_density']:.2f} 个/千字")
        
        if results['detected_foreshadowings']:
            report.append(f"\n🔍 检测到的伏笔 ({len(results['detected_foreshadowings'])} 个):")
            for i, fs in enumerate(results['detected_foreshadowings'], 1):
                report.append(f"  {i}. [{fs['type']}] {fs['content']}")
        
        if results['potential_foreshadowings']:
            report.append(f"\n💡 潜在伏笔 ({len(results['potential_foreshadowings'])} 个):")
            for i, fs in enumerate(results['potential_foreshadowings'], 1):
                report.append(f"  {i}. {fs['content']}")
        
        if results['recommendations']:
            report.append(f"\n💬 建议:")
            for rec in results['recommendations']:
                report.append(f"  - {rec}")
        
        report.append("=" * 60)
        return '\n'.join(report)


__all__ = ["ForeshadowingDetector"]
