# rust_dispatcher.py - 赛博印钞机 Pro 核心离合器
# 架构师方案：IPC 进程间通信，彻底解耦 Python 和 Rust
# 进可攻（Rust 高性能），退可守（Python 原生兜底）
import os
import json
import subprocess
import time
import sys
from typing import Dict, Any, Optional

# 导入现有项目的 Python 原生引擎（降级预案用）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from builtin_claude_core.logger import logger
from builtin_claude_core.query_engine import ClaudeQueryEngine
from builtin_claude_core.llm_adapter import get_llm_adapter

class RustCoreDispatcher:
    """
    核心分配器：优先拉起 Rust 物理加速引擎，失败则自动回退到 Python 原生
    完全物理隔离，零 ABI 兼容问题，零重写工作量
    """
    def __init__(self, llm_provider: Optional[str] = None):
        self.llm_provider = llm_provider
        self.os_type = os.name
        self.rust_binary = self._get_binary_path()
        self.workspace = os.path.expanduser("~/.cyberprinter/workspace")
        os.makedirs(self.workspace, exist_ok=True)
        
        # 初始化 LLM 适配器
        self.llm_adapter = get_llm_adapter(provider_type=llm_provider)
        
        # 检查是否有 Rust 核心
        self.has_rust_core = os.path.exists(self.rust_binary) and os.access(self.rust_binary, os.X_OK)
        
        if self.has_rust_core:
            logger.info("✅ 检测到 claw-core Rust 物理加速引擎，性能模式已激活")
        else:
            logger.warning("⚠️  未检测到 Rust 核心，使用 Python 原生引擎（性能模式未激活）")
            # 初始化 Python 原生引擎（降级预案）
            self.python_engine = ClaudeQueryEngine(llm_provider=llm_provider)

    def _get_binary_path(self) -> str:
        """智能寻址：动态获取不同平台下编译好的 Rust 核心文件"""
        project_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 优先找项目目录下的二进制
        if self.os_type == 'nt':
            # Windows
            binary_name = "claw-core.exe"
        else:
            # Mac/Linux
            binary_name = "claw-core"
        
        # 搜索路径：项目目录 → 用户目录 → 系统 PATH
        search_paths = [
            os.path.join(project_dir, "claw-code", "target", "release"),
            os.path.join(project_dir, "bin"),
            os.path.expanduser("~/.cyberprinter/bin"),
        ]
        
        for path in search_paths:
            binary_path = os.path.join(path, binary_name)
            if os.path.exists(binary_path) and os.access(binary_path, os.X_OK):
                return binary_path
        
        # 没找到，返回默认路径（用于后续编译）
        return os.path.join(project_dir, "bin", binary_name)

    def dispatch_task(
        self,
        chapter_num: int,
        target_words: int,
        custom_prompt: str,
        relevant_memory: str
    ) -> Dict[str, Any]:
        """
        核心任务分配器：
        1. 优先用 Rust 物理加速引擎
        2. Rust 崩了，自动切回 Python 原生引擎
        3. 用户完全无感知
        """
        if self.has_rust_core:
            try:
                return self._run_rust_engine(chapter_num, target_words, custom_prompt, relevant_memory)
            except Exception as e:
                logger.error(f"❌ Rust 引擎执行失败：{str(e)}，自动切换到 Python 原生引擎", exc_info=True)
                self.has_rust_core = False  # 本次会话不再尝试 Rust
        
        # 降级预案：Python 原生引擎
        return self._run_python_fallback(chapter_num, target_words, custom_prompt, relevant_memory)

    def _run_rust_engine(
        self,
        chapter_num: int,
        target_words: int,
        custom_prompt: str,
        relevant_memory: str
    ) -> Dict[str, Any]:
        """
        运行 Rust 物理加速引擎
        完全物理隔离的进程，跑得再疯也不会导致 Python 内存溢出
        """
        logger.info("🚀 切换至 Rust 高性能物理加速引擎...")
        
        # 1. 组装任务图纸 (JSON)
        payload = {
            "task_id": f"chapter_{chapter_num}_{int(time.time())}",
            "chapter_num": chapter_num,
            "config": {
                "target_words": target_words,
                "multi_agent": True,
                "undercover_mode": True,
                "llm_provider": self.llm_provider
            },
            "context": {
                "memory": relevant_memory,
                "prompt": custom_prompt
            },
            "output": {
                "workspace": self.workspace,
                "result_file": f"result_{chapter_num}.md"
            }
        }
        
        # 写入任务图纸
        payload_path = os.path.join(self.workspace, f"payload_{chapter_num}.json")
        with open(payload_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        # 2. 拉起 Rust 二进制程序干活
        logger.info(f"🔧 Rust 引擎已点火，读取任务图纸: {payload_path}")
        start_time = time.time()
        
        try:
            # 这是一个物理隔离的进程，它跑得再疯，也不会导致 Python 内存溢出
            process = subprocess.Popen(
                [self.rust_binary, "--run", payload_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                cwd=self.workspace
            )
            
            # 实时输出 Rust 日志
            for line in process.stdout:
                if line.strip():
                    logger.info(f"[Rust] {line.strip()}")
            
            process.wait()
            
            if process.returncode == 0:
                elapsed = time.time() - start_time
                logger.info(f"✅ Rust 引擎执行完毕，耗时 {elapsed:.2f}s")
                
                # 读取 Rust 输出的结果
                result_file = os.path.join(self.workspace, f"result_{chapter_num}.md")
                if os.path.exists(result_file):
                    with open(result_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 统计字数
                    real_chars = ClaudeQueryEngine._count_real_chars(content)
                    
                    return {
                        "outline": "",
                        "content": content,
                        "real_chars": real_chars,
                        "target_words": target_words
                    }
                else:
                    raise Exception(f"Rust 未生成结果文件：{result_file}")
            else:
                raise Exception(f"Rust 核心执行崩溃，退出码：{process.returncode}")
                
        except Exception as e:
            logger.error(f"❌ Rust 引擎拉起失败: {e}", exc_info=True)
            raise  # 抛出异常，触发降级预案

    def _run_python_fallback(
        self,
        chapter_num: int,
        target_words: int,
        custom_prompt: str,
        relevant_memory: str
    ) -> Dict[str, Any]:
        """
        Python 原生降级预案
        完全复用你现有的代码，零重写工作量
        """
        logger.info("⚠️  切换至 Python 原生引擎（降级模式）")
        
        # 确保 Python 引擎已初始化
        if not hasattr(self, 'python_engine'):
            self.python_engine = ClaudeQueryEngine(llm_provider=self.llm_provider)
        
        # 直接调用你现有的 Python 原生引擎
        return self.python_engine.multi_agent_coordinate(
            chapter_num,
            target_words,
            custom_prompt,
            relevant_memory
        )
    
    def load_memory(self, memory_dir: str):
        """
        加载记忆：Rust 引擎用 IPC，Python 引擎直接调用
        """
        if self.has_rust_core:
            try:
                # 组装内存加载任务
                payload = {
                    "task_id": f"memory_load_{int(time.time())}",
                    "type": "memory_load",
                    "memory_dir": memory_dir,
                    "output": {
                        "workspace": self.workspace
                    }
                }
                
                payload_path = os.path.join(self.workspace, f"memory_payload.json")
                with open(payload_path, 'w', encoding='utf-8') as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                
                # 运行 Rust 引擎加载记忆
                process = subprocess.Popen(
                    [self.rust_binary, "--load-memory", payload_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    cwd=self.workspace
                )
                
                for line in process.stdout:
                    if line.strip():
                        logger.info(f"[Rust] {line.strip()}")
                
                process.wait()
                logger.info("✅ 记忆加载完成")
            except Exception as e:
                logger.error(f"❌ Rust 引擎加载记忆失败: {str(e)}")
                # 回退到 Python 原生
                self.python_engine.load_memory(memory_dir)
        else:
            # 直接用 Python 原生
            self.python_engine.load_memory(memory_dir)
    
    def retrieve_memory(self, query: str, top_k: int = 5) -> str:
        """
        检索记忆：Rust 引擎用 IPC，Python 引擎直接调用
        """
        if self.has_rust_core:
            try:
                # 组装记忆检索任务
                payload = {
                    "task_id": f"memory_retrieve_{int(time.time())}",
                    "type": "memory_retrieve",
                    "query": query,
                    "top_k": top_k,
                    "output": {
                        "workspace": self.workspace,
                        "result_file": f"retrieve_result.json"
                    }
                }
                
                payload_path = os.path.join(self.workspace, f"retrieve_payload.json")
                with open(payload_path, 'w', encoding='utf-8') as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                
                # 运行 Rust 引擎检索记忆
                process = subprocess.Popen(
                    [self.rust_binary, "--retrieve-memory", payload_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    cwd=self.workspace
                )
                
                for line in process.stdout:
                    if line.strip():
                        logger.info(f"[Rust] {line.strip()}")
                
                process.wait()
                
                # 读取检索结果
                result_file = os.path.join(self.workspace, f"retrieve_result.json")
                if os.path.exists(result_file):
                    with open(result_file, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                    return "\n\n".join(result.get("results", []))
                else:
                    logger.error(f"❌ Rust 引擎未生成检索结果文件: {result_file}")
                    # 回退到 Python 原生
                    return self.python_engine.retrieve_memory(query, top_k)
            except Exception as e:
                logger.error(f"❌ Rust 引擎检索记忆失败: {str(e)}")
                # 回退到 Python 原生
                return self.python_engine.retrieve_memory(query, top_k)
        else:
            # 直接用 Python 原生
            return self.python_engine.retrieve_memory(query, top_k)
    
    def multi_agent_coordinate(self, chapter_num: int, target_words: int, custom_prompt: str, relevant_memory: str) -> dict:
        """
        多智能体协调创作
        主 Agent 负责任务拆解和结果汇总
        """
        # 直接调用 dispatch_task 方法
        return self.dispatch_task(chapter_num, target_words, custom_prompt, relevant_memory)
    
    def humanize_text(self, text: str) -> str:
        """
        文本去AI化润色
        调用 Python 引擎的 humanize_text 方法
        """
        # 确保 Python 引擎已初始化
        if not hasattr(self, 'python_engine'):
            self.python_engine = ClaudeQueryEngine(llm_provider=self.llm_provider)
        
        # 调用 Python 引擎的 humanize_text 方法
        return self.python_engine.humanize_text(text)
    
    @staticmethod
    def _count_real_chars(text: str) -> int:
        """
        统计实际字数（中文字符）
        """
        import re
        return len(re.findall(r'[\u4e00-\u9fa5]', text))

# 全局单例
_dispatcher: Optional[RustCoreDispatcher] = None


def get_dispatcher(llm_provider: Optional[str] = None) -> RustCoreDispatcher:
    """获取全局单例的离合器"""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = RustCoreDispatcher(llm_provider=llm_provider)
    return _dispatcher
