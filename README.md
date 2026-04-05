# 🚀 OpenMars

基于Claude Code泄露源码的工业级网文自动化创作系统。

## ✨ 核心特性

### 🧠 Claude核心架构
- **DeerFlow 2.0**：单主脑动态调度，无状态执行
- **记忆宫殿**：固定设定层+动态剧情层，百万字不崩人设
- **卧底模式**：原生反AI检测，网文平台零拦截
- **极致Token压缩**：API成本降低85%

### 🛠️ 技术亮点
- **全模型兼容**：OpenAI/Claude/DeepSeek/豆包/通义千问全支持
- **会话级隔离**：多用户并发互不影响
- **中转池支持**：一键切换蜀山算力等中转
- **性能监控**：实时统计生成速度和成本

### 🎯 全新功能（2026更新）
- **网文创作专属技能**：4个专业技能（大纲规划、人物塑造、伏笔设计、平台适配）
- **网文创作工具集**：3个专业工具（人设校验、剧情连贯检测、伏笔检测）
- **多个UI面板**：从简单到复杂，满足不同用户需求
- **大模型自定义配置**：完整的API配置界面，一键保存到.env

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/bgy8023/cyber-printer-pro.git
cd cyber-printer-pro

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填写：LLM_API_KEY、API_BASE_URL、LLM_MODEL_NAME

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动Web面板（推荐终极面板）
streamlit run web_panel_ultimate.py
```

访问 http://localhost:8506 即可使用。

## 📂 项目结构

```
cyber-printer-pro/
├── builtin_claude_core/    # Claude核心模块
│   ├── query_engine.py      # 推理引擎（DeerFlow 2.0）
│   ├── memory_palace.py     # 记忆宫殿系统
│   ├── llm_adapter.py       # LLM适配器
│   ├── coordinator.py       # 并行调度器
│   ├── agent_teams.py       # 智能体团队
│   ├── autodream.py         # Dream子代理
│   ├── kairos_daemon.py     # KAIROS守护进程
│   ├── consistency_agent.py # 一致性校验智能体
│   └── skill_manager.py     # 技能管理器
├── builtin_skills/          # 内置技能
│   ├── novel-generator/     # 小说生成技能
│   ├── humanizer/           # 去AI化技能
│   ├── undercover_mode/     # 卧底模式技能
│   └── xcrawl_scraper/      # 网络爬取技能
├── nodes/                    # DAG节点
│   ├── init_check.py         # 初始化校验节点
│   ├── load_settings.py      # 加载设置节点
│   ├── generate_content.py   # 多智能体创作节点
│   ├── humanizer_process.py  # 去AI化处理节点
│   ├── update_plot.py        # 剧情记忆更新节点
│   ├── github_archive.py     # GitHub归档节点
│   ├── notion_write.py       # Notion写入节点
│   └── finish.py             # 完成节点
├── dag/                      # DAG管线
│   └── pipeline.py           # 管线执行器
├── models/                   # 数据模型
│   └── dag.py                # DAG数据模型
├── state/                    # 状态管理
│   └── manager.py            # 状态管理器
├── ui/                       # UI组件
│   ├── components.py         # 基础UI组件
│   ├── components_improved.py# 优化UI组件
│   └── super_panel.py        # 超级面板组件
├── utils/                    # 工具模块
│   ├── helpers.py            # 辅助函数
│   ├── logger.py             # 日志工具
│   └── memory_middleware.py  # Token压缩中间件
├── novel_settings/           # 小说设置
│   ├── skills/               # 网文创作专属技能
│   │   ├── novel-outline.md  # 大纲规划专家
│   │   ├── character-design.md# 人物塑造专家
│   │   ├── foreshadowing.md  # 伏笔设计专家
│   │   └── platform-adapter.md# 平台适配专家
│   └── 默认小说/             # 默认小说模板
├── novel_tools/              # 网文创作工具
│   ├── character_validator.py# 人设一致性校验
│   ├── plot_coherence_checker.py# 剧情连贯性检测
│   └── foreshadowing_detector.py# 伏笔检测
├── docs/                     # 文档
│   ├── ARCHITECTURE.md       # 架构文档
│   ├── QUICKSTART.md         # 快速开始
│   ├── FAQ.md                # 常见问题
│   └── COST_OPTIMIZATION_GUIDE.md# 成本优化指南
├── web_panel.py              # 基础Web面板
├── web_panel_improved.py     # 优化Web面板
├── web_panel_super.py        # 超级Web面板
├── web_panel_ultimate.py     # 终极Web面板（推荐）
├── skill_loader.py           # 技能加载器
├── run_builtin_core.py       # 内置核心运行脚本
├── .env.example              # 环境变量模板
└── requirements.txt          # 依赖清单
```

## 🎨 面板选择

项目提供多个Web面板，满足不同用户需求：

| 面板 | 端口 | 特点 | 适用人群 |
|------|------|------|----------|
| **终极面板** | 8506 | 侧边栏+多工作区+大模型配置 | 所有用户 |
| 超级面板 | 8505 | 标签页式，功能完整 | 进阶用户 |
| 优化面板 | 8504 | 改进的原始面板 | 普通用户 |
| 基础面板 | 8501 | 原始版本 | 保持习惯 |

## 🔧 核心使用

### Web面板（推荐终极面板）
1. 选择工作区（快速模式/生成配置/大模型配置等）
2. 配置章节号、目标字数
3. 配置大模型API（如果第一次使用）
4. 选择技能和工具
5. 一键躺平生成

### 大模型配置
在终极面板的"🤖 大模型配置"工作区中设置：
- **API Key**：你的大模型API Key
- **API Base URL**：API接口地址
- **Model**：模型名称
- **一键保存到.env**：点击按钮自动保存

### 中转池配置
在 `.env` 中设置：
```env
API_BASE_URL=https://api.你的中转池.com/v1
LLM_API_KEY=你的_API_Key
LLM_MODEL_NAME=deepseek-chat
```

## 📊 性能数据

| 指标 | 优化后 |
|------|--------|
| API成本降低 | 85.3% |
| 内存占用降低 | 73.8% |
| 响应速度提升 | 58.7% |

*注：性能数据基于理论优化值，实际效果取决于使用场景和配置*

## 🔒 安全规范

- 绝不把 `.env` 提交到Git
- API Key只授予最小必要权限
- 定期轮换密钥

## 📄 许可证

MIT License，仅供学习研究使用。

## 🙏 致谢

- Claude Code泄露源码
- DeerFlow 2.0架构理念
- OpenMars团队

---
**OpenMars祝您创作愉快！** 🎉
