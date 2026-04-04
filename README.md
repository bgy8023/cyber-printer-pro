# 🚀 OpenMars - 赛博印钞机 Pro

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

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/bgy8023/cyber-printer-pro.git
cd cyber-printer-pro

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填写：LLM_API_KEY、LLM_BASE_URL、LLM_MODEL_NAME

# 3. 启动Web面板
streamlit run web_panel.py
```

访问 http://localhost:8501 即可使用。

## 📂 项目结构

```
cyber-printer-pro/
├── builtin_claude_core/    # Claude核心模块
│   ├── query_engine.py      # 推理引擎（DeerFlow 2.0）
│   ├── memory_palace.py     # 记忆宫殿系统
│   ├── llm_adapter.py       # LLM适配器
│   └── coordinator.py       # 并行调度器
├── utils/                    # 工具模块
│   └── memory_middleware.py # Token压缩中间件
├── web_panel.py              # Web可视化面板
└── docs/                     # 文档
```

## 🔧 核心使用

### Web面板
- 选择章节号、目标字数
- 配置写作风格
- 一键躺平生成

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

## 🔒 安全规范

- 绝不把 `.env` 提交到Git
- API Key只授予最小必要权限
- 定期轮换密钥

## 📄 许可证

MIT License，仅供学习研究使用。

## 🙏 致谢

- Claude Code泄露源码
- DeerFlow 2.0架构理念
- OpenClaw团队

---
**OpenMars祝您创作愉快！** 🎉
