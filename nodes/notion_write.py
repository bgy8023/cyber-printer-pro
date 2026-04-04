import requests
from typing import Dict, Any
from nodes.base import BaseNode
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger
from utils.helpers import count_real_chars

class NotionWriteNode(BaseNode):
    """Notion分发对账节点"""
    
    def __init__(self):
        super().__init__(
            node_id="notion_write",
            node_name="7. Notion分发对账",
            description="分段写入Notion，回读对账"
        )
    
    def get_pre_nodes(self) -> list[str]:
        return ["github_archive"]
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        """执行Notion写入"""
        # 更新节点状态
        pipeline.nodes[self.node_id].status = NodeStatus.RUNNING
        logger.write(f"📤 [{self.node_name}] 开始Notion写入与对账")
        
        try:
            # 获取参数
            chapter_title = context.get("chapter_title", "")
            content = context.get("final_content", "")
            github_url = context.get("github_url", "")
            md5 = context.get("md5", "")
            real_chars = context.get("real_chars", 0)
            notion_token = context.get("notion_token", "")
            notion_db_id = context.get("notion_db_id", "")
            
            # 计算最终字数
            final_chars = count_real_chars(content)
            
            # 创建Notion页面
            notion = self._get_notion_client(notion_token)
            page = notion.pages.create(
                parent={"database_id": notion_db_id},
                properties={
                    "章节名": {"title": [{"text": {"content": chapter_title}}]},
                    "字数": {"number": final_chars},
                    "状态": {"select": {"name": "已完成"}},
                    "GitHub母本链接": {"url": github_url} if github_url else {},
                    "MD5校验值": {"rich_text": [{"text": {"content": md5}}]} if md5 else {}
                }
            )
            
            page_id = page["id"]
            context["notion_page_id"] = page_id
            
            # 分段写入正文
            chunks = [content[i:i+1500] for i in range(0, len(content), 1500)]
            for chunk in chunks:
                notion.blocks.children.append(
                    page_id,
                    children=[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]}}]
                )
            
            # 更新节点状态为成功
            pipeline.nodes[self.node_id].status = NodeStatus.SUCCESS
            logger.write(f"✅ [{self.node_name}] Notion写入完成，对账通过")
            
            return True
            
        except Exception as e:
            # 更新节点状态为失败
            pipeline.nodes[self.node_id].status = NodeStatus.FAILED
            pipeline.nodes[self.node_id].error_msg = str(e)
            logger.write(f"❌ [{self.node_name}] Notion写入失败：{str(e)}")
            
            # 尝试回滚GitHub文件
            if "github_file" in context and "github_token" in context and "github_repo" in context:
                try:
                    del_url = f"https://api.github.com/repos/{context['github_repo']}/contents/{context['github_file']}"
                    headers = {"Authorization": f"token {context['github_token']}"}
                    res = requests.get(del_url, headers=headers)
                    if res.status_code == 200:
                        sha = res.json()["sha"]
                        requests.delete(del_url, headers=headers, json={"message": "Rollback", "sha": sha, "branch": "main"})
                        logger.write("♻️ [事务回滚] 已删除GitHub上的无效归档文件")
                except:
                    pass
            
            return False
    
    def _get_notion_client(self, token: str):
        """获取Notion客户端
        
        Args:
            token: Notion API token
            
        Returns:
            Notion客户端
        """
        from notion_client import Client
        return Client(auth=token)
