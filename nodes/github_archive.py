import base64
import hashlib
import requests
import time
from datetime import datetime
from typing import Dict, Any
from nodes.base import BaseNode
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger

def github_archive_node(node_id: str, node_name: str, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
    """GitHub母本归档节点 - 无状态纯函数版本"""
    pipeline.nodes[node_id].status = NodeStatus.RUNNING
    logger.write(f"📦 [{node_name}] 开始GitHub母本归档")
    
    try:
        chapter_title = context.get("chapter_title", "")
        content = context.get("final_content", "")
        github_token = context.get("github_token", "")
        github_repo = context.get("github_repo", "")
        
        # 如果没有配置 GitHub Token 或 Repo，直接跳过
        if not github_token or not github_repo or github_token == "你的_GitHub_Personal_Access_Token":
            logger.write(f"⚠️ [{node_name}] 未配置GitHub，跳过归档")
            pipeline.nodes[node_id].status = NodeStatus.SUCCESS
            return True
        
        filename = f"{chapter_title}_{datetime.now().strftime('%Y%m%d%H%M')}.md"
        
        url = f"https://api.github.com/repos/{github_repo}/contents/novels/{filename}"
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        headers = {"Authorization": f"token {github_token}"}
        data = {"message": f"Auto-upload: {filename}", "content": content_base64, "branch": "main"}
        
        res = None
        for i in range(2):
            try:
                res = requests.put(url, headers=headers, json=data)
                if res.status_code in [200, 201]:
                    break
                else:
                    if i == 0:
                        logger.write(f"⚠️ [{node_name}] GitHub上传失败，正在重试...")
                        time.sleep(1)
                    else:
                        raise Exception(f"GitHub上传失败：{res.text}")
            except Exception as e:
                if i == 0:
                    logger.write(f"⚠️ [{node_name}] GitHub上传异常，正在重试...")
                    time.sleep(1)
                else:
                    raise Exception(f"GitHub上传异常：{str(e)}")
        
        raw_url = f"https://raw.githubusercontent.com/{github_repo}/main/novels/{filename}"
        
        md5 = hashlib.md5(content.encode()).hexdigest()
        
        context["github_url"] = raw_url
        context["md5"] = md5
        context["github_file"] = f"novels/{filename}"
        if res and res.status_code in [200, 201]:
            context["github_sha"] = res.json()["content"]["sha"]
        
        pipeline.nodes[node_id].status = NodeStatus.SUCCESS
        pipeline.nodes[node_id].result = {"raw_url": raw_url, "md5": md5}
        logger.write(f"✅ [{node_name}] GitHub归档成功：{filename}")
        
        return True
        
    except Exception as e:
        pipeline.nodes[node_id].status = NodeStatus.FAILED
        pipeline.nodes[node_id].error_msg = str(e)
        logger.write(f"❌ [{node_name}] GitHub归档失败：{str(e)}")
        return False

class GitHubArchiveNode(BaseNode):
    """GitHub母本归档节点 - 向后兼容包装器"""
    
    def __init__(self):
        super().__init__(
            node_id="github_archive",
            node_name="6. GitHub母本归档",
            description="上传原始文件到私有仓库"
        )
    
    def get_pre_nodes(self) -> list[str]:
        return ["update_plot"]
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        return github_archive_node(self.node_id, self.node_name, pipeline, context, logger)
