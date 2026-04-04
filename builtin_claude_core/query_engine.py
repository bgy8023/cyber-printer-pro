import os
import re
import time
import json
from typing import List, Dict, Any, Optional
from .logger import logger
from .semantic_memory import semantic_memory
from .llm_adapter import get_llm_adapter
from .memory_palace import MemoryPalace, get_memory_palace
from .consistency_agent import get_consistency_agent
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.memory_middleware import MemoryMiddleware


class DeerFlowOrchestrator:
    """
    DeerFlow 2.0 核心动态调度器
    主脑只做调度，不下场写网文，通过LLM动态分析并拆分任务
    """
    
    def __init__(self, query_engine):
        self.query_engine = query_engine
        self.task_queue: List[Dict] = []
        self.executed_tasks: List[Dict] = []
        self.current_context: Dict = {}
    
    def analyze_and_split_task(self, main_task: str, context: Dict) -> List[Dict]:
        """
        使用LLM动态分析任务并拆分子任务
        """
        logger.info("🦌 DeerFlow: 主脑正在分析并动态拆分子任务...")
        
        prompt = f"""
你是一个专业的任务调度专家（DeerFlow主脑），你的唯一职责是分析任务并拆分为最优的子任务序列，绝不亲自执行任务。

【主任务】
{main_task}

【可用上下文】
{json.dumps(context, ensure_ascii=False, indent=2)}

【可用Agent类型】
- "outline_agent": 专业大纲师，负责规划剧情结构
- "content_agent": 主笔，负责生成正文内容
- "supplement_agent": 补全专家，负责补充字数
- "check_agent": 审核师，负责校验内容质量
- "humanize_agent": 润色师，负责去AI化优化

【要求】
1. 基于主任务和上下文，分析需要哪些Agent，按什么顺序执行
2. 每个子任务必须清晰定义：agent_type（使用上述可用类型）、description、input_params
3. 子任务数量要适中，既不过度拆分也不过于笼统
4. 只返回JSON数组，不要任何解释说明

【输出格式示例】
[
  {{
    "agent_type": "outline_agent",
    "description": "规划章节大纲",
    "input_params": {{...}}
  }},
  {{
    "agent_type": "content_agent",
    "description": "生成正文",
    "input_params": {{...}}
  }}
]
"""
        
        try:
            response = self.query_engine.llm_adapter.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                tasks = json.loads(json_match.group(0))
                logger.info(f"🦌 DeerFlow: 已动态拆分出 {len(tasks)} 个子任务")
                return tasks
            else:
                raise ValueError("无法解析任务拆分结果")
                
        except Exception as e:
            logger.warning(f"🦌 DeerFlow: 动态拆分失败，使用默认流程: {str(e)}")
            return self._get_default_tasks(context)
    
    def _get_default_tasks(self, context: Dict) -> List[Dict]:
        """
        当动态拆分失败时使用的默认任务流程
        """
        return [
            {
                "agent_type": "outline_agent",
                "description": "规划章节大纲",
                "input_params": context
            },
            {
                "agent_type": "content_agent",
                "description": "生成正文",
                "input_params": context
            },
            {
                "agent_type": "check_agent",
                "description": "校验内容质量",
                "input_params": context
            },
            {
                "agent_type": "humanize_agent",
                "description": "去AI化润色",
                "input_params": context
            }
        ]
    
    def execute_task(self, task: Dict) -> Any:
        """
        执行单个子任务
        """
        agent_type = task["agent_type"]
        logger.info(f"🦌 DeerFlow: 执行子任务 - {task['description']}")
        
        if agent_type == "outline_agent":
            return self._execute_outline_agent(task["input_params"])
        elif agent_type == "content_agent":
            return self._execute_content_agent(task["input_params"])
        elif agent_type == "supplement_agent":
            return self._execute_supplement_agent(task["input_params"])
        elif agent_type == "check_agent":
            return self._execute_check_agent(task["input_params"])
        elif agent_type == "humanize_agent":
            return self._execute_humanize_agent(task["input_params"])
        else:
            raise ValueError(f"未知Agent类型: {agent_type}")
    
    def _execute_outline_agent(self, params: Dict) -> str:
        chapter_num = params.get("chapter_num", 1)
        target_words = params.get("target_words", 3000)
        custom_prompt = params.get("custom_prompt", "")
        relevant_memory = params.get("relevant_memory", "")
        chapter_outline = params.get("chapter_outline", "")
        
        if chapter_outline:
            return chapter_outline
        
        prompt = self.query_engine.undercover_process(f"""
你是专业网文大纲师，基于以下设定，规划网络小说第{chapter_num}章的详细大纲。
要求：
1. 大纲必须包含：开头冲突、中段打脸高潮、围观群众反应、结尾悬念钩子
2. 严格贴合核心设定，不能崩人设、不能吃书
3. 大纲要支撑{target_words}字的正文内容，节奏紧凑，爽点密集
4. 只输出大纲，不要任何多余解释

【核心设定】
{relevant_memory}
【用户要求】
{custom_prompt}
        """)
        
        return self.query_engine._call_agent("大纲Agent", prompt)
    
    def _execute_content_agent(self, params: Dict) -> str:
        chapter_num = params.get("chapter_num", 1)
        target_words = params.get("target_words", 3000)
        relevant_memory = params.get("relevant_memory", "")
        chapter_outline = params.get("chapter_outline", "")
        
        prompt = self.query_engine.undercover_process(f"""
你是专业网文主笔，严格按照下面的大纲，生成网络小说第{chapter_num}章的完整正文。
要求：
1. 正文总字数必须达到{target_words}字，误差不超过5%
2. 严格贴合大纲，不崩人设、不吃书，保持剧情连贯
3. 爽点密集，节奏快，对话自然，细节到位
4. 结尾必须留下悬念钩子，吸引读者看下一章
5. 只输出正文，不要任何解释、标题、备注

【章节大纲】
{chapter_outline}
【核心设定】
{relevant_memory}
        """)
        
        return self.query_engine._call_agent("主笔Agent", prompt)
    
    def _execute_supplement_agent(self, params: Dict) -> str:
        raw_content = params.get("raw_content", "")
        target_words = params.get("target_words", 3000)
        relevant_memory = params.get("relevant_memory", "")
        
        prompt = self.query_engine.undercover_process(f"""
基于上文结尾续写小说正文，补全到{target_words}字，保持剧情连贯，人设不崩，只输出续写的内容，不要重复上文。
请一次性补全到目标字数，不要分段输出。
上文结尾：{raw_content[-1500:]}
核心设定：{relevant_memory}
        """)
        
        return self.query_engine._call_agent("补全Agent", prompt)
    
    def _execute_check_agent(self, params: Dict) -> str:
        raw_content = params.get("raw_content", "")
        relevant_memory = params.get("relevant_memory", "")
        
        prompt = f"""
你是专业网文审核师，检查下面的小说正文，完成以下校验：
1. 核对人设、剧情是否符合核心设定，有没有吃书、崩人设
2. 检查剧情是否连贯，逻辑是否通顺，有没有前后矛盾
3. 检查有没有不符合网文规范的内容
4. 如果有问题，直接修改正文，修正问题，保持原意不变
5. 如果没有问题，直接输出原文
6. 只输出最终的正文，不要任何解释、备注

【核心设定】
{relevant_memory}
【小说正文】
{raw_content}
        """
        
        return self.query_engine._call_agent("审核Agent", prompt)
    
    def _execute_humanize_agent(self, params: Dict) -> str:
        raw_content = params.get("raw_content", "")
        
        prompt = self.query_engine.undercover_process(f"""
你是专业网文润色师，对下面的小说正文进行去AI化润色。
要求：
1. 严格保留原剧情、人设、爽点、总字数不变
2. 优化句子节奏，混合长短句，让文本更像真人写的网文
3. 去除AI写作痕迹，让对话更自然，细节更生动
4. 只输出润色后的完整正文，不要任何解释、备注

【小说正文】
{raw_content}
        """)
        
        return self.query_engine._call_agent("润色Agent", prompt)
    
    def run(self, main_task: str, context: Dict) -> Dict:
        """
        运行DeerFlow调度器
        """
        self.current_context = context.copy()
        
        self.task_queue = self.analyze_and_split_task(main_task, context)
        
        final_result = {
            "outline": "",
            "content": "",
            "real_chars": 0,
            "target_words": context.get("target_words", 3000)
        }
        
        for task in self.task_queue:
            task["input_params"].update(self.current_context)
            
            result = self.execute_task(task)
            
            agent_type = task["agent_type"]
            if agent_type == "outline_agent":
                final_result["outline"] = result
                self.current_context["chapter_outline"] = result
            elif agent_type == "content_agent":
                self.current_context["raw_content"] = result
            elif agent_type == "supplement_agent":
                self.current_context["raw_content"] = self.current_context.get("raw_content", "") + "\n\n" + result
            elif agent_type == "check_agent":
                self.current_context["raw_content"] = result
            elif agent_type == "humanize_agent":
                final_result["content"] = result
                final_result["real_chars"] = ClaudeQueryEngine._count_real_chars(result)
            
            self.executed_tasks.append({
                "task": task,
                "result_length": len(str(result))
            })
        
        if not final_result["content"] and self.current_context.get("raw_content"):
            final_result["content"] = self.current_context["raw_content"]
            final_result["real_chars"] = ClaudeQueryEngine._count_real_chars(final_result["content"])
        
        return final_result


class ClaudeQueryEngine:
    """
    Claude Code泄露源码原生实现的QueryEngine核心推理引擎
    负责：多智能体调度、结构化记忆管理、上下文压缩、Undercover Mode底层处理
    【Deer-Flow 2.0 灵魂注入】
    - 主脑只做调度，绝不亲自下场写网文
    - 动态上下文拆分，按需分裂子任务
    - 无状态执行，任务完立即清理
    - Token极致压缩，只传结果不传废话
    """
    def __init__(self, llm_provider: Optional[str] = None):
        self.memory_store: Dict[str, Any] = {}
        self.agent_pool: Dict[str, Any] = {}
        self.undercover_mode = True
        self.max_retry = 3
        self.timeout = 300
        self.llm_provider = llm_provider
        
        self.deer_flow_enabled = True
        self.max_history_rounds = 3
        
        self.memory_middleware = MemoryMiddleware(
            max_conversation_rounds=self.max_history_rounds,
            logger=None
        )
        
        self.deer_orchestrator = DeerFlowOrchestrator(self)
        
        self._init_llm_adapter()
        logger.info("✅ Claude QueryEngine 初始化完成（已注入Deer-Flow 2.0灵魂）")
    
    def _init_llm_adapter(self):
        """初始化或重新初始化 LLM 适配器"""
        from .llm_adapter import reset_llm_adapter
        reset_llm_adapter()
        self.llm_adapter = get_llm_adapter(provider_type=self.llm_provider)
        logger.info(f"✅ LLM 适配器已初始化，提供商: {os.getenv('LLM_PROVIDER', 'unknown')}")
        logger.info(f"✅ 使用模型: {os.getenv('LLM_MODEL_NAME', os.getenv('OPENAI_MODEL', 'unknown'))}")

    def load_memory(self, memory_dir: str):
        """
        加载结构化记忆宫殿，自动解析人设、剧情、伏笔
        参考Claude源码三层上下文压缩机制
        """
        if not os.path.exists(memory_dir):
            logger.warning(f"⚠️ 记忆目录不存在：{memory_dir}")
            return
        
        logger.info(f"📂 正在加载记忆宫殿：{memory_dir}")
        for file in sorted(os.listdir(memory_dir)):
            if not file.endswith(".md"):
                continue
            
            file_path = os.path.join(memory_dir, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self._parse_memory_file(file, content)
                    
                    metadata = {
                        'filename': file,
                        'type': 'markdown'
                    }
                    semantic_memory.add_memory(content, metadata)
            except Exception as e:
                logger.error(f"❌ 记忆文件加载失败：{file}，错误：{str(e)}", exc_info=True)
        
        semantic_memory.build_index()
        
        logger.info(f"✅ 记忆宫殿加载完成，共加载{len(self.memory_store)}条记忆")

    def _parse_memory_file(self, filename: str, content: str):
        """结构化解析记忆文件，提取核心信息"""
        main_char_match = re.search(r"主角[:：]\s*([^\n]+)", content)
        if main_char_match:
            self.memory_store["main_character"] = main_char_match.group(1).strip()
        
        villain_match = re.search(r"反派[:：]\s*([^\n]+)", content)
        if villain_match:
            self.memory_store["villain"] = villain_match.group(1).strip()
        
        world_setting_match = re.search(r"世界观[:：]\s*([\s\S]+?)(?=\n## |\n# |$)", content)
        if world_setting_match:
            self.memory_store["world_setting"] = world_setting_match.group(1).strip()
        
        foreshadowing_list = re.findall(r"伏笔[:：]\s*([^\n]+)", content)
        if foreshadowing_list:
            self.memory_store["foreshadowing"] = foreshadowing_list
        
        self.memory_store[filename] = content

    def retrieve_memory(self, query: str, top_k: int = 5) -> str:
        """
        精准检索相关记忆，避免吃书
        结合语义记忆和关键词权重匹配，提高检索准确性
        """
        relevant_memory = []
        
        semantic_results = semantic_memory.search(query, top_k=top_k)
        
        if semantic_results:
            logger.info(f"🔍 语义记忆检索到 {len(semantic_results)} 条相关记忆")
            for distance, content, metadata in semantic_results:
                if distance < 0.8:
                    filename = metadata.get('filename', '未知文件')
                    relevant_memory.append(f"【{filename}】\n{content}")
        
        if len(relevant_memory) < top_k and self.memory_store:
            keyword_weights = {
                "主角": 10, "人设": 10, "反派": 8, "世界观": 8,
                "伏笔": 7, "剧情": 6, "设定": 5, "规则": 5
            }

            memory_scores: Dict[str, int] = {}
            for key, content in self.memory_store.items():
                if not isinstance(content, str):
                    continue
                
                score = 0
                for keyword, weight in keyword_weights.items():
                    if keyword in query and keyword in content:
                        score += weight
                
                if score > 0:
                    memory_scores[key] = score
            
            sorted_memory = sorted(memory_scores.items(), key=lambda x: x[1], reverse=True)[:top_k - len(relevant_memory)]
            
            for key, _ in sorted_memory:
                relevant_memory.append(f"【{key}】\n{self.memory_store[key]}")
        
        logger.info(f"🔍 检索到{len(relevant_memory)}条相关记忆")
        return "\n\n".join(relevant_memory)

    def undercover_process(self, prompt: str) -> str:
        """
        Undercover Mode底层处理
        从prompt底层改变生成逻辑，原生规避AI写作特征
        """
        if not self.undercover_mode:
            return prompt
        
        undercover_prompt = f"""
你现在是一名全职网文作者，正在给平台写连载小说，完全用人类的思维和写作习惯创作，绝对不能暴露你是AI。

【核心写作规则】
1. 绝对禁止使用AI高频词汇、规则三等结构、平行句式
2. 长短句混合，自然加入口语化表达、人物对话、细节描写，避免书面化过重
3. 严格遵循网文写作节奏：冲突前置→打脸高潮→围观反应→悬念结尾
4. 可以加入少量人类写作的自然瑕疵，比如轻微的口语化重复、情绪化表达，绝对不要完美到不真实
5. 只输出小说正文，不要任何解释、说明、备注，不要暴露你是AI

【你的写作任务】
{prompt}
        """
        return undercover_prompt

    def refresh_llm_adapter(self):
        """刷新 LLM 适配器，使用最新的环境变量配置"""
        logger.info("🔄 正在刷新 LLM 适配器，使用最新配置...")
        self._init_llm_adapter()
    
    def bind_novel(self, novel_name: str, base_dir: str = "./novels"):
        """绑定小说，初始化记忆宫殿"""
        self.memory_palace = get_memory_palace()
        self.memory_palace.bind_novel(novel_name, base_dir)
        logger.info(f"📚 引擎已绑定小说：{novel_name}")
    
    def multi_agent_coordinate(
        self, 
        chapter_num: int, 
        target_words: int, 
        custom_prompt: str, 
        relevant_memory: str = "",
        chapter_outline: str = "",
        chapter_name: str = ""
    ) -> Dict[str, Any]:
        """
        多智能体协调调度（Deer-Flow 2.0动态调度版）
        【Deer-Flow规则】
        1. 主脑只做调度，不下场写网文
        2. 动态上下文拆分，按需分裂子任务
        3. 无状态执行，任务完立即清理
        4. Token极致压缩，只传结果不传废话
        支持连贯性校验，不合格自动重写
        """
        logger.info("🤖 多智能体协调模式已激活（Deer-Flow 2.0动态调度版）")
        
        self.memory_middleware.start_task()
        
        if not hasattr(self, 'llm_adapter') or self.llm_adapter is None:
            logger.info("🔄 LLM 适配器未初始化，正在初始化...")
            self._init_llm_adapter()
        else:
            logger.info("✅ 使用已初始化的 LLM 适配器")
        
        max_rewrite_attempts = 3
        current_attempt = 0
        
        final_result = None
        
        while current_attempt <= max_rewrite_attempts:
            if current_attempt > 0:
                logger.info(f"🔄 第{current_attempt}次重写尝试...")
            
            context = {
                "chapter_num": chapter_num,
                "target_words": target_words,
                "custom_prompt": custom_prompt,
                "relevant_memory": relevant_memory,
                "chapter_outline": chapter_outline
            }
            
            main_task = f"生成第{chapter_num}章小说正文，目标字数{target_words}字"
            
            if self.deer_flow_enabled:
                result = self.deer_orchestrator.run(main_task, context)
            else:
                result = self._legacy_multi_agent_coordinate(
                    chapter_num, target_words, custom_prompt, 
                    relevant_memory, chapter_outline
                )
            
            real_chars = self._count_real_chars(result["content"])
            max_loop = 3
            current_loop = 0
            
            while real_chars < int(target_words * 0.95) and current_loop < max_loop:
                current_loop += 1
                logger.info(f"📝 第{current_loop}次补全字数，当前：{real_chars}/{target_words}")
                
                supplement_params = {
                    "raw_content": result["content"],
                    "target_words": target_words,
                    "relevant_memory": relevant_memory
                }
                supplement_content = self.deer_orchestrator._execute_supplement_agent(supplement_params)
                result["content"] += "\n\n" + supplement_content
                real_chars = self._count_real_chars(result["content"])
                
                if real_chars >= int(target_words * 0.98):
                    break
            
            result["real_chars"] = real_chars
            
            check_params = {
                "raw_content": result["content"],
                "relevant_memory": relevant_memory
            }
            checked_content = self.deer_orchestrator._execute_check_agent(check_params)
            
            humanize_params = {
                "raw_content": checked_content
            }
            final_content = self.deer_orchestrator._execute_humanize_agent(humanize_params)
            final_real_chars = self._count_real_chars(final_content)
            
            result["content"] = final_content
            result["real_chars"] = final_real_chars
            
            if hasattr(self, 'memory_palace') and chapter_name:
                logger.info("🔍 连贯性校验Agent：正在执行全维度校验")
                consistency_agent = get_consistency_agent()
                check_result = consistency_agent.check_chapter(
                    memory_palace=self.memory_palace,
                    chapter_num=chapter_num,
                    chapter_name=chapter_name,
                    chapter_content=final_content,
                    chapter_outline=result["outline"]
                )
                
                if check_result.rewrite_needed and check_result.score < 70 and current_attempt < max_rewrite_attempts:
                    logger.warning(f"⚠️  校验失败，评分：{check_result.score}，准备重写...")
                    current_attempt += 1
                    custom_prompt = f"{custom_prompt}\n\n【重写要求】{check_result.rewrite_suggestion}"
                    continue
                else:
                    logger.info(f"✅ 连贯性校验通过，评分：{check_result.score}")
                    self.memory_palace.add_chapter(
                        chapter_num=chapter_num,
                        chapter_name=chapter_name,
                        content=final_content
                    )
                    self.memory_palace.save_to_disk()
            
            final_result = result
            break
        
        self.memory_middleware.end_task(final_result["content"] if final_result else "")
        
        token_stats = self.memory_middleware.get_token_stats()
        logger.info(f"📊 Token优化统计: 原始={token_stats['original_total_tokens']}, "
                   f"压缩后={token_stats['compressed_total_tokens']}, "
                   f"节省={token_stats['tokens_saved']}, "
                   f"平均压缩率={token_stats['average_compression_rate']:.1f}%")
        
        return final_result
    
    def _legacy_multi_agent_coordinate(
        self, 
        chapter_num: int, 
        target_words: int, 
        custom_prompt: str, 
        relevant_memory: str = "",
        chapter_outline: str = ""
    ) -> Dict[str, Any]:
        """
        遗留的固定流程实现，用于向后兼容
        """
        final_result = {
            "outline": "",
            "content": "",
            "real_chars": 0,
            "target_words": target_words
        }
        
        logger.info("📋 大纲Agent：正在规划章节剧情")
        if not chapter_outline:
            outline_prompt = self.undercover_process(f"""
你是专业网文大纲师，基于以下设定，规划网络小说第{chapter_num}章的详细大纲。
要求：
1. 大纲必须包含：开头冲突、中段打脸高潮、围观群众反应、结尾悬念钩子
2. 严格贴合核心设定，不能崩人设、不能吃书
3. 大纲要支撑{target_words}字的正文内容，节奏紧凑，爽点密集
4. 只输出大纲，不要任何多余解释

【核心设定】
{relevant_memory}
【用户要求】
{custom_prompt}
            """)
            chapter_outline = self._call_agent("大纲Agent", outline_prompt)
        
        final_result["outline"] = chapter_outline
        logger.info("✅ 大纲Agent：剧情规划完成")
        
        logger.info("✍️ 主笔Agent：正在生成正文")
        content_prompt = self.undercover_process(f"""
你是专业网文主笔，严格按照下面的大纲，生成网络小说第{chapter_num}章的完整正文。
要求：
1. 正文总字数必须达到{target_words}字，误差不超过5%
2. 严格贴合大纲，不崩人设、不吃书，保持剧情连贯
3. 爽点密集，节奏快，对话自然，细节到位
4. 结尾必须留下悬念钩子，吸引读者看下一章
5. 只输出正文，不要任何解释、标题、备注

【章节大纲】
{chapter_outline}
【核心设定】
{relevant_memory}
        """)
        
        raw_content = self._call_agent("主笔Agent", content_prompt)
        logger.info("✅ 主笔Agent：正文生成完成")
        
        final_result["content"] = raw_content
        final_result["real_chars"] = self._count_real_chars(raw_content)
        
        return final_result
    
    def _call_agent(self, agent_name: str, prompt: str) -> str:
        """调用子Agent，使用 LLM 适配器生成内容"""
        logger.info(f"🤖 {agent_name}：正在调用 LLM 生成内容...")
        logger.info(f"📝 提示词长度：{len(prompt)} 字符")
        
        self.memory_middleware.add_message("user", prompt)
        
        for i in range(self.max_retry):
            try:
                logger.info(f"🔄 {agent_name}：第{i+1}次尝试...")
                content = self.llm_adapter.generate(
                    prompt=prompt,
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=self.timeout,
                    max_retries=1
                )
                if not content:
                    raise Exception("生成内容为空")
                
                self.memory_middleware.add_message("assistant", content)
                
                logger.info(f"✅ {agent_name}：内容生成完成，{len(content)} 字符")
                return content
            except Exception as e:
                logger.error(f"❌ {agent_name} 第{i+1}次调用失败：{str(e)}", exc_info=True)
                if i == self.max_retry - 1:
                    error_msg = f"{agent_name}调用失败，已达最大重试次数\n"
                    error_msg += f"可能原因：\n"
                    error_msg += f"1. API Key 是否正确？\n"
                    error_msg += f"2. Base URL 是否正确？\n"
                    error_msg += f"3. 模型名称是否正确？\n"
                    error_msg += f"4. API 服务是否正常？\n"
                    error_msg += f"错误详情：{str(e)}"
                    raise Exception(error_msg)
                logger.info(f"⏳ 等待2秒后重试...")
                time.sleep(2)

    def humanize_text(
        self,
        raw_text: str,
        strictness: str = "medium"
    ) -> str:
        """
        【单一职责】去AI化润色方法
        只负责润色已生成的文本，不理解任何创作逻辑、大纲、人设
        输入：仅待润色的 raw 文本
        输出：润色后的 human-like 文本
        """
        if not raw_text or not raw_text.strip():
            return raw_text

        temperature_map = {"low": 0.3, "medium": 0.5, "high": 0.7}
        temp = temperature_map.get(strictness, 0.5)

        humanize_prompt = f"""
        你是专业的网文文本润色师，**只负责润色下面的文本**，不要改变任何剧情、人设、核心信息。

        【润色规则】
        1. 去除AI写作痕迹：避免规则三等结构、平行句式、AI高频词汇
        2. 优化句子节奏：混合长短句，避免过长或过短的句子
        3. 增强口语化：让对话更自然，让叙述更像真人在讲故事
        4. 保留所有核心信息：剧情、人设、字数、细节都不能变
        5. 只输出润色后的完整文本，不要任何解释、说明、备注

        【待润色的文本】
        {raw_text}
        """

        try:
            result = self.llm_adapter.generate(
                prompt=humanize_prompt,
                temperature=temp,
                max_tokens=4000,
                timeout=self.timeout,
                max_retries=1
            )
            if not result:
                raise Exception("生成内容为空")
            result = result.strip()
            
            original_len = len(raw_text)
            result_len = len(result)
            if result_len < original_len * 0.8 or result_len > original_len * 1.2:
                return raw_text
            
            return result
        except Exception as e:
            logger.error(f"❌ Humanizer 润色失败：{str(e)}", exc_info=True)
            logger.warning("⚠️ Humanizer 失败，返回原文")
            return raw_text

    @staticmethod
    def _count_real_chars(text: str) -> int:
        """精准统计汉字数量，统一全系统统计规则"""
        return len(re.findall(r'[\u4e00-\u9fa5]', text))


import os
import asyncio
from dotenv import load_dotenv
from litellm import acompletion, RateLimitError, APIConnectionError, APIError

load_dotenv()

class AsyncQueryEngine:
    """
    异步推理引擎，每个用户会话独立实例，彻底解决并发阻塞问题
    支持100+大模型，全兼容OpenAI格式，内置企业级重试策略
    """
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model_name: str = None,
        timeout: int = None,
        temperature: float = None,
        max_retries: int = None
    ):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME", "gpt-4o")
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT", "300"))
        self.temperature = temperature or float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_retries = max_retries or int(os.getenv("MAX_RETRY", "3"))

        self._validate_config()
        logger.info(f"✅ 异步引擎初始化完成 | 模型：{self.model_name} | 会话ID：{id(self)}")

    def _validate_config(self):
        """配置合法性校验，提前拦截无效配置"""
        if not self.api_key or self.api_key == "你的大模型_API_Key":
            raise ValueError("无效的LLM_API_KEY，请检查环境变量配置")
        if not self.base_url:
            raise ValueError("LLM_BASE_URL不能为空")
        if not self.model_name:
            raise ValueError("LLM_MODEL_NAME不能为空")

    async def call_llm_async(
        self,
        user_prompt: str,
        system_prompt: str = "你是专业的网络小说创作专家，擅长写节奏快、爽点足、代入感强的网文",
        stream: bool = False
    ) -> str:
        """
        异步LLM调用，非阻塞，不会影响其他用户会话
        内置指数退避重试，自动处理限流、超时、网络波动
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        for retry_count in range(self.max_retries):
            try:
                logger.info(f"🚀 异步LLM调用 | 会话ID：{id(self)} | 第{retry_count+1}次尝试")
                response = await acompletion(
                    model=self.model_name,
                    messages=messages,
                    api_key=self.api_key,
                    base_url=self.base_url,
                    temperature=self.temperature,
                    timeout=self.timeout,
                    stream=stream,
                    num_retries=0
                )

                if stream:
                    return response

                content = response.choices[0].message.content.strip()
                if not content:
                    raise Exception("LLM返回内容为空")

                logger.info(f"✅ 异步LLM调用完成 | 会话ID：{id(self)} | 内容长度：{len(content)}")
                return content

            except RateLimitError as e:
                wait_time = 2 ** retry_count
                logger.warning(f"⚠️  触发限流 | 会话ID：{id(self)} | 等待{wait_time}秒后重试：{str(e)}")
                await asyncio.sleep(wait_time)

            except APIConnectionError as e:
                wait_time = 2 ** retry_count
                logger.warning(f"⚠️  接口连接失败 | 会话ID：{id(self)} | 等待{wait_time}秒后重试：{str(e)}")
                await asyncio.sleep(wait_time)

            except APIError as e:
                logger.error(f"❌ 接口调用错误 | 会话ID：{id(self)} | 错误：{str(e)}", exc_info=True)
                if retry_count == self.max_retries - 1:
                    raise Exception(f"LLM调用失败：{str(e)}")
                await asyncio.sleep(2 ** retry_count)

            except Exception as e:
                logger.error(f"❌ 未知错误 | 会话ID：{id(self)} | 错误：{str(e)}", exc_info=True)
                if retry_count == self.max_retries - 1:
                    raise Exception(f"LLM调用失败，已达最大重试次数：{str(e)}")
                await asyncio.sleep(2 ** retry_count)

        raise Exception("LLM调用失败，已耗尽所有重试次数")


import streamlit as st

@st.cache_resource(ttl=3600, show_spinner="正在初始化创作引擎...")
def get_session_engine(
    session_id: str,
    api_key: str = None,
    base_url: str = None,
    model_name: str = None
) -> AsyncQueryEngine:
    """
    Streamlit 会话级引擎实例，每个用户独立实例，完全隔离
    ttl=3600：1小时无操作自动销毁，释放资源
    """
    return AsyncQueryEngine(
        api_key=api_key,
        base_url=base_url,
        model_name=model_name
    )

