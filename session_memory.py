#!/usr/bin/env python3
"""
持久化会话记忆系统
参考 DeerFlow 2.0 的长期记忆和 OpenClaw 的持久化记忆
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", time.time())
        )


@dataclass
class KeyMemory:
    """关键记忆（重要信息提取）"""
    content: str
    importance: int = 1
    timestamp: float = field(default_factory=time.time)
    source_chat_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "importance": self.importance,
            "timestamp": self.timestamp,
            "source_chat_id": self.source_chat_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyMemory":
        return cls(
            content=data["content"],
            importance=data.get("importance", 1),
            timestamp=data.get("timestamp", time.time()),
            source_chat_id=data.get("source_chat_id")
        )


@dataclass
class ChatSession:
    """聊天会话"""
    chat_id: str
    created_at: float
    messages: List[ChatMessage] = field(default_factory=list)
    key_memories: List[KeyMemory] = field(default_factory=list)
    title: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chat_id": self.chat_id,
            "created_at": self.created_at,
            "messages": [m.to_dict() for m in self.messages],
            "key_memories": [k.to_dict() for k in self.key_memories],
            "title": self.title
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatSession":
        return cls(
            chat_id=data["chat_id"],
            created_at=data["created_at"],
            messages=[ChatMessage.from_dict(m) for m in data.get("messages", [])],
            key_memories=[KeyMemory.from_dict(k) for k in data.get("key_memories", [])],
            title=data.get("title")
        )
    
    def add_message(self, role: str, content: str):
        """添加消息"""
        self.messages.append(ChatMessage(role=role, content=content))
        
        if len(self.messages) == 1 and not self.title:
            self.title = content[:50] + ("..." if len(content) > 50 else "")
    
    def add_key_memory(self, content: str, importance: int = 1, source_chat_id: Optional[str] = None):
        """添加关键记忆"""
        self.key_memories.append(KeyMemory(
            content=content,
            importance=importance,
            source_chat_id=source_chat_id
        ))
    
    def get_context(self, max_messages: int = 20) -> str:
        """获取上下文（最近的消息）"""
        recent_messages = self.messages[-max_messages:]
        context_parts = []
        for msg in recent_messages:
            role_label = "用户" if msg.role == "user" else "助手"
            context_parts.append(f"{role_label}: {msg.content}")
        
        key_memory_parts = []
        for km in sorted(self.key_memories, key=lambda x: -x.importance):
            key_memory_parts.append(f"- {km.content}")
        
        full_context = []
        if key_memory_parts:
            full_context.append("【关键记忆】\n" + "\n".join(key_memory_parts[:10]))
        
        full_context.append("【对话历史】\n" + "\n".join(context_parts))
        
        return "\n\n".join(full_context)


class SessionMemoryManager:
    """会话记忆管理器"""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            storage_dir = Path(__file__).parent / ".ai_sessions"
        
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True)
        
        self._sessions: Dict[str, ChatSession] = {}
        self._load_all_sessions()
    
    def _get_session_path(self, chat_id: str) -> Path:
        """获取会话文件路径"""
        return self.storage_dir / f"{chat_id}.json"
    
    def _load_all_sessions(self):
        """加载所有会话"""
        for session_file in self.storage_dir.glob("*.json"):
            try:
                chat_id = session_file.stem
                session = self._load_session(chat_id)
                if session:
                    self._sessions[chat_id] = session
            except Exception:
                pass
    
    def _load_session(self, chat_id: str) -> Optional[ChatSession]:
        """加载单个会话"""
        session_path = self._get_session_path(chat_id)
        if not session_path.exists():
            return None
        
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return ChatSession.from_dict(data)
        except Exception:
            return None
    
    def _save_session(self, session: ChatSession):
        """保存会话"""
        session_path = self._get_session_path(session.chat_id)
        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
    
    def create_session(self, chat_id: str) -> ChatSession:
        """创建新会话"""
        session = ChatSession(
            chat_id=chat_id,
            created_at=time.time()
        )
        self._sessions[chat_id] = session
        self._save_session(session)
        return session
    
    def get_session(self, chat_id: str) -> Optional[ChatSession]:
        """获取会话"""
        return self._sessions.get(chat_id)
    
    def get_or_create_session(self, chat_id: str) -> ChatSession:
        """获取或创建会话"""
        session = self.get_session(chat_id)
        if not session:
            session = self.create_session(chat_id)
        return session
    
    def add_message(self, chat_id: str, role: str, content: str) -> ChatSession:
        """添加消息到会话"""
        session = self.get_or_create_session(chat_id)
        session.add_message(role, content)
        self._save_session(session)
        return session
    
    def add_key_memory(self, chat_id: str, content: str, importance: int = 1):
        """添加关键记忆"""
        session = self.get_or_create_session(chat_id)
        session.add_key_memory(content, importance, chat_id)
        self._save_session(session)
    
    def get_context(self, chat_id: str, max_messages: int = 20) -> str:
        """获取会话上下文"""
        session = self.get_session(chat_id)
        if not session:
            return ""
        return session.get_context(max_messages)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        sessions_list = []
        for chat_id, session in sorted(
            self._sessions.items(),
            key=lambda x: -x[1].created_at
        ):
            sessions_list.append({
                "chat_id": chat_id,
                "title": session.title or chat_id,
                "created_at": datetime.fromtimestamp(session.created_at).strftime("%Y-%m-%d %H:%M:%S"),
                "message_count": len(session.messages),
                "key_memory_count": len(session.key_memories)
            })
        return sessions_list
    
    def delete_session(self, chat_id: str) -> bool:
        """删除会话"""
        if chat_id in self._sessions:
            del self._sessions[chat_id]
            session_path = self._get_session_path(chat_id)
            if session_path.exists():
                session_path.unlink()
            return True
        return False


# 全局单例
_memory_manager: Optional[SessionMemoryManager] = None


def get_memory_manager() -> SessionMemoryManager:
    """获取全局记忆管理器"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = SessionMemoryManager()
    return _memory_manager


__all__ = [
    "ChatMessage",
    "KeyMemory",
    "ChatSession",
    "SessionMemoryManager",
    "get_memory_manager"
]
