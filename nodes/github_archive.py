import base64
import hashlib
import requests
import time
from datetime import datetime
from typing import Dict, Any
from nodes.base import BaseNode
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger

class GitHubArchiveNode(BaseNode):
    """GitHub母本归档节点"""
    
    def __init__(self):
        super().__init__(
            node_id="github_archive",
            node_name="6. GitHub母本归档",
            description="上传原始文件到私有仓库"
        )
    
    def get_pre_nodes(self) -> list[str]:
        return ["update_plot"]
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        """执行GitHub归档"""
        # 更新节点状态
        pipeline.nodes[self.node_id].status = NodeStatus.RUNNING
        logger.write(f"📦 [{self.node_name}] 开始GitHub母本归档")
        
        try:
            # 获取参数
            chapter_title = context.get("chapter_title", "")
            content = context.get("final_content", "")
            github_token = context.get("github_token", "")
            github_repo = context.get("github_repo", "")
            
            # 生成文件名
            filename = f"{chapter_title}_{datetime.now().strftime('%Y%m%d%H%M')}.md"
            
            # 准备GitHub API请求
            url = f"https://api.github.com/repos/{github_repo}/contents/novels/{filename}"
            content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            headers = {"Authorization": f"token {github_token}"}
            data = {"message": f"Auto-upload: {filename}", "content": content_base64, "branch": "main"}
            
            # 尝试上传
            for i in range(2):
                try:
                    res = requests.put(url, headers=headers, json=data)
                    if res.status_code in [200, 201]:
                        break
                    else:
                        if i == 0:
                            logger.write(f"⚠️ [{self.node_name}] GitHub上传失败，正在重试...")
                            time.sleep(1)
                        else:
                            raise Exception(f"GitHub上传失败：{res.text}")
                except Exception as e:
                    if i == 0:
                        logger.write(f"⚠️ [{self.node_name}] GitHub上传异常，正在重试...")
                        time.sleep(1)
                    else:
                        raise Exception(f"GitHub上传异常：{str(e)}")
            
            # 生成原始文件URL
            raw_url = f"https://raw.githubusercontent.com/{github_repo}/main/novels/{filename}"
            
            # 计算MD5校验值
            md5 = hashlib.md5(content.encode()).hexdigest()
            
            # 保存到上下文
            context["github_url"] = raw_url
            context["md5"] = md5
            context["github_file"] = f"novels/{filename}"
            if res.status_code in [200, 201]:
                context["github_sha"] = res.json()["content"]["sha"]
            
            # 更新节点状态为成功
            pipeline.nodes[self.node_id].status = NodeStatus.SUCCESS
            pipeline.nodes[self.node_id].result = {"raw_url": raw_url, "md5": md5}
            logger.write(f"✅ [{self.node_name}] GitHub归档成功：{filename}")
            
            return True
            
        except Exception as e:
            # 更新节点状态为失败
            pipeline.nodes[self.node_id].status = NodeStatus.FAILED
            pipeline.nodes[self.node_id].error_msg = str(e)
            logger.write(f"❌ [{self.node_name}] GitHub归档失败：{str(e)}")
            return False
