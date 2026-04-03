#!/usr/bin/env python3
"""
测试所有改进：
1. 硬约束一致性检查器
2. humanize_text 重构
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from builtin_claude_core.consistency_checker import (
    HardRuleConsistencyChecker,
    ConsistencyCheckResult
)

def test_consistency_checker():
    """测试硬约束一致性检查器"""
    print("=" * 60)
    print("测试 1: 硬约束一致性检查器")
    print("=" * 60)
    
    checker = HardRuleConsistencyChecker()
    
    # 测试 1.1: 基本功能
    print("\n[测试 1.1] 基本功能测试...")
    result = checker.check("这是一段普通文本")
    print(f"  普通文本检查结果: passed={result.passed}")
    assert result.passed, "普通文本应该通过检查"
    
    # 测试 1.2: 添加核心人物并测试
    print("\n[测试 1.2] 核心人物消失检测...")
    checker.required_keywords = ["张三", "李四"]
    content_without_zhangsan = "这是一段只有李四的文本"
    result = checker.check(content_without_zhangsan)
    print(f"  缺少张三的检查结果: passed={result.passed}")
    print(f"  失败项: {result.failed_items}")
    assert not result.passed, "缺少核心人物应该失败"
    
    # 测试 1.3: 所有核心人物都在
    print("\n[测试 1.3] 所有核心人物都存在...")
    content_with_all = "张三和李四一起去冒险"
    result = checker.check(content_with_all)
    print(f"  所有核心人物存在的检查结果: passed={result.passed}")
    assert result.passed, "所有核心人物存在应该通过"
    
    print("\n✅ 一致性检查器测试通过！")


def test_file_integrity():
    """测试文件完整性"""
    print("\n" + "=" * 60)
    print("测试 2: 文件完整性检查")
    print("=" * 60)
    
    # 检查关键文件是否存在
    files_to_check = [
        ".gitignore",
        "builtin_claude_core/query_engine.py",
        "builtin_claude_core/consistency_checker.py",
        ".git/hooks/pre-commit"
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
        test_consistency_checker()
        test_file_integrity()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
