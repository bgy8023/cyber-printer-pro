#!/usr/bin/env python3
"""
测试 humanize_text 方法修复
"""

from rust_dispatcher import get_dispatcher

print("=== 测试 humanize_text 方法修复 ===")

try:
    # 初始化 dispatcher
    print("1. 初始化 RustCoreDispatcher...")
    dispatcher = get_dispatcher()
    print("✅ RustCoreDispatcher 初始化成功")
    
    # 测试 humanize_text 方法
    print("\n2. 测试 humanize_text 方法...")
    test_text = "这是一段测试文本，测试 humanize_text 方法是否正常工作。"
    result = dispatcher.humanize_text(test_text)
    print("✅ humanize_text 方法调用成功")
    print(f"输入: {test_text}")
    print(f"输出: {result}")
    
    print("\n🎉 修复成功！humanize_text 方法现在可以正常工作了。")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
