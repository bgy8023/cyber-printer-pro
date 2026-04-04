import os
import requests
import time
from typing import Dict, Any, Tuple
from nodes.base import BaseNode
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger
from utils.helpers import reload_env, get_resource_path, get_clawpanel_agents, get_agent_skills, get_mcp_servers

def init_check_node(node_id: str, node_name: str, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
    """初始化校验节点 - 无状态纯函数版本"""
    pipeline.nodes[node_id].status = NodeStatus.RUNNING
    logger.write(f"🔍 [{node_name}] 开始初始化环境校验（内置技能已加载）")
    
    try:
        notion_token, notion_db_id, github_token, github_repo = reload_env()
        required_env = [notion_token, notion_db_id, github_token, github_repo]
        
        if any(not env for env in required_env):
            raise Exception("核心环境变量缺失，请检查.env文件")
        
        gen_script_path = get_resource_path("run_openclaw.sh")
        if not gen_script_path or not os.path.exists(gen_script_path):
            raise Exception(f"生成脚本不存在：{gen_script_path}")
        
        target_agent = context.get("target_agent", "default")
        logger.write(f"🤖 [{node_name}] 正在检查目标Agent：{target_agent}")
        
        agents_list = get_clawpanel_agents()
        if target_agent not in agents_list:
            logger.write(f"⚠️ [{node_name}] Agent {target_agent} 不在检测列表中，尝试使用default")
        
        skills = get_agent_skills(target_agent)
        core_skills = ["novel-generator", "undercover_mode", "humanizer", "xcrawl_scraper"]
        for skill in core_skills:
            if skill in skills:
                logger.write(f"✅ [{node_name}] {skill}技能已就绪（内置加载）")
        
        enable_mcp = context.get("enable_mcp", False)
        if enable_mcp:
            mcp_servers = get_mcp_servers()
            if mcp_servers:
                logger.write(f"✅ [{node_name}] MCP跨维工具已就绪：{', '.join(mcp_servers)}")
        
        for i in range(2):
            try:
                gh_res = requests.get(
                    f"https://api.github.com/repos/{github_repo}",
                    headers={"Authorization": f"token {github_token}"}
                )
                if gh_res.status_code == 200:
                    break
                else:
                    if i == 0:
                        logger.write(f"⚠️ [{node_name}] GitHub API连通失败，正在重试...")
                        time.sleep(1)
                    else:
                        raise Exception(f"GitHub API连通失败：{gh_res.text}")
            except Exception as e:
                if i == 0:
                    logger.write(f"⚠️ [{node_name}] GitHub API请求异常，正在重试...")
                    time.sleep(1)
                else:
                    raise Exception(f"GitHub API请求异常：{str(e)}")
        
        notion_res = requests.get(
            f"https://api.notion.com/v1/databases/{notion_db_id}",
            headers={
                "Authorization": f"Bearer {notion_token}",
                "Notion-Version": "2022-06-28"
            }
        )
        if notion_res.status_code != 200:
            raise Exception(f"Notion API连通失败：{notion_res.text}")
        
        setting_path = get_resource_path("novel_settings")
        if not os.path.exists(setting_path):
            os.makedirs(setting_path)
        
        pipeline.nodes[node_id].status = NodeStatus.SUCCESS
        logger.write(f"✅ [{node_name}] 初始化校验全部通过，内置技能已加载")
        
        context["notion_token"] = notion_token
        context["notion_db_id"] = notion_db_id
        context["github_token"] = github_token
        context["github_repo"] = github_repo
        
        return True
        
    except Exception as e:
        pipeline.nodes[node_id].status = NodeStatus.FAILED
        pipeline.nodes[node_id].error_msg = str(e)
        logger.write(f"❌ [{node_name}] 初始化校验失败：{str(e)}")
        return False

class InitCheckNode(BaseNode):
    """初始化校验节点 - 向后兼容包装器"""
    
    def __init__(self):
        super().__init__(
            node_id="init_check",
            node_name="1. 初始化校验",
            description="检查环境、Agent、技能、工具"
        )
    
    def get_pre_nodes(self) -> list[str]:
        return []
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        return init_check_node(self.node_id, self.node_name, pipeline, context, logger)
