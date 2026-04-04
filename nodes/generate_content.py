import os
import sys
import subprocess
from typing import Dict, Any
from nodes.base import BaseNode
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger
from utils.helpers import get_resource_path, extract_latest_novel_from_output, clean_mermaid_code, count_real_chars

def generate_content_node(node_id: str, node_name: str, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
    """多智能体创作节点 - 无状态纯函数版本"""
    pipeline.nodes[node_id].status = NodeStatus.RUNNING
    enable_multi_agent = context.get("enable_multi_agent", False)
    logger.write(f"🤖 [{node_name}] 开始多智能体创作（多Agent：{'已激活' if enable_multi_agent else '未激活'}")
    
    try:
        chapter_num = context.get("chapter_num", 1)
        chapter_title = context.get("chapter_title", f"第{chapter_num}章")
        final_prompt = context.get("final_prompt", "")
        target_words = context.get("target_words", 7500)
        target_agent = context.get("target_agent", "default")
        enable_humanizer = context.get("enable_humanizer", False)
        
        gen_script_path = get_resource_path("run_openclaw.sh")
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
            
            for line in process.stdout:
                if line.strip():
                    logger.write(f"[Claude Core] {line.strip()}")
            
            process.wait(timeout=300)
            if process.returncode not in [0, 124]:
                raise Exception(f"生成脚本执行失败，返回码：{process.returncode}")
        else:
            raise Exception("未找到生成脚本")
        
        logger.write(f"📂 [{node_name}] 正在从输出目录提取小说正文...")
        generated_content = extract_latest_novel_from_output()
        if not generated_content:
            raise Exception("无法从输出目录提取小说正文")
        
        generated_content = clean_mermaid_code(generated_content)
        
        real_chars = count_real_chars(generated_content)
        if real_chars < target_words * 0.95:
            raise Exception(f"字数不达标！目标{target_words}字，仅生成{real_chars}字")
        
        context["raw_content"] = generated_content
        context["real_chars"] = real_chars
        
        pipeline.nodes[node_id].status = NodeStatus.SUCCESS
        pipeline.nodes[node_id].result = {"content": generated_content, "real_chars": real_chars}
        logger.write(f"✅ [{node_name}] 创作完成，实际有效汉字：{real_chars}字")
        
        return True
        
    except Exception as e:
        pipeline.nodes[node_id].status = NodeStatus.FAILED
        pipeline.nodes[node_id].error_msg = str(e)
        logger.write(f"❌ [{node_name}] 创作失败：{str(e)}")
        return False

class GenerateContentNode(BaseNode):
    """多智能体创作节点 - 向后兼容包装器"""
    
    def __init__(self):
        super().__init__(
            node_id="generate_content",
            node_name="3. 多智能体创作",
            description="调用Claude内核生成正文"
        )
    
    def get_pre_nodes(self) -> list[str]:
        return ["load_settings"]
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        return generate_content_node(self.node_id, self.node_name, pipeline, context, logger)
