# Changelog

## [2.3.0] - 2025-01-15
### Added
- 基于 LiteLLM 实现全量大模型支持（100+ 模型）
- 新增 AsyncQueryEngine 异步推理引擎
- 新增 Session 级完全隔离机制
- 新增 SimpleMemoryPalace 原子级记忆宫殿
- 新增 FileLockManager 跨进程文件锁
- 新增 MetricsCollector 性能监控系统
- 新增 HardRuleConsistencyChecker 硬约束校验
- 新增 Coordinator 并行多Agent协调器
- 新增 AutoDream 梦游记忆巩固
- 新增 KairosDaemon 持久守护进程
- 新增 Streamlit 可视化面板（web_panel_ultra.py）
- 新增一键启动脚本（start_ultimate.command）
- 新增环境变量配置模板（.env.example）

### Fixed
- 修复了记忆宫殿并发读写问题
- 修复了大模型调用重试机制
- 修复了配置文件管理
- 修复了日志系统

### Improved
- 优化了项目结构
- 统一了文档和注释
- 完善了错误处理机制
- 增强了安全性

## [2.2.0] - 2024-12-20
### Added
- 初始版本发布
- 基础网文生成功能
- 基础记忆系统
