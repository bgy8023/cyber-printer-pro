# builtin_claude_core/consistency_agent.py
# 连贯性校验Agent - 自动校验生成内容，不合格自动触发重写

from typing import Dict, Tuple, List, Optional
from .logger import logger
from .memory_palace import MemoryPalace
from openai import OpenAI
import os
import re
from dotenv import load_dotenv

load_dotenv()


class ConsistencyCheckResult:
    """校验结果封装类"""
    
    def __init__(self):
        self.passed: bool = True
        self.score: int = 100
        self.failed_items: List[Dict] = []
        self.rewrite_suggestion: str = ""
        self.rewrite_needed: bool = False


class ConsistencyAgent:
    """连贯性校验Agent核心类"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.anthropic.com/v1/")
        )
        self.model_name = os.getenv("LLM_MODEL_NAME", "claude-3-5-sonnet-20240620")
        self.pass_score = 80
        logger.info("✅ 连贯性校验Agent初始化完成")
    
    def check_chapter(
        self,
        memory_palace: MemoryPalace,
        chapter_num: int,
        chapter_name: str,
        chapter_content: str,
        chapter_outline: str
    ) -> ConsistencyCheckResult:
        """
        核心校验方法：单章内容全维度校验
        返回校验结果，判断是否需要重写
        """
        logger.info(f"🔍 开始校验第{chapter_num}章：{chapter_name}")
        result = ConsistencyCheckResult()
        
        fixed_memory_prompt = memory_palace.get_full_fixed_prompt()
        previous_plot = memory_palace.get_previous_plot_summary(max_chapters=5)
        unresolved_foreshadowing = memory_palace.get_unresolved_foreshadowing_prompt()
        
        check_prompt = f"""
你是专业的网文内容校验师，严格按照以下4个维度，对小说章节内容进行校验，输出校验报告和评分。
校验规则：
1. 满分100分，80分以上为合格，低于80分必须重写
2. 每发现一处严重问题扣20分，普通问题扣10分
3. 严重问题：人设崩塌、剧情前后矛盾、完全不符合大纲规划
4. 普通问题：细节不严谨、伏笔回收不合理、节奏不符合要求

【校验基准】
{fixed_memory_prompt}
{previous_plot}
【本章大纲要求】{chapter_outline}
【未回收的伏笔】{unresolved_foreshadowing}

【待校验的章节内容】
第{chapter_num}章 {chapter_name}
{chapter_content}

【输出格式要求】
严格按照以下格式输出，不要修改结构：
# 校验评分
分数：[0-100的数字]
是否合格：[是/否]
是否需要重写：[是/否]

# 问题清单
[分点列出所有问题，标注严重/普通，说明问题位置和原因]

# 重写建议
[详细说明重写的核心要求和修改方向，必须具体可执行]
        """
        
        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": check_prompt}],
                temperature=0.3,
                timeout=300
            )
            check_result = resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error("❌ 校验调用失败：{}".format(str(e)), exc_info=True)
            result.passed = True
            result.rewrite_needed = False
            result.score = 80
            return result
        
        result = self._parse_check_result(check_result)
        logger.info(f"📊 第{chapter_num}章校验完成，得分：{result.score}，是否通过：{result.passed}")
        
        if result.failed_items:
            for item in result.failed_items:
                logger.warning(f"⚠️  校验问题：{item['level']} - {item['content']}")
        
        return result
    
    def _parse_check_result(self, check_result: str) -> ConsistencyCheckResult:
        """解析LLM返回的校验结果"""
        result = ConsistencyCheckResult()
        
        score_match = re.search(r"分数[：:]\s*(\d+)", check_result)
        if score_match:
            result.score = int(score_match.group(1))
            result.passed = result.score >= self.pass_score
            result.rewrite_needed = result.score < self.pass_score
        
        rewrite_match = re.search(r"是否需要重写[：:]\s*(是|否)", check_result)
        if rewrite_match:
            result.rewrite_needed = rewrite_match.group(1) == "是"
        
        issues_match = re.search(r"# 问题清单([\s\S]+?)(?=\n# |$)", check_result)
        if issues_match:
            issues_content = issues_match.group(1).strip()
            issue_lines = [line.strip() for line in issues_content.split("\n") if line.strip().startswith("-")]
            for line in issue_lines:
                level = "严重" if "严重" in line else "普通"
                result.failed_items.append({
                    "level": level,
                    "content": line
                })
        
        suggestion_match = re.search(r"# 重写建议([\s\S]+)", check_result)
        if suggestion_match:
            result.rewrite_suggestion = suggestion_match.group(1).strip()
        
        return result


_consistency_agent: Optional[ConsistencyAgent] = None


def get_consistency_agent() -> ConsistencyAgent:
    global _consistency_agent
    if _consistency_agent is None:
        _consistency_agent = ConsistencyAgent()
    return _consistency_agent
