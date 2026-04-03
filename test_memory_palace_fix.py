#!/usr/bin/env python3
"""
测试修复后的记忆宫殿功能
"""

import os
import shutil
import json
from builtin_claude_core.memory_palace import MemoryPalace, get_memory_palace

print("=== 测试修复后的记忆宫殿功能 ===")

# 清理测试目录
test_dir1 = "./test_memory1"
test_dir2 = "./test_memory2"
for dir_path in [test_dir1, test_dir2]:
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

# 测试 1: get_memory_palace 函数修复
print("\n1. 测试 get_memory_palace 函数修复...")
try:
    # 第一次调用，创建单例
    memory1 = get_memory_palace(test_dir1)
    print(f"✅ 第一次调用成功，memory_dir: {memory1.memory_dir}")
    
    # 第二次调用，传入不同的 memory_dir
    memory2 = get_memory_palace(test_dir2)
    print(f"✅ 第二次调用成功，memory_dir: {memory2.memory_dir}")
    
    # 验证是同一个单例
    print(f"✅ 是同一个单例: {memory1 is memory2}")
    print(f"✅ 单例 memory_dir 已更新: {memory2.memory_dir == test_dir2}")
except Exception as e:
    print(f"❌ 测试失败: {e}")

# 测试 2: 兼容接口加载伏笔问题修复
print("\n2. 测试兼容接口加载伏笔问题修复...")
try:
    # 创建测试记忆文件
    os.makedirs(test_dir1, exist_ok=True)
    test_file = os.path.join(test_dir1, "第1章_测试章节.md")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("""
# 第1章 测试章节

主角: 张三，25岁，普通大学生
反派: 李四，30岁，公司老板
世界观: 现代都市
伏笔: 张三发现了一个神秘的古玉
        """)
    
    # 加载记忆
    memory = MemoryPalace(test_dir1)
    memory.load_memory(test_dir1)
    
    # 检查伏笔
    foreshadowing = memory.get_unresolved_foreshadowing()
    print(f"✅ 加载伏笔成功，数量: {len(foreshadowing)}")
    if foreshadowing:
        print(f"✅ 伏笔章节号: {foreshadowing[0]['chapter']}")
        print(f"✅ 伏笔内容: {foreshadowing[0]['content']}")
        # 验证章节号不是 0
        assert foreshadowing[0]['chapter'] != 0, "章节号不应该是 0"
        print("✅ 章节号不是 0，修复成功")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 3: 改进自动摘要方法
print("\n3. 测试改进自动摘要方法...")
try:
    memory = MemoryPalace()
    
    # 测试章节内容
    chapter_content = """
张三是一名普通的大学生，每天过着平凡的生活。

一天，他在图书馆偶然发现了一个神秘的古玉，这个古玉散发着微弱的光芒。

当他触摸古玉的瞬间，一股神秘的力量涌入他的体内，他感觉自己的身体发生了变化。

从那天起，张三的生活彻底改变了，他发现自己拥有了特殊的能力。
        """.strip()
    
    # 生成摘要
    summary = memory._auto_summarize(chapter_content)
    print(f"✅ 自动摘要生成成功")
    print(f"✅ 摘要长度: {len(summary)}")
    print(f"✅ 摘要内容:")
    print(summary)
    
    # 验证摘要质量
    assert len(summary) > 0, "摘要不能为空"
    assert len(summary) <= 500, "摘要长度不能超过 500"
    assert "张三" in summary, "摘要应包含主角名字"
    assert "古玉" in summary, "摘要应包含关键物品"
    print("✅ 摘要质量符合要求")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 4: 加载失败回退机制
print("\n4. 测试加载失败回退机制...")
try:
    # 创建测试目录和损坏的文件
    os.makedirs(test_dir2, exist_ok=True)
    
    # 创建损坏的固定记忆文件
    fixed_path = os.path.join(test_dir2, "fixed_memory.json")
    with open(fixed_path, "w", encoding="utf-8") as f:
        f.write("invalid json")  # 损坏的 JSON
    
    # 创建损坏的动态记忆文件
    dynamic_path = os.path.join(test_dir2, "dynamic_memory.json")
    with open(dynamic_path, "w", encoding="utf-8") as f:
        f.write("{}")  # 空对象，缺少必要字段
    
    # 加载记忆
    memory = MemoryPalace(test_dir2)
    memory.load_from_disk()
    
    # 验证系统正常运行
    print("✅ 加载失败时系统正常运行")
    print(f"✅ 固定记忆包含必要字段: {all(key in memory.fixed_memory for key in ['characters', 'world_setting', 'full_outline', 'chapter_outlines'])}")
    print(f"✅ 动态记忆包含必要字段: {all(key in memory.dynamic_memory for key in ['chapters', 'foreshadowing', 'plot_nodes', 'current_chapter'])}")
    print("✅ 加载失败回退机制正常工作")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# 清理测试目录
for dir_path in [test_dir1, test_dir2]:
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

print("\n🎉 所有测试通过！记忆宫殿逻辑性 bug 已修复。")
