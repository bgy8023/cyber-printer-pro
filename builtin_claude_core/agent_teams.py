# agent_teams.py - 专业写作Agent团队
# 包含5个专业写作Agent：Outline/Writer/Review/Polish/Foreshadow

import asyncio
from typing import Dict, Optional, List, Any
from .logger import logger
from .query_engine import AsyncQueryEngine


class BaseAgent:
    """基础Agent类"""
    
    def __init__(self, name: str, role: str, system_prompt: str, query_engine: AsyncQueryEngine):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.query_engine = query_engine
        logger.info(f"🤖 Agent初始化完成：{name}")
    
    async def execute(self, task: str, context: Optional[str] = None) -> str:
        """执行Agent任务"""
        logger.info(f"🚀 {self.name} 开始执行任务")
        combined_context = f"{self.system_prompt}\n\n"
        if context:
            combined_context += f"【上下文】\n{context}\n\n"
        combined_context += f"【任务】\n{task}"
        
        result = await self.query_engine.call_llm_async(
            user_prompt=task,
            system_prompt=combined_context
        )
        
        logger.info(f"✅ {self.name} 任务完成")
        return result


class OutlineAgent(BaseAgent):
    """大纲设计Agent - 负责整体结构规划"""
    
    def __init__(self, query_engine: AsyncQueryEngine):
        system_prompt = """你是专业的小说大纲设计专家，擅长构建逻辑严密、节奏紧凑的故事框架。
你需要：
1. 设计清晰的三幕式结构
2. 合理安排爽点分布
3. 埋设关键伏笔
4. 规划人物成长弧光
5. 确保剧情逻辑自洽

输出格式要求结构化，分章节明确。"""
        super().__init__(
            name="OutlineAgent",
            role="大纲设计师",
            system_prompt=system_prompt,
            query_engine=query_engine
        )
    
    async def design_outline(self, theme: str, genre: str, character_settings: str) -> str:
        """设计全书大纲"""
        task = f"""请设计一部{genre}小说的完整大纲，主题是：{theme}

【人物设定】
{character_settings}

请输出：
1. 核心概念
2. 三幕式结构
3. 分章大纲（至少30章）
4. 关键伏笔埋设计划
5. 爽点节奏规划"""
        return await self.execute(task)
    
    async def design_chapter_outline(self, chapter_num: int, previous_chapters: str, full_outline: str) -> str:
        """设计单章大纲"""
        task = f"""请设计第{chapter_num}章的详细大纲

【全书大纲】
{full_outline}

【前序章节】
{previous_chapters}

请输出：
1. 本章核心目标
2. 情节发展脉络
3. 人物互动设计
4. 本章结尾钩子"""
        return await self.execute(task)


class WriterAgent(BaseAgent):
    """正文写作Agent - 负责章节内容创作"""
    
    def __init__(self, query_engine: AsyncQueryEngine):
        system_prompt = """你是顶级网络小说作家，擅长写节奏快、爽点足、代入感强的网文。
写作风格要求：
1. 语言流畅自然，符合中文表达习惯
2. 对话生动，符合人物性格
3. 场景描写有画面感
4. 节奏张弛有度
5. 每章都有明确的爽点和钩子
6. 字数控制在7000-8000字左右"""
        super().__init__(
            name="WriterAgent",
            role="正文作家",
            system_prompt=system_prompt,
            query_engine=query_engine
        )
    
    async def write_chapter(self, chapter_outline: str, character_settings: str, previous_content: str) -> str:
        """撰写章节正文"""
        task = f"""请根据以下大纲撰写完整章节

【本章大纲】
{chapter_outline}

【人物设定】
{character_settings}

【前序内容】
{previous_content}

要求：
1. 字数7000-8000字
2. 节奏紧凑，爽点突出
3. 对话自然生动
4. 结尾留有钩子"""
        return await self.execute(task)


class ReviewAgent(BaseAgent):
    """审核编辑Agent - 负责内容审核和质量检查"""
    
    def __init__(self, query_engine: AsyncQueryEngine):
        system_prompt = """你是资深文学编辑，负责审核小说内容质量。
审核重点：
1. 人物一致性检查（避免OOC）
2. 逻辑连贯性检查
3. 世界观设定一致性
4. 情节合理性检查
5. 伏笔回收检查
6. 错别字和语病修改建议

输出要客观、具体、有建设性。"""
        super().__init__(
            name="ReviewAgent",
            role="审核编辑",
            system_prompt=system_prompt,
            query_engine=query_engine
        )
    
    async def review_chapter(self, chapter_content: str, character_settings: str, previous_chapters: str) -> str:
        """审核章节内容"""
        task = f"""请审核以下章节内容

【本章内容】
{chapter_content}

【人物设定】
{character_settings}

【前序章节】
{previous_chapters}

请从以下方面审核：
1. 人物一致性
2. 逻辑连贯性
3. 世界观设定
4. 情节合理性
5. 伏笔回收情况
6. 语言质量

请指出问题并给出修改建议。"""
        return await self.execute(task)


class PolishAgent(BaseAgent):
    """润色优化Agent - 负责文本润色和优化"""
    
    def __init__(self, query_engine: AsyncQueryEngine):
        system_prompt = """你是专业的文字润色专家，擅长提升文本的文学性和可读性。
润色重点：
1. 优化语言表达，使其更流畅自然
2. 增强画面感和感染力
3. 调整节奏，使其更紧凑
4. 强化对话的生动性
5. 保留原作的核心情节和人物风格
6. 避免过度修改，保持原文神韵"""
        super().__init__(
            name="PolishAgent",
            role="润色专家",
            system_prompt=system_prompt,
            query_engine=query_engine
        )
    
    async def polish_chapter(self, chapter_content: str, review_suggestions: Optional[str] = None) -> str:
        """润色章节内容"""
        task = f"""请润色以下章节内容

【本章内容】
{chapter_content}
"""
        if review_suggestions:
            task += f"\n【审核建议】\n{review_suggestions}\n"
        
        task += """请进行润色优化：
1. 优化语言表达
2. 增强画面感
3. 调整节奏
4. 强化对话
5. 根据审核建议修改问题

请输出润色后的完整章节。"""
        return await self.execute(task)


class ForeshadowAgent(BaseAgent):
    """伏笔管理Agent - 负责伏笔的埋设和回收"""
    
    def __init__(self, query_engine: AsyncQueryEngine):
        system_prompt = """你是专业的伏笔设计师，擅长埋设和回收巧妙的伏笔。
工作职责：
1. 设计自然不突兀的伏笔
2. 跟踪已埋设的伏笔
3. 规划伏笔回收时机
4. 确保伏笔回收自然合理
5. 构建伏笔网络，增强故事连贯性"""
        super().__init__(
            name="ForeshadowAgent",
            role="伏笔设计师",
            system_prompt=system_prompt,
            query_engine=query_engine
        )
    
    async def design_foreshadows(self, full_outline: str, chapter_num: int) -> str:
        """设计本章应该埋设的伏笔"""
        task = f"""请根据全书大纲，为第{chapter_num}章设计应该埋设的伏笔

【全书大纲】
{full_outline}

请输出：
1. 本章应该埋设的伏笔列表
2. 每个伏笔的回收时机规划
3. 埋设方式建议（自然融入情节）"""
        return await self.execute(task)
    
    async def check_foreshadow_recovery(self, current_chapter: int, unresolved_foreshadows: List[Dict]) -> str:
        """检查哪些伏笔可以在本章回收"""
        foreshadows_text = "\n".join([
            f"{i+1}. (第{f['chapter']}章) {f['content']}"
            for i, f in enumerate(unresolved_foreshadows)
        ])
        
        task = f"""请检查以下未回收的伏笔，哪些适合在第{current_chapter}章回收

【未回收伏笔】
{foreshadows_text}

请输出：
1. 建议在本章回收的伏笔
2. 回收方式建议
3. 暂时不回收的理由（如有）"""
        return await self.execute(task)


class WritingTeam:
    """写作团队 - 协调5个Agent协同工作"""
    
    def __init__(self, query_engine: AsyncQueryEngine):
        self.query_engine = query_engine
        self.outline_agent = OutlineAgent(query_engine)
        self.writer_agent = WriterAgent(query_engine)
        self.review_agent = ReviewAgent(query_engine)
        self.polish_agent = PolishAgent(query_engine)
        self.foreshadow_agent = ForeshadowAgent(query_engine)
        logger.info("✅ 写作团队初始化完成")
    
    async def generate_full_outline(self, theme: str, genre: str, character_settings: str) -> str:
        """生成完整大纲"""
        return await self.outline_agent.design_outline(theme, genre, character_settings)
    
    async def generate_chapter(
        self,
        chapter_num: int,
        full_outline: str,
        character_settings: str,
        previous_chapters: str,
        unresolved_foreshadows: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """生成完整章节（流水线作业）"""
        logger.info(f"📚 开始生成第{chapter_num}章")
        
        chapter_outline = await self.outline_agent.design_chapter_outline(
            chapter_num, previous_chapters, full_outline
        )
        
        foreshadow_plan = ""
        if unresolved_foreshadows:
            foreshadow_plan = await self.foreshadow_agent.check_foreshadow_recovery(
                chapter_num, unresolved_foreshadows
            )
        
        raw_content = await self.writer_agent.write_chapter(
            chapter_outline, character_settings, previous_chapters
        )
        
        review_result = await self.review_agent.review_chapter(
            raw_content, character_settings, previous_chapters
        )
        
        polished_content = await self.polish_agent.polish_chapter(
            raw_content, review_result
        )
        
        logger.info(f"✅ 第{chapter_num}章生成完成")
        
        return {
            "chapter_num": chapter_num,
            "outline": chapter_outline,
            "raw_content": raw_content,
            "review": review_result,
            "polished_content": polished_content,
            "foreshadow_plan": foreshadow_plan
        }


# 全局写作团队实例
_writing_team: Optional[WritingTeam] = None


def get_writing_team(query_engine: AsyncQueryEngine) -> WritingTeam:
    """获取写作团队单例"""
    global _writing_team
    if _writing_team is None:
        _writing_team = WritingTeam(query_engine)
    return _writing_team

