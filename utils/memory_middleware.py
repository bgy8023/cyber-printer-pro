import re
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from .logger import Logger


class MemoryMiddleware:
    """
    Token压缩和记忆清洗中间件
    功能：
    1. 对话历史管理，只保留最近3轮对话
    2. 自动摘要压缩功能
    3. 任务结束后清空全量历史，只保留结果摘要
    4. Token使用量统计与对比
    """
    
    def __init__(self, max_conversation_rounds: int = 3, logger: Optional[Logger] = None):
        """
        初始化记忆中间件
        
        Args:
            max_conversation_rounds: 保留的最大对话轮数
            logger: 日志记录器实例
        """
        self.max_conversation_rounds = max_conversation_rounds
        self.logger = logger
        
        self.conversation_history: List[Dict] = []
        self.task_summary: str = ""
        self.token_stats: Dict = {
            "original_total_tokens": 0,
            "compressed_total_tokens": 0,
            "original_tokens_per_round": [],
            "compressed_tokens_per_round": [],
            "compression_rates": []
        }
        self.task_in_progress: bool = False
    
    def _count_tokens(self, text: str) -> int:
        """
        估算Token数量（简化版本）
        
        Args:
            text: 待统计的文本
            
        Returns:
            估算的Token数量
        """
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
        other_chars = len(text) - chinese_chars
        return chinese_chars + (other_chars // 4)
    
    def _compress_text(self, text: str, max_ratio: float = 0.5) -> str:
        """
        压缩文本内容，确保压缩率至少达到指定比例
        
        Args:
            text: 原始文本
            max_ratio: 最大保留比例（默认50%，即压缩50%）
            
        Returns:
            压缩后的文本
        """
        min_length = 100
        target_length = max(min_length, int(len(text) * max_ratio))
        
        if len(text) <= target_length:
            return text
        
        sentences = re.split(r'[。！？.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return text[:target_length] + "..."
        
        compressed = []
        current_length = 0
        
        if len(sentences) >= 1:
            compressed.append(sentences[0])
            current_length += len(sentences[0])
        
        if len(sentences) >= 2:
            last_idx = len(sentences) - 1
            if current_length + len(sentences[last_idx]) + 2 <= target_length:
                compressed.append(sentences[last_idx])
                current_length += len(sentences[last_idx]) + 2
        
        if len(sentences) > 2:
            step = max(1, len(sentences) // 5)
            for i in range(1, len(sentences) - 1, step):
                sentence = sentences[i]
                if current_length + len(sentence) + 2 <= target_length:
                    compressed.insert(len(compressed) - 1 if len(compressed) > 1 else len(compressed), sentence)
                    current_length += len(sentence) + 2
                else:
                    break
        
        result = "。".join(compressed) + "。"
        
        if len(result) > target_length:
            result = result[:target_length]
            last_punct = max(result.rfind('。'), result.rfind('！'), result.rfind('？'))
            if last_punct > target_length * 0.7:
                result = result[:last_punct + 1]
            else:
                result += "..."
        
        return result
    
    def _summarize_conversation(self) -> str:
        """
        生成对话摘要
        
        Returns:
            对话摘要
        """
        if not self.conversation_history:
            return ""
        
        summary_parts = []
        for i, msg in enumerate(self.conversation_history):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            max_len = 200
            if len(content) > max_len:
                ratio = max_len / len(content)
                compressed = self._compress_text(content, max_ratio=ratio)
            else:
                compressed = content
            summary_parts.append(f"[{i+1}] {role}: {compressed}")
        
        return "\n".join(summary_parts)
    
    def add_message(self, role: str, content: str):
        """
        添加消息到对话历史
        
        Args:
            role: 角色（user/assistant/system）
            content: 消息内容
        """
        original_tokens = self._count_tokens(content)
        self.token_stats["original_total_tokens"] += original_tokens
        
        compressed_content = self._compress_text(content, max_ratio=0.55)
        compressed_tokens = self._count_tokens(compressed_content)
        self.token_stats["compressed_total_tokens"] += compressed_tokens
        
        self.token_stats["original_tokens_per_round"].append(original_tokens)
        self.token_stats["compressed_tokens_per_round"].append(compressed_tokens)
        
        if original_tokens > 0:
            compression_rate = (1 - compressed_tokens / original_tokens) * 100
            self.token_stats["compression_rates"].append(compression_rate)
        
        self.conversation_history.append({
            "role": role,
            "content": compressed_content,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "timestamp": datetime.now().isoformat()
        })
        
        self._trim_conversation_history()
        
        if self.logger:
            self.logger.write(f"[MemoryMiddleware] 消息已添加 - 原始: {original_tokens} tokens, 压缩后: {compressed_tokens} tokens")
    
    def _trim_conversation_history(self):
        """
        裁剪对话历史，只保留最近N轮对话
        每轮对话包含user和assistant消息
        """
        messages_per_round = 2
        max_messages = self.max_conversation_rounds * messages_per_round
        
        if len(self.conversation_history) > max_messages:
            excess = len(self.conversation_history) - max_messages
            self.conversation_history = self.conversation_history[excess:]
            
            if self.logger:
                self.logger.write(f"[MemoryMiddleware] 对话历史已裁剪，保留最近{self.max_conversation_rounds}轮")
    
    def start_task(self):
        """开始新任务"""
        self.task_in_progress = True
        self.conversation_history = []
        self.task_summary = ""
        self.token_stats = {
            "original_total_tokens": 0,
            "compressed_total_tokens": 0,
            "original_tokens_per_round": [],
            "compressed_tokens_per_round": [],
            "compression_rates": []
        }
        
        if self.logger:
            self.logger.write("[MemoryMiddleware] 任务开始，对话历史已重置")
    
    def end_task(self, result_content: Optional[str] = None):
        """
        结束任务，清空全量历史，只保留结果摘要
        
        Args:
            result_content: 任务结果内容
        """
        self.task_in_progress = False
        
        if result_content:
            max_len = 1000
            if len(result_content) > max_len:
                ratio = max_len / len(result_content)
                self.task_summary = self._compress_text(result_content, max_ratio=ratio)
            else:
                self.task_summary = result_content
        else:
            self.task_summary = self._summarize_conversation()
        
        self.conversation_history = []
        
        if self.logger:
            self.logger.write("[MemoryMiddleware] 任务结束，对话历史已清空，结果摘要已保存")
    
    def get_context_messages(self) -> List[Dict]:
        """
        获取当前上下文消息（用于发送给LLM）
        
        Returns:
            上下文消息列表
        """
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.conversation_history
        ]
    
    def get_token_stats(self) -> Dict:
        """
        获取Token统计信息
        
        Returns:
            Token统计字典
        """
        avg_compression_rate = 0
        if self.token_stats["compression_rates"]:
            avg_compression_rate = sum(self.token_stats["compression_rates"]) / len(self.token_stats["compression_rates"])
        
        return {
            "original_total_tokens": self.token_stats["original_total_tokens"],
            "compressed_total_tokens": self.token_stats["compressed_total_tokens"],
            "tokens_saved": self.token_stats["original_total_tokens"] - self.token_stats["compressed_total_tokens"],
            "average_compression_rate": avg_compression_rate,
            "target_reached": avg_compression_rate >= 40,
            "rounds": len(self.token_stats["original_tokens_per_round"])
        }
    
    def get_task_summary(self) -> str:
        """
        获取任务摘要
        
        Returns:
            任务摘要字符串
        """
        return self.task_summary
    
    def clear_all(self):
        """清空所有数据"""
        self.conversation_history = []
        self.task_summary = ""
        self.token_stats = {
            "original_total_tokens": 0,
            "compressed_total_tokens": 0,
            "original_tokens_per_round": [],
            "compressed_tokens_per_round": [],
            "compression_rates": []
        }
        self.task_in_progress = False
        
        if self.logger:
            self.logger.write("[MemoryMiddleware] 所有数据已清空")
    
    def export_stats(self) -> str:
        """
        导出统计信息为JSON字符串
        
        Returns:
            JSON格式的统计信息
        """
        stats = self.get_token_stats()
        return json.dumps(stats, ensure_ascii=False, indent=2)
