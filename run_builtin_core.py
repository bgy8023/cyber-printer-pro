#!/usr/bin/env python3
# 赛博印钞机 Pro - 简化版核心引擎（直接使用 LLM API）
# 替代 run_openmars.sh，不需要外部 openmars 命令

import os
import sys
import time
import re
import argparse
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import get_resource_path
from utils.logger import Logger


def load_skills() -> str:
    """加载网文创作专属技能"""
    try:
        from skill_loader import get_skill_loader
        loader = get_skill_loader()
        skills = loader.get_all_skills()
        
        if skills:
            skill_parts = []
            skill_parts.append("你是一位专业的网文创作助手，拥有以下专业技能：\n")
            
            for skill_name, skill_content in skills.items():
                skill_parts.append(f"\n## {skill_name}\n")
                skill_parts.append(skill_content)
            
            skill_parts.append("\n请根据以上技能指导，为用户提供专业的网文创作帮助。")
            return "\n".join(skill_parts)
        return ""
    except Exception as e:
        print(f"⚠️  加载技能失败：{str(e)}")
        return ""


def count_real_chars(text: str) -> int:
    """统计有效汉字数量"""
    chinese_chars = re.findall(r"[\u4e00-\u9fa5]", text)
    return len(chinese_chars)


def load_structured_memory(novel_settings_dir: str, chapter_num: int) -> str:
    """加载结构化记忆"""
    memory_file = os.path.join(novel_settings_dir, "2_剧情自动推演记录.md")
    memory_content = ""
    
    if os.path.exists(memory_file):
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            relevant_lines = []
            for line in lines:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in ["主角", "反派", "核心设定", f"第{chapter_num-1}章", "伏笔"]):
                    relevant_lines.append(line.strip())
            
            memory_content = "\n".join(relevant_lines[:50])
        except Exception as e:
            print(f"⚠️  加载结构化记忆失败：{str(e)}")
    
    return memory_content


def generate_with_litellm(
    prompt: str,
    system_prompt: Optional[str] = None,
    timeout: int = 300,
) -> str:
    """
    使用 LiteLLM 直接调用 LLM
    不需要外部 openmars 命令
    """
    try:
        import litellm
        from dotenv import load_dotenv
        
        env_path = get_resource_path(".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
        
        api_key = os.getenv("LLM_API_KEY")
        model = os.getenv("LLM_MODEL_NAME", "gpt-4")
        base_url = os.getenv("API_BASE_URL") or os.getenv("LLM_BASE_URL")
        
        # 对于 OpenAI 兼容的 API，添加 openai/ 前缀
        if not model.startswith(("openai/", "anthropic/", "deepseek/", "ollama/")):
            model = f"openai/{model}"
        
        if not api_key:
            raise Exception("未找到 LLM_API_KEY，请配置 .env 文件")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        print(f"🤖 正在调用 LLM 生成内容（模型：{model}）...")
        
        response = litellm.completion(
            model=model,
            messages=messages,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )
        
        content = response.choices[0].message.content
        print("✅ 生成成功")
        return content
        
    except ImportError as e:
        raise Exception(f"缺少依赖：{str(e)}\n请运行：pip install litellm python-dotenv")
    except Exception as e:
        raise Exception(f"LLM 调用失败：{str(e)}")


def generate_chapter_simple(
    chapter_num: int,
    prompt: str,
    target_words: int,
    agent_name: str = "main-2",
    enable_humanizer: bool = True,
    enable_multi_agent: bool = True,
    enable_skills: bool = True,
) -> str:
    """
    简化版章节生成（直接使用 LLM API）
    """
    resource_dir = os.path.dirname(os.path.abspath(__file__))
    novel_settings_dir = os.path.join(resource_dir, "novel_settings")
    
    print("=" * 60)
    print(f"🚀 赛博印钞机 Pro - 简化核心引擎启动")
    print(f"📖 第 {chapter_num} 章生成任务")
    print("=" * 60)
    
    # 0. 加载网文创作专属技能
    skills_system_prompt = ""
    if enable_skills:
        print("🎯 正在加载网文创作专属技能...")
        skills_system_prompt = load_skills()
        if skills_system_prompt:
            print(f"✅ 已加载 {len(skills_system_prompt)} 字技能指导")
        else:
            print("ℹ️  技能加载失败或为空，使用默认模式")
    
    # 1. 加载结构化记忆
    print("🧠 正在加载结构化记忆...")
    structured_memory = load_structured_memory(novel_settings_dir, chapter_num)
    if structured_memory:
        print(f"✅ 已加载 {len(structured_memory.splitlines())} 行结构化记忆")
    else:
        print("ℹ️  未找到结构化记忆")
    
    final_content = ""
    
    if enable_multi_agent:
        print("🤝 多智能体协调模式已激活")
        
        # 子代理1：大纲规划
        print("📋 子代理1（大纲师）：正在规划剧情...")
        outline_prompt = f"""你是专业网文大纲师，基于以下结构化记忆和核心要求，规划第{chapter_num}章的详细剧情大纲，要求有冲突、有打脸、有悬念，严格防吃书，不崩人设，只输出大纲，不要多余解释。

【结构化记忆】
{structured_memory}

【核心要求】
{prompt}"""
        
        try:
            chapter_outline = generate_with_litellm(outline_prompt, system_prompt=skills_system_prompt, timeout=60)
            print("✅ 子代理1：大纲规划完成")
        except Exception as e:
            print(f"❌ 大纲规划失败：{str(e)}")
            print("💡 切换到单 Agent 模式")
            enable_multi_agent = False
        
        # 子代理2：正文生成
        if enable_multi_agent:
            print("✍️ 子代理2（主笔）：正在生成正文...")
            content_prompt = f"""你是专业网文主笔，严格遵循以下大纲，生成第{chapter_num}章完整正文，字数要求{target_words}字，严格保留人设，爽点密集，结尾留悬念，只输出正文，不要任何多余解释。

【大纲】
{chapter_outline}

【核心要求】
{prompt}"""
            
            try:
                generated_content = generate_with_litellm(content_prompt, system_prompt=skills_system_prompt, timeout=240)
                print("✅ 子代理2：正文生成完成")
            except Exception as e:
                print(f"❌ 正文生成失败：{str(e)}")
                sys.exit(1)
        
        # 子代理3：校验优化
        if enable_multi_agent:
            print("🔍 子代理3（校验师）：正在校验内容...")
            check_prompt = f"""你是专业网文校验师，检查下面的小说正文，核对人设和剧情是否符合结构化记忆，核对字数是否达标，优化结尾悬念，修正吃书问题，只输出优化后的完整正文，不要任何多余解释。

【结构化记忆】
{structured_memory}

【目标字数】
{target_words}字

【正文】
{generated_content}"""
            
            try:
                final_content = generate_with_litellm(check_prompt, system_prompt=skills_system_prompt, timeout=120)
                print("✅ 子代理3：校验优化完成")
            except Exception as e:
                print(f"⚠️  校验优化失败，保留原始正文：{str(e)}")
                final_content = generated_content
    
    # 单 Agent 模式（兜底）
    if not enable_multi_agent or not final_content:
        print("🤖 单 Agent 模式已激活，正在生成正文...")
        single_prompt = f"""生成第 {chapter_num} 章。字数要求：{target_words}字。

【核心要求】
{prompt}

【结构化记忆】
{structured_memory}

只输出正文，不要任何多余解释。"""
        
        try:
            final_content = generate_with_litellm(single_prompt, system_prompt=skills_system_prompt, timeout=300)
            print("✅ 正文生成完成")
        except Exception as e:
            print(f"❌ 正文生成失败：{str(e)}")
            sys.exit(1)
    
    # Humanizer 二次去 AI 化
    if enable_humanizer:
        print("🧹 正在二次去 AI 化...")
        humanize_prompt = f"""请对下面的小说正文进行二次去AI化处理，严格保留原剧情、人设、爽点、节奏和字数，只去除残留的AI痕迹，让文本更像真人写的网文，直接输出改写后的完整正文，不要任何额外解释：

【正文】
{final_content}"""
        
        try:
            final_content = generate_with_litellm(humanize_prompt, timeout=180)
            print("✅ 二次去 AI 化完成")
        except Exception as e:
            print(f"⚠️  去 AI 化失败，保留原始正文：{str(e)}")
    
    # 字数统计
    real_chars = count_real_chars(final_content)
    print("=" * 60)
    print(f"📊 最终有效汉字：{real_chars}字（目标{target_words}字）")
    
    if real_chars < target_words * 0.95:
        print(f"⚠️  提示：实际字数少于目标的 95%")
    else:
        print("✅ 字数达标")
    
    print("=" * 60)
    print("✅ 全流程执行完成")
    
    return final_content


def main():
    parser = argparse.ArgumentParser(description="赛博印钞机 Pro - 简化核心引擎")
    parser.add_argument("chapter_num", type=int, help="章节号")
    parser.add_argument("prompt", type=str, help="核心要求提示词")
    parser.add_argument("target_words", type=int, help="目标字数")
    parser.add_argument("agent_name", type=str, nargs="?", default="main-2", help="Agent 名称")
    parser.add_argument("enable_humanizer", type=str, nargs="?", default="true", help="是否启用 Humanizer")
    parser.add_argument("enable_multi_agent", type=str, nargs="?", default="true", help="是否启用多 Agent")
    parser.add_argument("enable_skills", type=str, nargs="?", default="true", help="是否启用网文创作专属技能")
    
    args = parser.parse_args()
    
    # 解析布尔参数
    enable_humanizer = args.enable_humanizer.lower() in ["true", "1", "yes"]
    enable_multi_agent = args.enable_multi_agent.lower() in ["true", "1", "yes"]
    enable_skills = args.enable_skills.lower() in ["true", "1", "yes"]
    
    # 生成内容
    content = generate_chapter_simple(
        chapter_num=args.chapter_num,
        prompt=args.prompt,
        target_words=args.target_words,
        agent_name=args.agent_name,
        enable_humanizer=enable_humanizer,
        enable_multi_agent=enable_multi_agent,
        enable_skills=enable_skills,
    )
    
    # 写入输出文件
    openmars_workspace = os.path.expanduser("~/.openmars/workspace")
    os.makedirs(openmars_workspace, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    output_file = os.path.join(openmars_workspace, f"第{args.chapter_num}章_{timestamp}.md")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ 最终文件已写入：{output_file}")
    
    # 输出到 stdout（供父进程捕获）
    print(content)


if __name__ == "__main__":
    main()
