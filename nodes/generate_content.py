import os
import sys
import subprocess
from typing import Dict, Any
from nodes.base import BaseNode
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger
from utils.helpers import get_resource_path, extract_latest_novel_from_output, clean_mermaid_code, count_real_chars

class GenerateContentNode(BaseNode):
    """多智能体创作节点"""
    
    def __init__(self):
        super().__init__(
            node_id="generate_content",
            node_name="3. 多智能体创作",
            description="调用Claude内核生成正文"
        )
    
    def get_pre_nodes(self) -> list[str]:
        return ["load_settings"]
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        """执行多智能体创作"""
        # 更新节点状态
        pipeline.nodes[self.node_id].status = NodeStatus.RUNNING
        enable_multi_agent = context.get("enable_multi_agent", False)
        logger.write(f"🤖 [{self.node_name}] 开始多智能体创作（多Agent：{'已激活' if enable_multi_agent else '未激活'}")
        
        try:
            # 获取参数
            chapter_num = context.get("chapter_num", 1)
            chapter_title = context.get("chapter_title", f"第{chapter_num}章")
            final_prompt = context.get("final_prompt", "")
            target_words = context.get("target_words", 7500)
            target_agent = context.get("target_agent", "default")
            enable_humanizer = context.get("enable_humanizer", False)
            
            # 执行生成脚本
            gen_script_path = get_resource_path("run_claude_core.sh")
            if gen_script_path and os.path.exists(gen_script_path):
                env = os.environ.copy()
                if hasattr(sys, '_MEIPASS'):
                    env["APP_BUILTIN_RESOURCES"] = sys._MEIPASS
                
                process = subprocess.Popen(
                    [gen_script_path, str(chapter_num), final_prompt, str(target_words), target_agent, "false", "true" if enable_multi_agent else "false"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    bufsize=1,
                    universal_newlines=True,
                    env=env
                )
                
                # 实时输出日志
                for line in process.stdout:
                    if line.strip():
                        logger.write(f"[Claude Core] {line.strip()}")
                
                # 等待进程完成
                process.wait(timeout=300)
                if process.returncode not in [0, 124]:
                    raise Exception(f"生成脚本执行失败，返回码：{process.returncode}")
            else:
                raise Exception("未找到生成脚本")
            
            # 提取生成的内容
            logger.write(f"📂 [{self.node_name}] 正在从输出目录提取小说正文...")
            generated_content = extract_latest_novel_from_output()
            if not generated_content:
                raise Exception("无法从输出目录提取小说正文")
            
            # 清理内容
            generated_content = clean_mermaid_code(generated_content)
            
            # 检查字数
            real_chars = count_real_chars(generated_content)
            if real_chars < target_words * 0.95:
                raise Exception(f"字数不达标！目标{target_words}字，仅生成{real_chars}字")
            
            # 保存到上下文
            context["raw_content"] = generated_content
            context["real_chars"] = real_chars
            
            # 更新节点状态为成功
            pipeline.nodes[self.node_id].status = NodeStatus.SUCCESS
            pipeline.nodes[self.node_id].result = {"content": generated_content, "real_chars": real_chars}
            logger.write(f"✅ [{self.node_name}] 创作完成，实际有效汉字：{real_chars}字")
            
            return True
            
        except Exception as e:
            # 更新节点状态为失败
            pipeline.nodes[self.node_id].status = NodeStatus.FAILED
            pipeline.nodes[self.node_id].error_msg = str(e)
            logger.write(f"❌ [{self.node_name}] 创作失败：{str(e)}")
            return False
