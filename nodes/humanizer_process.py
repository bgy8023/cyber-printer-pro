import os
import sys
import subprocess
from typing import Dict, Any
from nodes.base import BaseNode
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger
from utils.helpers import count_real_chars, OPENMARS_WORKSPACE

def humanizer_process_node(node_id: str, node_name: str, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
    """去AI化处理节点 - 无状态纯函数版本"""
    pipeline.nodes[node_id].status = NodeStatus.RUNNING
    
    enable_humanizer = context.get("enable_humanizer", False)
    if not enable_humanizer:
        logger.write(f"⚠️ [{node_name}] 已关闭去AI化处理，跳过本节点")
        pipeline.nodes[node_id].status = NodeStatus.SKIPPED
        context["final_content"] = context.get("raw_content", "")
        return True
    
    try:
        logger.write(f"🧹 [{node_name}] 正在调用Humanizer技能，二次去AI化")
        
        raw_content = context.get("raw_content", "")
        target_agent = context.get("target_agent", "default")
        
        prompt = f"请使用Humanizer技能，对下面的小说正文进行二次去AI化处理，严格保留原剧情、人设、爽点、节奏和字数，只去除残留的AI痕迹，让文本更像真人写的网文，直接输出改写后的完整正文，不要任何额外解释：\n\n{raw_content}"
        
        env = os.environ.copy()
        if hasattr(sys, '_MEIPASS'):
            env["APP_BUILTIN_RESOURCES"] = sys._MEIPASS
        
        process = subprocess.Popen(
            [os.path.join(OPENMARS_WORKSPACE, "openmars"), "chat", prompt, "--agent", target_agent, "--skills", "humanizer"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            bufsize=1,
            universal_newlines=True,
            env=env
        )
        
        humanized_content = ""
        if process.stdout is not None:
            for line in process.stdout:
                if line.strip() and not line.strip().startswith("[") and not line.strip().startswith("✅") and not line.strip().startswith("⚠️") and not line.strip().startswith("❌"):
                    humanized_content += line + "\n"
                if line.strip():
                    logger.write(f"[Humanizer] {line.strip()}")
        
        process.wait(timeout=180)
        if process.returncode != 0:
            raise Exception("Humanizer技能调用失败")
        
        if not humanized_content or len(humanized_content.strip()) < 100:
            raise Exception("去AI化处理后内容为空，保留原始正文")
        
        raw_chars = count_real_chars(raw_content)
        humanized_chars = count_real_chars(humanized_content)
        if humanized_chars < raw_chars * 0.9:
            logger.write(f"⚠️ [{node_name}] 去AI化后字数缩水，原始{raw_chars}字，处理后{humanized_chars}字，保留原始正文")
            humanized_content = raw_content
        else:
            logger.write(f"✅ [{node_name}] 去AI化处理完成，处理后有效汉字：{humanized_chars}字")
        
        context["final_content"] = humanized_content
        
        pipeline.nodes[node_id].status = NodeStatus.SUCCESS
        pipeline.nodes[node_id].result = {"humanized_content": humanized_content}
        
        return True
        
    except Exception as e:
        logger.write(f"❌ [{node_name}] 去AI化处理失败：{str(e)}，保留原始正文")
        context["final_content"] = context.get("raw_content", "")
        pipeline.nodes[node_id].status = NodeStatus.SUCCESS
        return True

class HumanizerProcessNode(BaseNode):
    """去AI化处理节点 - 向后兼容包装器"""
    
    def __init__(self):
        super().__init__(
            node_id="humanizer_process",
            node_name="4. 去AI化处理",
            description="二次优化，过审保障"
        )
    
    def get_pre_nodes(self) -> list[str]:
        return ["generate_content"]
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        return humanizer_process_node(self.node_id, self.node_name, pipeline, context, logger)
