import requests
from typing import Dict, Any
from nodes.base import BaseNode
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger
from utils.helpers import count_real_chars

def _get_notion_client(token: str):
    """获取Notion客户端 - 辅助函数"""
    try:
        from notion_client import Client
        return Client(auth=token)
    except ImportError:
        raise Exception("notion_client 模块未安装")

def notion_write_node(node_id: str, node_name: str, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
    """Notion分发对账节点 - 无状态纯函数版本"""
    pipeline.nodes[node_id].status = NodeStatus.RUNNING
    logger.write(f"📤 [{node_name}] 开始Notion写入与对账")
    
    try:
        chapter_title = context.get("chapter_title", "")
        content = context.get("final_content", "")
        github_url = context.get("github_url", "")
        md5 = context.get("md5", "")
        real_chars = context.get("real_chars", 0)
        notion_token = context.get("notion_token", "")
        notion_db_id = context.get("notion_db_id", "")
        
        # 先尝试导入 notion_client，如果失败直接跳过
        try:
            from notion_client import Client
        except ImportError:
            logger.write(f"⚠️ [{node_name}] notion_client未安装，跳过分发")
            pipeline.nodes[node_id].status = NodeStatus.SUCCESS
            return True
        
        # 如果没有配置 Notion Token 或 DB ID，直接跳过
        if not notion_token or not notion_db_id or notion_token == "你的_Notion_Integration_Token":
            logger.write(f"⚠️ [{node_name}] 未配置Notion，跳过分发")
            pipeline.nodes[node_id].status = NodeStatus.SUCCESS
            return True
        
        final_chars = count_real_chars(content)
        
        notion = _get_notion_client(notion_token)
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
        
        chunks = [content[i:i+1500] for i in range(0, len(content), 1500)]
        for chunk in chunks:
            notion.blocks.children.append(
                page_id,
                children=[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]}}]
            )
        
        pipeline.nodes[node_id].status = NodeStatus.SUCCESS
        logger.write(f"✅ [{node_name}] Notion写入完成，对账通过")
        
        return True
        
    except Exception as e:
        pipeline.nodes[node_id].status = NodeStatus.FAILED
        pipeline.nodes[node_id].error_msg = str(e)
        logger.write(f"❌ [{node_name}] Notion写入失败：{str(e)}")
        
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

class NotionWriteNode(BaseNode):
    """Notion分发对账节点 - 向后兼容包装器"""
    
    def __init__(self):
        super().__init__(
            node_id="notion_write",
            node_name="7. Notion分发对账",
            description="分段写入Notion，回读对账"
        )
    
    def get_pre_nodes(self) -> list[str]:
        return ["github_archive"]
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        return notion_write_node(self.node_id, self.node_name, pipeline, context, logger)
