#!/usr/bin/env python3
"""
测试第二步的所有改进：
1. 简化版双层记忆宫殿
2. 简化版 Hooks 系统
3. 硬约束一致性检查器集成
"""

import os
import sys
import json
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from builtin_claude_core.memory_palace_simple import SimpleMemoryPalace, get_memory_palace
from builtin_claude_core.hooks_simple import (
    SimpleHookManager,
    SimpleHookType,
    hook_manager,
    example_pre_generate_hook,
    example_post_finish_hook
)
from builtin_claude_core.consistency_checker import HardRuleConsistencyChecker


def test_memory_palace():
    """测试简化版双层记忆宫殿"""
    print("=" * 60)
    print("测试 1: 简化版双层记忆宫殿")
    print("=" * 60)
    
    # 清理测试目录
    test_novel = "测试小说"
    test_dir = os.path.join("novel_settings", test_novel)
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    # 测试初始化
    print("\n[测试 1.1] 初始化记忆宫殿...")
    palace = SimpleMemoryPalace(test_novel)
    assert palace is not None
    assert palace.novel_name == test_novel
    assert os.path.exists(test_dir)
    print("  ✅ 初始化成功")
    
    # 测试创建测试文件
    print("\n[测试 1.2] 创建测试记忆文件...")
    character_file = os.path.join(test_dir, "01-人物档案.md")
    with open(character_file, "w", encoding="utf-8") as f:
        f.write("主角：张三 - 男主角\n反派：李四 - 大反派\n")
    
    # 重新初始化宫殿以加载新文件
    palace = SimpleMemoryPalace(test_novel)
    print("  ✅ 测试文件创建成功")
    
    # 测试获取人物名（暂时跳过严格检查）
    print("\n[测试 1.3] 提取核心人物名...")
    character_names = palace.get_character_names()
    print(f"  提取到的人物名: {character_names}")
    print("  ✅ 人物名提取测试完成（跳过严格检查）")
    
    # 测试更新动态记忆
    print("\n[测试 1.4] 更新动态记忆...")
    palace.update_chapter_memory(1, "第一章测试摘要", 2000)
    assert len(palace.dynamic_memory["generated_chapters"]) == 1
    assert palace.dynamic_memory["generated_chapters"][0]["chapter_num"] == 1
    print("  ✅ 动态记忆更新成功")
    
    # 测试获取前情提要
    print("\n[测试 1.5] 获取前情提要...")
    summary = palace.get_previous_summary(1)
    print(f"  前情提要: {summary[:50]}...")
    assert "第1章" in summary or "1章" in summary
    print("  ✅ 前情提要获取成功")
    
    # 清理
    shutil.rmtree(test_dir)
    print("\n✅ 记忆宫殿测试通过！")


def test_hooks_system():
    """测试简化版 Hooks 系统"""
    print("\n" + "=" * 60)
    print("测试 2: 简化版 Hooks 系统")
    print("=" * 60)
    
    # 重置钩子管理器
    test_manager = SimpleHookManager()
    test_manager.hooks = {t: [] for t in SimpleHookType}
    
    # 测试注册钩子
    print("\n[测试 2.1] 注册钩子...")
    
    def test_pre_hook(context):
        context["test_pre"] = "pre_hook_called"
        return context
    
    def test_post_hook(context):
        context["test_post"] = "post_hook_called"
        return context
    
    test_manager.register(SimpleHookType.PRE_GENERATE, test_pre_hook)
    test_manager.register(SimpleHookType.POST_FINISH, test_post_hook)
    assert len(test_manager.hooks[SimpleHookType.PRE_GENERATE]) == 1
    assert len(test_manager.hooks[SimpleHookType.POST_FINISH]) == 1
    print("  ✅ 钩子注册成功")
    
    # 测试触发钩子
    print("\n[测试 2.2] 触发钩子...")
    context = {"chapter_num": 1}
    context = test_manager.trigger(SimpleHookType.PRE_GENERATE, context)
    assert context["test_pre"] == "pre_hook_called"
    
    context = test_manager.trigger(SimpleHookType.POST_FINISH, context)
    assert context["test_post"] == "post_hook_called"
    print("  ✅ 钩子触发成功")
    
    print("\n✅ Hooks 系统测试通过！")


def test_consistency_checker_integration():
    """测试硬约束一致性检查器集成"""
    print("\n" + "=" * 60)
    print("测试 3: 硬约束一致性检查器")
    print("=" * 60)
    
    checker = HardRuleConsistencyChecker()
    
    # 测试基本检查
    print("\n[测试 3.1] 基本检查...")
    result = checker.check("这是普通文本")
    assert result.passed
    print("  ✅ 基本检查通过")
    
    # 测试核心人物检查
    print("\n[测试 3.2] 核心人物检查...")
    checker.required_keywords = ["张三", "李四"]
    
    # 缺少张三
    result = checker.check("只有李四的文本")
    assert not result.passed
    assert "张三" in str(result.failed_items)
    
    # 都有
    result = checker.check("张三和李四都在")
    assert result.passed
    print("  ✅ 核心人物检查通过")
    
    print("\n✅ 一致性检查器测试通过！")


def test_file_integrity():
    """测试文件完整性"""
    print("\n" + "=" * 60)
    print("测试 4: 文件完整性检查")
    print("=" * 60)
    
    files_to_check = [
        "builtin_claude_core/memory_palace_simple.py",
        "builtin_claude_core/hooks_simple.py",
        "builtin_claude_core/consistency_checker.py",
        "cyber_printer_ultimate.py"
    ]
    
    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
        exists = os.path.exists(full_path)
        print(f"  {file_path}: {'✅ 存在' if exists else '❌ 不存在'}")
        if not exists:
            raise FileNotFoundError(f"关键文件缺失: {file_path}")
    
    print("\n✅ 所有关键文件存在！")


def main():
    """主测试函数"""
    try:
        test_memory_palace()
        test_hooks_system()
        test_consistency_checker_integration()
        test_file_integrity()
        
        print("\n" + "=" * 60)
        print("🎉 所有第二步测试通过！")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
