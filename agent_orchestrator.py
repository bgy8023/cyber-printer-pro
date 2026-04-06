#!/usr/bin/env python3
"""
子智能体编排系统（Handoffs）
参考 OpenAI Agents SDK 的 Handoffs 概念
"""
import json
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class AgentRole(Enum):
    """智能体角色"""
    GENERAL = "general"
    CODER = "coder"
    RESEARCHER = "researcher"
    DEBUGGER = "debugger"
    PLANNER = "planner"


@dataclass
class Agent:
    """子智能体"""
    name: str
    role: AgentRole
    description: str
    system_prompt: str
    tools: List[str] = field(default_factory=list)
    handoff_targets: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role.value,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "handoff_targets": self.handoff_targets
        }


class AgentOrchestrator:
    """智能体编排器"""
    
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._current_agent: Optional[str] = None
        self._register_default_agents()
    
    def _register_default_agents(self):
        """注册默认智能体"""
        self.register_agent(Agent(
            name="General",
            role=AgentRole.GENERAL,
            description="通用智能体，处理日常对话",
            system_prompt="""你是一个通用 AI 助手，可以帮助用户处理各种日常任务。
你可以：
1. 回答问题
2. 进行对话
3. 根据需要，将任务转交给专门的智能体

如果你觉得任务需要特定的专业技能，可以使用 handoff 功能转交给专门的智能体。""",
            handoff_targets=["Coder", "Researcher", "Planner"]
        ))
        
        self.register_agent(Agent(
            name="Coder",
            role=AgentRole.CODER,
            description="代码专家，专注于编程任务",
            system_prompt="""你是一个专业的代码专家，专注于编程任务。
你可以：
1. 编写代码
2. 调试代码
3. 代码审查
4. 技术架构设计

你的主要工具包括：
- 文件读取和编辑
- 命令执行
- git 操作
- 项目分析

你可以根据需要将任务转交给 Debugger 或 Planner。""",
            tools=["read_file", "write_file", "execute_shell", "git"],
            handoff_targets=["Debugger", "Planner", "General"]
        ))
        
        self.register_agent(Agent(
            name="Researcher",
            role=AgentRole.RESEARCHER,
            description="研究员，专注于信息搜索和分析",
            system_prompt="""你是一个专业的研究员，专注于信息搜索和分析。
你可以：
1. 搜索网络信息
2. 分析资料
3. 撰写报告
4. 提供参考资料

你的主要工具包括：
- 网络搜索
- 网页抓取
- 文件分析

你可以根据需要将任务转交给 Planner 或 General。""",
            tools=["web_search", "web_fetch"],
            handoff_targets=["Planner", "General"]
        ))
        
        self.register_agent(Agent(
            name="Debugger",
            role=AgentRole.DEBUGGER,
            description="调试专家，专注于问题排查",
            system_prompt="""你是一个专业的调试专家，专注于问题排查。
你可以：
1. 分析错误日志
2. 复现问题
3. 提出修复方案
4. 验证修复效果

你的主要工具包括：
- 日志分析
- 调试命令
- 测试执行

你可以根据需要将任务转交给 Coder 或 General。""",
            tools=["read_file", "execute_shell"],
            handoff_targets=["Coder", "General"]
        ))
        
        self.register_agent(Agent(
            name="Planner",
            role=AgentRole.PLANNER,
            description="规划专家，专注于任务规划",
            system_prompt="""你是一个专业的规划专家，专注于任务规划。
你可以：
1. 分析需求
2. 制定计划
3. 分解任务
4. 跟踪进度

你的主要工具包括：
- 项目分析
- 任务管理

你可以根据需要将任务转交给 Coder、Researcher 或 General。""",
            tools=["project_info"],
            handoff_targets=["Coder", "Researcher", "General"]
        ))
    
    def register_agent(self, agent: Agent):
        """注册智能体"""
        self._agents[agent.name] = agent
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """获取智能体"""
        return self._agents.get(name)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有智能体"""
        agents_list = []
        for name, agent in self._agents.items():
            agents_list.append({
                "name": agent.name,
                "role": agent.role.value,
                "description": agent.description,
                "tools": agent.tools,
                "handoff_targets": agent.handoff_targets
            })
        return agents_list
    
    def get_current_agent(self) -> Optional[Agent]:
        """获取当前智能体"""
        if self._current_agent:
            return self._agents.get(self._current_agent)
        return None
    
    def set_current_agent(self, name: str) -> bool:
        """设置当前智能体"""
        if name in self._agents:
            self._current_agent = name
            return True
        return False
    
    def can_handoff(self, from_agent: str, to_agent: str) -> bool:
        """检查是否可以转交"""
        agent = self._agents.get(from_agent)
        if not agent:
            return False
        return to_agent in agent.handoff_targets
    
    def handoff(self, from_agent: str, to_agent: str, reason: str = "") -> Dict[str, Any]:
        """转交任务"""
        if not self.can_handoff(from_agent, to_agent):
            return {
                "success": False,
                "error": f"Cannot handoff from {from_agent} to {to_agent}"
            }
        
        self._current_agent = to_agent
        target_agent = self._agents[to_agent]
        
        return {
            "success": True,
            "from": from_agent,
            "to": to_agent,
            "reason": reason,
            "agent": target_agent.to_dict()
        }
    
    def get_agent_system_prompt(self, name: Optional[str] = None) -> Optional[str]:
        """获取智能体的系统提示词"""
        agent_name = name or self._current_agent
        if not agent_name:
            return None
        agent = self._agents.get(agent_name)
        if agent:
            return agent.system_prompt
        return None


# 全局单例
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """获取全局编排器"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


__all__ = [
    "AgentRole",
    "Agent",
    "AgentOrchestrator",
    "get_orchestrator"
]
