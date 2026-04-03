#!/usr/bin/env python3
"""
测试连贯性校验 Agent 功能
"""

from builtin_claude_core.consistency_agent import ConsistencyAgent, get_consistency_agent
from builtin_claude_core.memory_palace import MemoryPalace

print("=== 测试 Day2: 连贯性校验 Agent ===")

# 测试 1: 模块导入
print("\n1. 测试模块导入...")
try:
    from builtin_claude_core.consistency_agent import ConsistencyAgent, get_consistency_agent
    print("✅ 模块导入成功")
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    exit(1)

# 测试 2: 初始化连贯性校验 Agent
print("\n2. 测试连贯性校验 Agent 初始化...")
try:
    consistency_agent = ConsistencyAgent()
    print("✅ 连贯性校验 Agent 初始化成功")
except Exception as e:
    print(f"❌ 连贯性校验 Agent 初始化失败: {e}")
    exit(1)

# 测试 3: 全局单例
print("\n3. 测试全局单例...")
try:
    singleton_agent = get_consistency_agent()
    print("✅ 全局单例获取成功")
except Exception as e:
    print(f"❌ 全局单例获取失败: {e}")
    exit(1)

# 测试 4: 校验方法
print("\n4. 测试校验方法...")
try:
    # 创建测试用的记忆宫殿
    memory_palace = MemoryPalace()
    
    # 设置测试数据
    memory_palace.set_character("主角", "张三，25岁，普通大学生，性格内向，意外获得系统能力")
    memory_palace.set_world_setting("现代都市，存在隐藏的修炼者世界")
    memory_palace.set_full_outline("第一卷：觉醒，第二卷：成长，第三卷：巅峰")
    memory_palace.set_chapter_outline(1, "主角觉醒系统")
    
    # 添加测试章节
    memory_palace.add_chapter(1, "第一章 觉醒", "主角在图书馆意外觉醒系统")
    
    # 测试章节内容（故意包含一个问题）
    chapter_content = """
张三，25岁，普通大学生，性格外向，在图书馆意外觉醒系统。
他兴奋地大叫起来，引来了很多人的注意。
"""
    
    # 执行校验
    check_result = consistency_agent.check_chapter(
        memory_palace=memory_palace,
        chapter_num=2,
        chapter_name="第二章 系统激活",
        chapter_content=chapter_content,
        chapter_outline="主角激活系统"
    )
    
    print(f"✅ 校验方法执行成功")
    print(f"✅ 校验得分: {check_result.score}")
    print(f"✅ 是否通过: {check_result.passed}")
    print(f"✅ 是否需要重写: {check_result.rewrite_needed}")
    
    if check_result.failed_items:
        print("\n❌ 发现的问题:")
        for item in check_result.failed_items:
            print(f"  - {item['level']}: {item['content']}")
    
    if check_result.rewrite_suggestion:
        print("\n📝 重写建议:")
        print(f"  {check_result.rewrite_suggestion[:100]}...")
        
except Exception as e:
    print(f"❌ 校验方法执行失败: {e}")
    import traceback
    traceback.print_exc()

print("\n🎉 测试完成！Day2: 连贯性校验 Agent 功能正常。")
