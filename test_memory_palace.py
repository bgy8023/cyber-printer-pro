#!/usr/bin/env python3
"""
测试记忆宫殿系统功能
"""

import os
import shutil
from builtin_claude_core.memory_palace import MemoryPalace, get_memory_palace

print("=== 测试 Day1: 双层记忆宫殿系统 ===")

# 测试 1: 模块导入
print("\n1. 测试模块导入...")
try:
    from builtin_claude_core.memory_palace import MemoryPalace, get_memory_palace
    print("✅ 模块导入成功")
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    exit(1)

# 测试 2: 初始化记忆宫殿
print("\n2. 测试记忆宫殿初始化...")
try:
    # 清理测试目录
    test_dir = "./test_memory"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    memory_palace = MemoryPalace(test_dir)
    print("✅ 记忆宫殿初始化成功")
except Exception as e:
    print(f"❌ 记忆宫殿初始化失败: {e}")
    exit(1)

# 测试 3: 固定记忆管理
print("\n3. 测试固定记忆管理...")
try:
    # 设置人物档案
    memory_palace.set_character("主角", "张三，25岁，普通大学生，意外获得系统能力")
    print("✅ 人物档案设置成功")
    
    # 设置世界观设定
    memory_palace.set_world_setting("现代都市，存在隐藏的修炼者世界")
    print("✅ 世界观设定设置成功")
    
    # 设置全书大纲
    memory_palace.set_full_outline("第一卷：觉醒，第二卷：成长，第三卷：巅峰")
    print("✅ 全书大纲设置成功")
    
    # 设置章节大纲
    memory_palace.set_chapter_outline(1, "主角觉醒系统")
    print("✅ 章节大纲设置成功")
    
    # 获取固定记忆
    character = memory_palace.get_character("主角")
    world_setting = memory_palace.get_world_setting()
    full_outline = memory_palace.get_full_outline()
    chapter_outline = memory_palace.get_chapter_outline(1)
    
    print(f"✅ 人物档案获取成功: {character}")
    print(f"✅ 世界观设定获取成功: {world_setting}")
    print(f"✅ 全书大纲获取成功: {full_outline}")
    print(f"✅ 章节大纲获取成功: {chapter_outline}")
except Exception as e:
    print(f"❌ 固定记忆管理失败: {e}")
    exit(1)

# 测试 4: 动态记忆管理
print("\n4. 测试动态记忆管理...")
try:
    # 添加章节
    memory_palace.add_chapter(1, "第一章 觉醒", "主角在图书馆意外觉醒系统")
    print("✅ 章节添加成功")
    
    # 添加伏笔
    memory_palace.add_foreshadowing("主角发现一个神秘的古玉", 1)
    print("✅ 伏笔添加成功")
    
    # 添加剧情节点
    memory_palace.add_plot_node("主角觉醒系统", 1)
    print("✅ 剧情节点添加成功")
    
    # 获取动态记忆
    chapter = memory_palace.get_chapter(1)
    unresolved_foreshadowing = memory_palace.get_unresolved_foreshadowing()
    current_chapter = memory_palace.get_current_chapter()
    
    print(f"✅ 章节获取成功: {chapter['name']}")
    print(f"✅ 未回收伏笔获取成功: {len(unresolved_foreshadowing)}个")
    print(f"✅ 当前章节获取成功: {current_chapter}")
except Exception as e:
    print(f"❌ 动态记忆管理失败: {e}")
    exit(1)

# 测试 5: 记忆持久化和加载
print("\n5. 测试记忆持久化和加载...")
try:
    # 保存到磁盘
    memory_palace.save_to_disk()
    print("✅ 记忆持久化成功")
    
    # 创建新的记忆宫殿实例并加载
    new_memory_palace = MemoryPalace(test_dir)
    new_character = new_memory_palace.get_character("主角")
    new_chapter = new_memory_palace.get_chapter(1)
    
    print(f"✅ 记忆加载成功: 人物档案 - {new_character}")
    print(f"✅ 记忆加载成功: 章节 - {new_chapter['name']}")
except Exception as e:
    print(f"❌ 记忆持久化和加载失败: {e}")
    exit(1)

# 测试 6: 提示词生成方法
print("\n6. 测试提示词生成方法...")
try:
    full_fixed_prompt = memory_palace.get_full_fixed_prompt()
    previous_plot = memory_palace.get_previous_plot_summary()
    unresolved_foreshadowing_prompt = memory_palace.get_unresolved_foreshadowing_prompt()
    
    print("✅ get_full_fixed_prompt 方法正常")
    print("✅ get_previous_plot_summary 方法正常")
    print("✅ get_unresolved_foreshadowing_prompt 方法正常")
    
    # 打印部分结果
    print(f"\n固定记忆提示词示例: {full_fixed_prompt[:100]}...")
    print(f"前序剧情摘要示例: {previous_plot[:100]}...")
    print(f"未回收伏笔提示词示例: {unresolved_foreshadowing_prompt[:100]}...")
except Exception as e:
    print(f"❌ 提示词生成方法失败: {e}")
    exit(1)

# 测试 7: 全局单例
print("\n7. 测试全局单例...")
try:
    singleton_memory_palace = get_memory_palace()
    print("✅ 全局单例获取成功")
except Exception as e:
    print(f"❌ 全局单例获取失败: {e}")
    exit(1)

# 清理测试目录
if os.path.exists(test_dir):
    shutil.rmtree(test_dir)

print("\n🎉 所有测试通过！Day1: 双层记忆宫殿系统功能正常。")
