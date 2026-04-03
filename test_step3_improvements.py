#!/usr/bin/env python3
"""
测试第三步的所有改进：
1. AutoDream 梦游机制
2. Coordinator 并行多 Agent
3. Skills 技能系统
4. 终极生成流程集成
"""

import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from builtin_claude_core.autodream import AutoDream, get_autodream
from builtin_claude_core.coordinator import Coordinator
from builtin_claude_core.skill_manager import SkillManager, WritingSkill, skill_manager
from builtin_claude_core.memory_palace_simple import SimpleMemoryPalace


def test_autodream():
    """测试 AutoDream 梦游机制"""
    print("=" * 60)
    print("测试 1: AutoDream 梦游机制")
    print("=" * 60)
    
    test_novel = "测试小说_梦游"
    test_dir = os.path.join("novel_settings", test_novel)
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    print("\n[测试 1.1] 初始化 AutoDream...")
    dream = AutoDream(test_novel)
    assert dream is not None
    assert dream.novel_name == test_novel
    assert os.path.exists(test_dir)
    print("  ✅ 初始化成功")
    
    print("\n[测试 1.2] 创建测试记忆文件...")
    outline_file = os.path.join(test_dir, "00-全本大纲.md")
    character_file = os.path.join(test_dir, "01-人物档案.md")
    with open(outline_file, "w", encoding="utf-8") as f:
        f.write("这是一本测试小说的大纲，讲述了主角的冒险故事。")
    with open(character_file, "w", encoding="utf-8") as f:
        f.write("主角：张三 - 勇敢的冒险家\n反派：李四 - 邪恶的Boss")
    
    # 重新初始化以加载新文件
    dream = AutoDream(test_novel)
    print("  ✅ 测试文件创建成功")
    
    print("\n[测试 1.3] 更新几章动态记忆...")
    dream.memory.update_chapter_memory(1, "第一章：主角出发", 2000)
    dream.memory.update_chapter_memory(2, "第二章：遇到反派", 2500)
    print("  ✅ 动态记忆更新成功")
    
    print("\n[测试 1.4] 执行梦游巩固...")
    result = dream.consolidate()
    assert result is True
    print("  ✅ 梦游巩固成功")
    
    shutil.rmtree(test_dir)
    print("\n✅ AutoDream 梦游机制测试通过！")


def test_coordinator():
    """测试 Coordinator 并行多 Agent"""
    print("\n" + "=" * 60)
    print("测试 2: Coordinator 并行多 Agent")
    print("=" * 60)
    
    print("\n[测试 2.1] 初始化 Coordinator...")
    coord = Coordinator()
    assert coord is not None
    print("  ✅ 初始化成功")
    
    print("\n[测试 2.2] 执行并行设计...")
    result = coord.parallel_design("测试大纲", "测试上下文")
    assert result is not None
    assert "爽点设计" in result
    assert "开头钩子" in result
    assert "节奏规划" in result
    assert "人物对话风格" in result
    print("  ✅ 并行设计完成")
    
    print("\n✅ Coordinator 并行多 Agent 测试通过！")


def test_skill_manager():
    """测试 Skills 技能系统"""
    print("\n" + "=" * 60)
    print("测试 3: Skills 技能系统")
    print("=" * 60)
    
    print("\n[测试 3.1] 初始化 SkillManager...")
    manager = SkillManager()
    assert manager is not None
    assert manager.current_skill == WritingSkill.TOMATO
    print("  ✅ 初始化成功，默认技能：番茄爆款")
    
    print("\n[测试 3.2] 获取番茄爆款提示词...")
    prompt = manager.get_prompt()
    assert "节奏快" in prompt
    assert "爽点密" in prompt
    print(f"  ✅ 提示词: {prompt[:30]}...")
    
    print("\n[测试 3.3] 切换到起点男频...")
    manager.set_skill(WritingSkill.QIDIAN)
    assert manager.current_skill == WritingSkill.QIDIAN
    prompt = manager.get_prompt()
    assert "宏大世界观" in prompt
    print("  ✅ 切换成功")
    
    print("\n[测试 3.4] 测试所有技能...")
    skills = [WritingSkill.SWEET, WritingSkill.SUSPENSE, WritingSkill.TOMATO]
    for skill in skills:
        manager.set_skill(skill)
        prompt = manager.get_prompt()
        assert prompt != ""
        print(f"  ✅ {skill.value} 技能正常")
    
    print("\n✅ Skills 技能系统测试通过！")


def test_file_integrity():
    """测试文件完整性"""
    print("\n" + "=" * 60)
    print("测试 4: 文件完整性检查")
    print("=" * 60)
    
    files_to_check = [
        "builtin_claude_core/autodream.py",
        "builtin_claude_core/coordinator.py",
        "builtin_claude_core/skill_manager.py",
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
        test_autodream()
        test_coordinator()
        test_skill_manager()
        test_file_integrity()
        
        print("\n" + "=" * 60)
        print("🎉 所有第三步测试通过！")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
