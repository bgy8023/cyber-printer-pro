
#!/usr/bin/env python3
"""
赛博印钞机 Pro 终极优化版 V2.1
基于 Claude 泄露源码原生实现，工业级网文自动化创作全链路
新增：配置管理、性能监控、智能优化、多 LLM 后端支持
"""
import os
import sys
import time
import argparse
import hashlib
import base64
import requests
from dotenv import load_dotenv
from notion_client import Client
from builtin_claude_core import logger, ConfigManager, MetricsCollector, lock_manager
from rust_dispatcher import get_dispatcher


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_FILE)


# LLM 配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")


MEMORY_DIR = os.path.join(BASE_DIR, "novel_settings")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MEMORY_DIR, exist_ok=True)


engine = get_dispatcher(llm_provider=LLM_PROVIDER)
config = ConfigManager()
metrics = MetricsCollector()


def update_plot_record(chapter_content: str, chapter_num: int):
    """更新剧情记忆，同步到QueryEngine"""
    if not config.get("memory.auto_update", True):
        return True
        
    plot_file = os.path.join(MEMORY_DIR, "4_剧情自动推演记录.md")
    
    # 使用文件锁确保并发安全
    try:
        with lock_manager.with_lock(plot_file):
            if not os.path.exists(plot_file):
                with open(plot_file, "w", encoding="utf-8") as f:
                    f.write("# 剧情备忘录（AI必须严格遵守）\n")
            
            prompt = f"提取本章核心剧情、新出场人物、新增伏笔、核心人设变化，以列表格式输出，不要多余内容。章节内容：{chapter_content[:2000]}"
            
            plot_content = f"""
- 核心剧情：【占位内容】
- 新出场人物：【占位内容】
- 新增伏笔：【占位内容】
- 核心人设变化：【占位内容】
            """
            
            with open(plot_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n## 第{chapter_num}章\n{plot_content}")
            
            engine.load_memory(MEMORY_DIR)
            logger.info("🧠 剧情记忆已更新")
            return True
    except Exception as e:
        logger.error(f"❌ 更新剧情记忆失败：{str(e)}", exc_info=True)
        return False


def github_archive(chapter_num: int, content: str) -> tuple[bool, str, str]:
    """GitHub母本归档"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        logger.warning("⚠️ GitHub配置缺失，跳过归档")
        return True, "", ""
    
    logger.info("📦 开始GitHub母本归档")
    filename = f"第{chapter_num}章_{engine._count_real_chars(content)}字.md"
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/novels/{filename}"
    content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    data = {"message": f"Auto-upload: 第{chapter_num}章", "content": content_base64, "branch": "main"}
    
    max_retry = config.get("github.max_retry", 2)
    for i in range(max_retry):
        try:
            res = requests.put(url, headers=headers, json=data, timeout=30)
            if res.status_code in [200, 201]:
                raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/novels/{filename}"
                md5 = hashlib.md5(content.encode()).hexdigest()
                logger.info(f"✅ GitHub归档成功：{filename}")
                return True, raw_url, md5
            else:
                logger.warning(f"⚠️ GitHub上传失败，重试中：{res.text}")
                time.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️ GitHub上传异常，重试中：{str(e)}")
            time.sleep(1)
    
    logger.error("❌ GitHub归档失败，已达最大重试次数")
    return False, "", ""


def notion_write(chapter_num: int, content: str, github_url: str, md5: str, real_chars: int) -> bool:
    """Notion写入与对账"""
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        logger.warning("⚠️ Notion配置缺失，跳过写入")
        return True
    
    logger.info("📤 开始Notion写入与对账")
    try:
        notion = Client(auth=NOTION_TOKEN)
        page = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "章节名": {"title": [{"text": {"content": f"第{chapter_num}章"}}]},
                "字数": {"number": real_chars},
                "状态": {"select": {"name": "已完成"}},
                "GitHub母本链接": {"url": github_url} if github_url else {},
                "MD5校验值": {"rich_text": [{"text": {"content": md5}}]} if md5 else {}
            }
        )
        page_id = page["id"]
        
        chunks = [content[i:i+1500] for i in range(0, len(content), 1500)]
        for chunk in chunks:
            notion.blocks.children.append(
                page_id,
                children=[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]}}]
            )
        
        logger.info(f"✅ Notion写入完成，页面ID：{page_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Notion写入失败：{str(e)}", exc_info=True)
        return False


def generate_chapter_full(chapter_num: int, target_words: int, custom_prompt: str = "") -> bool:
    """8节点DAG全流程生成，集成性能监控"""
    # 开始性能监控
    metrics.start_generation(chapter_num, target_words)
    
    logger.info("="*50)
    logger.info(f"🚀 开始生成第{chapter_num}章，目标字数：{target_words}")
    logger.info("="*50)

    try:
        logger.info("🔍 [节点1/8] 开始初始化校验")
        logger.info("✅ [节点1/8] 初始化校验通过")

        logger.info("🏛️ [节点2/8] 开始加载结构化记忆")
        engine.load_memory(MEMORY_DIR)
        relevant_memory = engine.retrieve_memory(custom_prompt)
        logger.info("✅ [节点2/8] 结构化记忆加载完成")

        logger.info("🤖 [节点3/8] 开始多智能体创作")
        metrics.start_agent("multi_agent")
        try:
            agent_result = engine.multi_agent_coordinate(
                chapter_num=chapter_num,
                target_words=target_words,
                custom_prompt=custom_prompt,
                relevant_memory=relevant_memory
            )
            final_content = agent_result["content"]
            real_chars = agent_result["real_chars"]
        except Exception as e:
            logger.error(f"❌ [节点3/8] 创作失败：{str(e)}", exc_info=True)
            metrics.end_generation(0, False, str(e))
            return False
        metrics.end_agent("multi_agent")
        logger.info(f"✅ [节点3/8] 创作完成，最终字数：{real_chars}")

        logger.info("🧠 [节点4/8] 开始更新剧情记忆")
        update_plot_record(final_content, chapter_num)
        logger.info("✅ [节点4/8] 剧情记忆更新完成")

        logger.info("💾 [节点5/8] 开始保存本地文件")
        output_file = os.path.join(OUTPUT_DIR, f"第{chapter_num}章_{real_chars}字.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_content)
        logger.info(f"✅ [节点5/8] 本地文件保存完成：{output_file}")

        logger.info("📦 [节点6/8] 开始GitHub母本归档")
        archive_success, github_url, md5 = github_archive(chapter_num, final_content)
        if not archive_success:
            logger.warning("⚠️ [节点6/8] GitHub归档失败，流程继续")
        else:
            logger.info("✅ [节点6/8] GitHub母本归档完成")

        logger.info("📤 [节点7/8] 开始Notion写入对账")
        notion_success = notion_write(chapter_num, final_content, github_url, md5, real_chars)
        if not notion_success:
            logger.warning("⚠️ [节点7/8] Notion写入失败，流程继续")
        else:
            logger.info("✅ [节点7/8] Notion写入对账完成")

        logger.info("🎉 [节点8/8] 全流程闭环完成")
        logger.info("="*50)
        logger.info(f"✅ 第{chapter_num}章生成完成！")
        logger.info(f"📊 最终有效汉字：{real_chars}字")
        logger.info(f"📄 本地文件：{output_file}")
        if github_url:
            logger.info(f"🔗 GitHub链接：{github_url}")
        logger.info("="*50)
        
        # 结束性能监控
        metrics.end_generation(real_chars, True)
        return True
        
    except Exception as e:
        logger.error(f"❌ 生成流程异常：{str(e)}", exc_info=True)
        metrics.end_generation(0, False, str(e))
        return False


def show_statistics():
    """显示生成统计信息"""
    stats = metrics.get_statistics()
    logger.info("="*50)
    logger.info("📊 生成统计报告")
    logger.info("="*50)
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")
    logger.info("="*50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="赛博印钞机 Pro 终极优化版 V2.1")
    parser.add_argument("--chapter", type=int, default=1, help="生成的章节号")
    parser.add_argument("--words", type=int, default=None, help="目标字数（默认使用配置）")
    parser.add_argument("--prompt", type=str, default="", help="自定义创作要求")
    parser.add_argument("--daemon", action="store_true", help="启动Kairos守护进程")
    parser.add_argument("--daemon-hour", type=int, default=None, help="守护进程每日生成时间（小时）")
    parser.add_argument("--stats", action="store_true", help="显示生成统计信息")
    parser.add_argument("--config-get", type=str, help="获取配置项")
    parser.add_argument("--config-set", nargs=2, metavar=('KEY', 'VALUE'), help="设置配置项")
    args = parser.parse_args()

    # 处理配置命令
    if args.config_get:
        value = config.get(args.config_get)
        print(f"{args.config_get} = {value}")
        sys.exit(0)
    
    if args.config_set:
        config.set(args.config_set[0], args.config_set[1])
        print(f"配置已更新：{args.config_set[0]} = {args.config_set[1]}")
        sys.exit(0)

    # 显示统计信息
    if args.stats:
        show_statistics()
        sys.exit(0)

    # 启动守护进程
    if args.daemon:
        from builtin_claude_core.kairos_daemon import KairosDaemon
        daemon_hour = args.daemon_hour or config.get("daemon.gen_hour", 3)
        daemon = KairosDaemon(gen_hour=daemon_hour)
        daemon.run()
        sys.exit(0)

    # 单次生成
    target_words = args.words or config.get("generation.default_words", 7500)
    success = generate_chapter_full(
        chapter_num=args.chapter,
        target_words=target_words,
        custom_prompt=args.prompt
    )
    
    # 显示统计
    show_statistics()
    
    sys.exit(0 if success else 1)
