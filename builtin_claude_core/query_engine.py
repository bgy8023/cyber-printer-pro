
import os
import re
import time
from typing import List, Dict, Any, Optional
from .logger import logger
from .semantic_memory import semantic_memory
from .llm_adapter import get_llm_adapter


class ClaudeQueryEngine:
    """
    Claude Code泄露源码原生实现的QueryEngine核心推理引擎
    负责：多智能体调度、结构化记忆管理、上下文压缩、Undercover Mode底层处理
    """
    def __init__(self, llm_provider: Optional[str] = None):
        self.memory_store: Dict[str, Any] = {}
        self.agent_pool: Dict[str, Any] = {}
        self.undercover_mode = True
        self.max_retry = 3
        self.timeout = 300
        self.llm_provider = llm_provider
        # 初始化 LLM 适配器
        self._init_llm_adapter()
        logger.info("✅ Claude QueryEngine 初始化完成")
    
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
                    
                    # 添加到语义记忆系统
                    metadata = {
                        'filename': file,
                        'type': 'markdown'
                    }
                    semantic_memory.add_memory(content, metadata)
            except Exception as e:
                logger.error(f"❌ 记忆文件加载失败：{file}，错误：{str(e)}", exc_info=True)
        
        # 构建语义记忆索引
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
        
        # 1. 使用语义记忆系统进行检索
        semantic_results = semantic_memory.search(query, top_k=top_k)
        
        if semantic_results:
            logger.info(f"🔍 语义记忆检索到 {len(semantic_results)} 条相关记忆")
            for distance, content, metadata in semantic_results:
                # 距离越小，相关性越高
                if distance < 0.8:  # 设置阈值
                    filename = metadata.get('filename', '未知文件')
                    relevant_memory.append(f"【{filename}】\n{content}")
        
        # 2. 如果语义记忆检索结果不足，使用关键词权重匹配作为补充
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
    
    def multi_agent_coordinate(self, chapter_num: int, target_words: int, custom_prompt: str, relevant_memory: str) -> Dict[str, Any]:
        """
        多智能体协调调度，参考Claude源码Coordinator模式
        分工：大纲Agent→主笔Agent→审核Agent→润色Agent，流水线式创作
        """
        logger.info("🤖 多智能体协调模式已激活")
        
        # 检查 LLM 适配器是否初始化，没有的话才初始化
        if not hasattr(self, 'llm_adapter') or self.llm_adapter is None:
            logger.info("🔄 LLM 适配器未初始化，正在初始化...")
            self._init_llm_adapter()
        else:
            logger.info("✅ 使用已初始化的 LLM 适配器")
        
        final_result = {
            "outline": "",
            "content": "",
            "real_chars": 0,
            "target_words": target_words
        }

        logger.info("📋 大纲Agent：正在规划章节剧情")
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

        outline_content = self._call_agent("大纲Agent", outline_prompt)
        final_result["outline"] = outline_content
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
{outline_content}
【核心设定】
{relevant_memory}
        """)

        raw_content = self._call_agent("主笔Agent", content_prompt)
        logger.info("✅ 主笔Agent：正文生成完成")

        real_chars = self._count_real_chars(raw_content)
        max_loop = 5
        current_loop = 0

        while real_chars < int(target_words * 0.95) and current_loop < max_loop:
            current_loop += 1
            logger.info(f"📝 第{current_loop}次补全字数，当前：{real_chars}/{target_words}")
            
            supplement_prompt = self.undercover_process(f"""
基于上文结尾续写小说正文，补全到{target_words}字，保持剧情连贯，人设不崩，只输出续写的内容，不要重复上文。
上文结尾：{raw_content[-2000:]}
核心设定：{relevant_memory}
            """)
            
            supplement_content = self._call_agent("补全Agent", supplement_prompt)
            raw_content += "\n\n" + supplement_content
            real_chars = self._count_real_chars(raw_content)

        final_result["content"] = raw_content
        final_result["real_chars"] = real_chars
        logger.info(f"✅ 正文最终字数：{real_chars}/{target_words}")

        logger.info("🔍 审核Agent：正在校验内容")
        check_prompt = f"""
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

        checked_content = self._call_agent("审核Agent", check_prompt)
        final_result["content"] = checked_content
        final_result["real_chars"] = self._count_real_chars(checked_content)
        logger.info("✅ 审核Agent：内容校验完成")

        logger.info("🧹 润色Agent：正在去AI化优化")
        humanize_prompt = self.undercover_process(f"""
你是专业网文润色师，对下面的小说正文进行去AI化润色。
要求：
1. 严格保留原剧情、人设、爽点、总字数不变
2. 优化句子节奏，混合长短句，让文本更像真人写的网文
3. 去除AI写作痕迹，让对话更自然，细节更生动
4. 只输出润色后的完整正文，不要任何解释、备注

【小说正文】
{checked_content}
        """)

        final_content = self._call_agent("润色Agent", humanize_prompt)
        final_result["content"] = final_content
        final_result["real_chars"] = self._count_real_chars(final_content)
        logger.info("✅ 润色Agent：去AI化优化完成")

        return final_result

    def _call_agent(self, agent_name: str, prompt: str) -> str:
        """调用子Agent，使用 LLM 适配器生成内容"""
        logger.info(f"🤖 {agent_name}：正在调用 LLM 生成内容...")
        logger.info(f"📝 提示词长度：{len(prompt)} 字符")
        
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

    def humanize_text(self, text: str) -> str:
        """
        超强 Humanizer 去AI化润色
        基于维基百科 "Signs of AI writing" 指南和行业最佳实践
        将 AI 生成的文本转化为自然的人类写作风格
        """
        logger.info("🧹 超强 Humanizer：开始去AI化润色")
        
        humanize_prompt = self.undercover_process(f"""【角色定义】
你是一位拥有15年经验的资深网文编辑，同时也是网文心理学专家。你深谙中文网文的读者心理、节奏把控和写作技巧。

【核心任务】
对下面的小说正文进行深度去AI化润色，让它看起来、读起来都像是一位有经验的真人作者写的。

【维基百科 AI 写作特征去除清单】

### 第一阶段：内容模式修复
1. **去除过度强调重要性**：
   - 去掉"标志着/代表着/见证着/是转折点/重要时刻/关键作用"等
   - 去掉"反映了更广泛的趋势/象征着持久的贡献/为...奠定基础"
   - 改为直接叙述事实

2. **去除过度强调知名度**：
   - 去掉"被多家媒体报道/独立报道/社会广泛关注"
   - 去掉"拥有大量粉丝/活跃的社交媒体"
   - 改为具体的一个引用或场景

3. **去除肤浅的 -ing 分析**：
   - 去掉"强调着/确保着/反映着/象征着..."
   - 改为直接的陈述句

4. **去除模糊的归属**：
   - 去掉"有人说/人们认为/众所周知/据说..."
   - 要么具体到人，要么直接陈述

5. **去除破折号滥用**：
   - AI 喜欢用 — 来连接，改成逗号、句号或重新组织

6. **去除三段式套路**：
   - AI 喜欢"首先/其次/最后""一方面/另一方面"
   - 改成自然的叙述流

### 第二阶段：语言和语法修复
7. **替换AI高频词汇**：
   - 去掉：此外、与之相一致、至关重要、深入探讨、因此、从而、进而、
     鉴于、基于、鉴于此、综上所述、总而言之、据此
   - 换成自然的中文连接：而且、不过、其实、话说回来、当然、
     你还别说、有意思的是

8. **去除否定平行结构**：
   - 去掉"不是...而是...""与其...不如..."
   - 改成更自然的表达

9. **去除过度的连接短语**：
   - 去掉：此外、再者、更进一步、更重要的是
   - 让段落自然流动

### 第三阶段：段落和结构修复
10. **混合句子长度**：
    - 不要所有句子都是差不多长
    - 短句：有力、冲击
    - 长句：细腻、铺垫
    - 交替使用

11. **段落不要太规整**：
    - AI 喜欢每个段落长度差不多
    - 有的段落一句话，有的段落很详细
    - 制造节奏变化

12. **加入一点"凌乱"**：
    - 完美的结构反而像AI
    - 可以有一个小的题外话、回忆片段
    - 可以有一个未完成的想法、伏笔

### 第四阶段：人格和灵魂注入（最重要！）
13. **加入观点和情绪**：
    - 不要中立的报道
    - "我觉得这件事有点奇怪" 比 "这件事很奇怪" 更像人
    - 角色可以有犹豫、矛盾、小偏见

14. **承认复杂性**：
    - 人类有混合情绪
    - "这很爽，但也有点不安" 比 "这很爽" 更真实

15. **用第一人称视角（如果合适）**：
    - 主角的内心戏用"我"
    - "我心里咯噔一下" 比 "他心里咯噔一下" 更有代入感

16. **让一些"不完美"存在**：
    - 可以有口语化表达
    - 可以有重复（但不要太多）
    - 可以有逻辑上的"毛边"

17. **加入感官细节**：
    - 不仅写视觉，还要写听觉、嗅觉、触觉、味觉
    - "血腥味涌上来" 比 "他闻到血腥味" 更生动

### 第五阶段：中文网文专属优化
18. **对话优化**：
    - 不要每个人说话都像播音员
    - 有的人口头禅多，有的人话少
    - 可以有打断、抢话、结巴
    - 可以有没说完的话

19. **节奏把控**：
    - 战斗/紧张场景：短句多，段落短
    - 抒情/铺垫场景：长句多，段落长
    - 一张一弛

20. **加入网文元素**：
    - 可以有一句吐槽（如果符合人设）
    - 可以有一个"伏笔感"的句子
    - 可以有角色的内心吐槽

【硬性规则】
- ✅ 严格保留：原剧情、人设、爽点、关键信息
- ✅ 尽量保持：总字数（±10%）
- ❌ 不要输出：任何解释、说明、备注
- ❌ 不要改变：故事走向、角色性格
- ✅ 只输出：润色后的完整正文

【小说正文】
{text}

【输出要求】
直接开始输出润色后的正文，不要任何开场白。""")
        
        try:
            humanized_content = self._call_agent("超强润色Agent", humanize_prompt)
            logger.info("✅ 超强 Humanizer：去AI化润色完成")
            
            # 二次反AI检查（可选但推荐）
            final_check_prompt = self.undercover_process(f"""【反AI最终检查】
读下面这段文字，简要回答：
1. 这段话里还有哪些明显的AI痕迹？（列出1-3点）
2. 只列问题，不要修改

【待检查文本】
{humanized_content}""")
            
            logger.info("🔍 进行最终反AI检查...")
            ai_check_result = self._call_agent("反AI检查员", final_check_prompt)
            logger.info(f"📋 反AI检查结果：{ai_check_result[:200]}")
            
            # 如果检查出问题，再润色一次（但不强制，避免死循环）
            if "AI痕迹" in ai_check_result or "痕迹" in ai_check_result:
                logger.info("🔄 发现AI痕迹，进行最终微调...")
                final_polish_prompt = self.undercover_process(f"""【最终微调】
刚才的润色还有这些AI痕迹，再微调一下，不要改动剧情：
{ai_check_result}

【原文】
{humanized_content}

只输出修改后的正文。""")
                humanized_content = self._call_agent("微调Agent", final_polish_prompt)
                logger.info("✅ 最终微调完成")
            
            return humanized_content
        except Exception as e:
            logger.error(f"❌ 超强 Humanizer 润色失败：{str(e)}", exc_info=True)
            logger.warning("⚠️ Humanizer 失败，返回原文")
            return text

    @staticmethod
    def _count_real_chars(text: str) -> int:
        """精准统计汉字数量，统一全系统统计规则"""
        return len(re.findall(r'[\u4e00-\u9fa5]', text))
