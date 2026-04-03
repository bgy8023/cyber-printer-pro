#!/usr/bin/env python3
"""
测试大纲生成功能
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from builtin_claude_core.query_engine import ClaudeQueryEngine
from builtin_claude_core.memory_palace import get_memory_palace

def test_outline_generation():
    """测试大纲生成功能"""
    print("=" * 50)
    print("🧪 测试大纲生成功能")
    print("=" * 50)
    
    # 读取设定文件
    setting_file = os.path.join("novel_settings", "0_5问设定.md")
    if not os.path.exists(setting_file):
        print(f"❌ 设定文件不存在：{setting_file}")
        return False
    
    with open(setting_file, "r", encoding="utf-8") as f:
        setting_content = f.read()
    
    print("✅ 已读取设定文件")
    print(f"📝 设定内容长度：{len(setting_content)} 字符")
    
    # 构建大纲生成提示词
    outline_prompt = f"""
你是专业的网文大纲师，基于以下设定，生成一本完整的小说大纲。
要求：
1. 大纲要包含：全书概览、主要人物、世界观设定、详细的章节列表
2. 章节列表要包含：章节号、章节标题、章节内容简介
3. 章节数量要合理，根据目标字数来安排
4. 大纲要结构清晰，逻辑连贯，符合网文创作规律

{setting_content}
    """
    
    print("\n🤖 正在调用 ClaudeQueryEngine 生成大纲...")
    
    try:
        # 初始化引擎
        query_engine = ClaudeQueryEngine()
        print("✅ ClaudeQueryEngine 初始化完成")
        
        # 生成大纲
        outline_content = query_engine._call_agent("大纲Agent", outline_prompt)
        print(f"✅ 大纲生成完成，长度：{len(outline_content)} 字符")
        
        # 保存大纲到文件
        outline_file = os.path.join("novel_settings", "0_全本大纲.md")
        with open(outline_file, "w", encoding="utf-8") as f:
            f.write(outline_content)
        print(f"✅ 大纲已保存到：{outline_file}")
        
        # 保存到记忆宫殿
        memory_palace = get_memory_palace()
        memory_palace.set_full_outline(outline_content)
        memory_palace.save_to_disk()
        print("✅ 大纲已保存到记忆宫殿")
        
        # 显示大纲前500字符
        print("\n" + "=" * 50)
        print("📋 大纲预览（前500字符）：")
        print("=" * 50)
        print(outline_content[:500])
        print("...")
        
        print("\n" + "=" * 50)
        print("🎉 大纲生成测试成功！")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ 大纲生成失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_outline_generation()
    sys.exit(0 if success else 1)
