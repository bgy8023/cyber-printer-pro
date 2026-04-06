#!/usr/bin/env python3
"""
自我迭代核心引擎
实现持续自我优化机制
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class ImprovementCategory(Enum):
    """改进分类"""
    PERFORMANCE = "performance"
    SECURITY = "security"
    FUNCTIONALITY = "functionality"
    USABILITY = "usability"
    RELIABILITY = "reliability"


@dataclass
class Improvement:
    """改进记录"""
    id: str
    category: ImprovementCategory
    description: str
    status: str = "pending"
    priority: int = 2
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    result: Optional[str] = None


class SelfImprover:
    """自我迭代引擎"""
    
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            project_root = Path(__file__).parent
        
        self.project_root = project_root
        self.improvements_file = project_root / ".ai_improvements.json"
        self.improvements: Dict[str, Improvement] = {}
        self._load_improvements()
    
    def _load_improvements(self):
        """加载改进记录"""
        if self.improvements_file.exists():
            try:
                with open(self.improvements_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for imp_id, imp_data in data.items():
                        imp = Improvement(
                            id=imp_data["id"],
                            category=ImprovementCategory(imp_data["category"]),
                            description=imp_data["description"],
                            status=imp_data.get("status", "pending"),
                            priority=imp_data.get("priority", 2),
                            created_at=imp_data.get("created_at", time.time()),
                            completed_at=imp_data.get("completed_at"),
                            result=imp_data.get("result")
                        )
                        self.improvements[imp_id] = imp
            except Exception:
                pass
    
    def _save_improvements(self):
        """保存改进记录"""
        data = {}
        for imp_id, imp in self.improvements.items():
            data[imp_id] = {
                "id": imp.id,
                "category": imp.category.value,
                "description": imp.description,
                "status": imp.status,
                "priority": imp.priority,
                "created_at": imp.created_at,
                "completed_at": imp.completed_at,
                "result": imp.result
            }
        
        with open(self.improvements_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_improvement(self, category: ImprovementCategory, description: str, priority: int = 2) -> str:
        """添加改进"""
        import uuid
        imp_id = str(uuid.uuid4())[:8]
        imp = Improvement(
            id=imp_id,
            category=category,
            description=description,
            priority=priority
        )
        self.improvements[imp_id] = imp
        self._save_improvements()
        return imp_id
    
    def get_improvement(self, imp_id: str) -> Optional[Improvement]:
        """获取改进"""
        return self.improvements.get(imp_id)
    
    def list_improvements(self, status: Optional[str] = None) -> List[Improvement]:
        """列出改进"""
        improvements = list(self.improvements.values())
        if status:
            improvements = [imp for imp in improvements if imp.status == status]
        return sorted(improvements, key=lambda x: (-x.priority, x.created_at))
    
    def complete_improvement(self, imp_id: str, result: str) -> bool:
        """完成改进"""
        imp = self.improvements.get(imp_id)
        if imp:
            imp.status = "completed"
            imp.completed_at = time.time()
            imp.result = result
            self._save_improvements()
            return True
        return False
    
    def get_next_improvement(self) -> Optional[Improvement]:
        """获取下一个待处理的改进"""
        pending = self.list_improvements(status="pending")
        if pending:
            return pending[0]
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        total = len(self.improvements)
        pending = len(self.list_improvements(status="pending"))
        completed = len(self.list_improvements(status="completed"))
        
        categories = {}
        for imp in self.improvements.values():
            cat = imp.category.value
            if cat not in categories:
                categories[cat] = {"total": 0, "pending": 0, "completed": 0}
            categories[cat]["total"] += 1
            if imp.status == "pending":
                categories[cat]["pending"] += 1
            elif imp.status == "completed":
                categories[cat]["completed"] += 1
        
        return {
            "total": total,
            "pending": pending,
            "completed": completed,
            "categories": categories
        }


# 全局单例
_self_improver: Optional[SelfImprover] = None


def get_self_improver() -> SelfImprover:
    """获取全局自我迭代引擎"""
    global _self_improver
    if _self_improver is None:
        _self_improver = SelfImprover()
    return _self_improver


__all__ = [
    "ImprovementCategory",
    "Improvement",
    "SelfImprover",
    "get_self_improver"
]
