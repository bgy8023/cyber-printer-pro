#!/usr/bin/env python3
"""
测试全自动连载功能
"""
import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from builtin_claude_core.query_engine import ClaudeQueryEngine
from builtin_claude_core.memory_palace import get_memory_palace

def test_serial_functionality():
    """测试全自动连载功能"""
    print("=" * 50)
    print("🧪 测试全自动连载功能")
    print("=" * 50)
    
    # 检查是否有大纲文件
    outline_file = os.path.join("novel_settings", "0_全本大纲.md")
    if not os.path.exists(outline_file):
        print(f"❌ 大纲文件不存在：{outline_file}")
        return False
    
    print("✅ 大纲文件存在")
    
    # 读取大纲内容
    with open(outline_file, "r", encoding="utf-8") as f:
        outline_content = f.read()
    
    print(f"📝 大纲内容长度：{len(outline_content)} 字符")
    
    # 创建连载设置
    serial_settings = {
        "start_chapter": 1,
        "end_chapter": 2,  # 测试生成2章
        "target_words": 1000,  # 测试用，字数较少
        "enable_schedule": False,
        "schedule_hour": None
    }
    
    # 保存连载设置
    settings_file = os.path.join("novel_settings", "0_连载设置.json")
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(serial_settings, f, ensure_ascii=False, indent=2)
    
    print("✅ 连载设置已保存")
    
    # 初始化引擎
    try:
        query_engine = ClaudeQueryEngine()
        memory_palace = get_memory_palace()
        print("✅ 引擎初始化完成")
        
    except Exception as e:
        print(f"❌ 引擎初始化失败：{str(e)}")
        return False
    
    # 测试章节生成
    try:
        current_chapter = serial_settings.get("start_chapter", 1)
        end_chapter = serial_settings.get("end_chapter", 2)
        target_words = serial_settings.get("target_words", 1000)
        
        print(f"\n🚀 开始生成章节 {current_chapter} 到 {end_chapter}")
        
        for chapter_num in range(current_chapter, end_chapter + 1):
            print(f"\n🔄 正在生成第{chapter_num}章...")
            
            # 构建章节生成提示词
            chapter_prompt = f"""
基于以下大纲，生成网络小说第{chapter_num}章的完整正文。
要求：
1. 字数要求：{target_words}字
2. 严格贴合大纲，保持剧情连贯
3. 保持人物设定和世界观的一致性
4. 包含适当的冲突和悬念
5. 只输出正文，不要任何解释或标题

{outline_content}
            """
            
            # 调用 Claude 核心生成章节
            agent_result = query_engine.multi_agent_coordinate(
                chapter_num=chapter_num,
                target_words=target_words,
                custom_prompt=chapter_prompt,
                chapter_outline="",
                chapter_name=f"第{chapter_num}章"
            )
            
            final_content = agent_result["content"]
            real_chars = agent_result["real_chars"]
            
            # 保存章节内容
            output_file = os.path.join("output", f"第{chapter_num}章_{real_chars}字_{datetime.now().strftime('%Y%m%d%H%M')}.md")
            os.makedirs("output", exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(final_content)
            
            # 更新记忆宫殿
            memory_palace.add_chapter(chapter_num, f"第{chapter_num}章", final_content)
            memory_palace.save_to_disk()
            
            print(f"✅ 第{chapter_num}章生成完成，字数：{real_chars}字")
            print(f"📄 保存到：{output_file}")
        
        # 验证章节文件是否生成
        output_files = os.listdir("output")
        chapter_files = [f for f in output_files if f.startswith("第") and f.endswith(".md")]
        
        print(f"\n📊 生成结果：")
        print(f"生成的章节文件数量：{len(chapter_files)}")
        for file in chapter_files:
            print(f"  - {file}")
        
        if len(chapter_files) >= end_chapter:
            print("\n🎉 测试成功！全自动连载功能正常工作")
            return True
        else:
            print("\n❌ 测试失败：章节文件生成不足")
            return False
            
    except Exception as e:
        print(f"\n❌ 章节生成失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_serial_functionality()
    sys.exit(0 if success else 1)
