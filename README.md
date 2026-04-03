
# 🚀 赛博印钞机 Pro V2.3 | Cyber Printer Pro

基于 Claude Code 51.2万行泄露源码原生实现，工业级网文自动化创作全链路系统，让AI帮你稳定写完一本完整的网络小说。

## ✨ 核心功能

### V2.2 新增功能 🆕
- **launchd 守护进程**：使用 macOS 原生 launchd 服务，支持深度休眠唤醒、开机自启
- **Node.js 依赖管理**：自动检测并安装 Node.js 环境和依赖，支持 x-crawl 爬虫
- **文件锁系统**：解决并发读写冲突，保护记忆宫殿数据安全
- **执行权限锁死**：通过 Git 锁死 .command 文件执行权限，避免权限报错

### V2.1 功能
- **配置管理系统**：YAML/JSON 配置文件，统一管理所有设置，支持动态修改
- **性能监控模块**：实时统计生成速度、成功率、Agent 耗时，支持导出报告
- **智能配置命令**：命令行直接查看和修改配置，无需手动编辑文件
- **生成统计报告**：自动生成字数、速度、成功率等关键指标统计

### 原有核心功能
- **QueryEngine 推理引擎**：4.6 万行核心逻辑，负责意图解析、多 Agent 调度、上下文管理、记忆检索
- **多智能体协调系统**：Coordinator 指挥官模式，5 个专业 Agent 分工协作，流水线式创作
- **Undercover Mode 卧底模式**：从思维链底层规避 AI 写作特征，原生反 AI 检测，平台零拦截
- **结构化记忆系统**：三层上下文压缩机制，自动记录人设、剧情、伏笔，彻底解决吃书问题
- **Kairos 持久守护进程**：后台休眠运行，到点自动唤醒生成，零 CPU 占用，支持异常重启
- **多 LLM 后端支持**：统一适配器支持 OpenAI、Anthropic Claude、Ollama 本地模型，灵活切换
- **LLM 适配器系统**：统一接口封装多种 LLM 后端，自动重试、流式生成、错误处理
- **全链路自动化**：生成→去 AI 化→记忆更新→GitHub 归档→Notion 分发，全流程无人值守

## 🚀 快速开始

### 前置要求
- macOS 10.15+（支持 Intel/Apple Silicon）
- Python 3.10+
- LLM API 密钥（OpenAI/Anthropic）或本地 Ollama 模型
- Homebrew

### 一键启动
```bash
# 克隆仓库
git clone https://github.com/bgy8023/cyber-printer-pro.git
cd cyber-printer-pro

# 双击运行或在终端执行
./start_ultimate.command
```

### 手动启动
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装Node.js依赖
npm install

# 启动可视化面板
python3 -m streamlit run web_panel_ultra.py --server.port 8502
```

## 📂 项目结构

```
OpenClaw_Arch_Ultra/
├── builtin_claude_core/          # Claude源码核心能力实现
│   ├── __init__.py
│   ├── logger.py                  # 统一日志配置
│   ├── query_engine.py            # QueryEngine核心推理引擎
│   ├── kairos_daemon.py           # Kairos持久守护进程
│   ├── config_manager.py          # 配置管理模块
│   ├── metrics.py                 # 性能监控模块
│   └── file_lock.py               # 🆕 文件锁管理器
├── builtin_skills/                # 内置技能库
│   ├── undercover_mode/           # 卧底模式反AI检测
│   ├── novel_generator/           # 网文生成核心技能
│   ├── humanizer/                 # 去AI化润色技能
│   └── xcrawl_scraper/            # 全网素材抓取技能
├── novel_settings/                # 结构化记忆宫殿
├── output/                        # 生成的小说章节输出
├── logs/                          # 系统运行日志
│   └── metrics/                   # 性能指标数据
├── configs/                       # 配置文件目录
│   └── app_config.yaml            # 应用配置文件
├── .locks/                        # 🆕 文件锁目录
├── com.cyberprinter.daemon.plist  # 🆕 launchd 配置文件
├── install_daemon.sh              # 🆕 launchd 安装脚本
├── package.json                   # 🆕 Node.js 依赖配置
├── .env                           # 环境变量配置
├── .env.example                   # 环境变量配置模板
├── .gitignore                     # Git忽略文件
├── requirements.txt               # Python依赖清单
├── cyber_printer_ultimate.py      # 核心生成主脚本 (V2.2)
├── web_panel_ultra.py             # Streamlit可视化面板
├── start_ultimate.command         # Mac一键启动器
└── README.md                      # 本文档
```

## 🔧 环境配置

1. **复制环境配置模板**
   ```bash
   cp .env.example .env
   ```

2. **填写 LLM 配置（必填）**
   
   选择一种 LLM 后端配置：
   
   **方案 A：OpenAI（推荐）**
   ```bash
   LLM_PROVIDER=openai
   OPENAI_API_KEY="your-openai-api-key"
   OPENAI_MODEL=gpt-4
   # 可选：使用第三方代理
   # OPENAI_BASE_URL="https://api.openai.com/v1"
   ```
   
   **方案 B：Anthropic Claude**
   ```bash
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY="your-anthropic-api-key"
   ANTHROPIC_MODEL=claude-3-sonnet-20240229
   ```
   
   **方案 C：本地 Ollama（完全免费，需要 GPU）**
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama2
   ```
   
3. **填写其他配置**
   - `NOTION_TOKEN`：Notion API Token
   - `NOTION_DATABASE_ID`：Notion 数据库 ID
   - `GITHUB_TOKEN`：GitHub Personal Access Token
   - `GITHUB_REPO`：GitHub 仓库地址

## 🎯 功能使用

### 1. 可视化面板
- 访问 http://localhost:8502
- 选择章节号、目标字数、Agent
- 开启所需功能（多智能体模式、Undercover模式等）
- 点击「一键躺平生成」

### 2. 命令行生成
```bash
# 生成第1章，7500字
python cyber_printer_ultimate.py --chapter 1 --words 7500 --prompt "废土修仙打脸爽文"

# 使用配置的默认字数生成
python cyber_printer_ultimate.py --chapter 1 --prompt "废土修仙打脸爽文"
```

### 3. 🆕 自动日更守护进程（launchd 版）

```bash
# 安装 launchd 守护进程（推荐）
./install_daemon.sh install

# 查看守护进程状态
./install_daemon.sh status

# 卸载守护进程
./install_daemon.sh uninstall
```

**守护进程特性：**
- ✅ 每天凌晨 3:00 自动生成
- ✅ 支持 macOS 深度休眠唤醒
- ✅ 开机自启，异常重启
- ✅ 详细日志记录

### 4. 配置管理

```bash
# 查看配置
python cyber_printer_ultimate.py --config-get generation.default_words
# 输出: generation.default_words = 7500

# 修改配置
python cyber_printer_ultimate.py --config-set generation.default_words 8000
# 输出: 配置已更新：generation.default_words = 8000

# 查看所有可用配置项
python cyber_printer_ultimate.py --config-get agents
```

**可配置项说明：**
- `generation.default_words`：默认生成字数 (1000-20000)
- `generation.max_retry`：最大重试次数
- `generation.timeout`：生成超时时间（秒）
- `agents.outline_agent.enabled`：大纲 Agent 开关
- `agents.writer_agent.timeout`：主笔 Agent 超时时间
- `undercover_mode.enabled`：卧底模式开关
- `undercover_mode.strictness`：严格程度 (low/medium/high)
- `memory.auto_update`：自动更新剧情记忆
- `daemon.gen_hour`：守护进程生成时间（小时）

### 5. 性能统计

```bash
# 查看生成统计报告
python cyber_printer_ultimate.py --stats
```

**统计报告包含：**
- 总章节数
- 成功章节数
- 成功率
- 总字数
- 总耗时
- 平均速度（字/秒）
- 平均每章字数

性能指标数据保存在 `logs/metrics/generation_metrics.jsonl`

## 🔒 安全规范

- 绝对不要把 `.env` 文件提交到 Git 仓库
- Notion/GitHub Token 只授予最小必要权限
- 定期轮换 API Token，避免泄露风险
- 守护进程不要用 root 权限运行

## 📊 更新日志

### V2.2 (2026-04-02) - 架构师补丁版
- ✅ 修复 Kairos 守护进程 - 使用 launchd 替换死循环，支持深度休眠唤醒
- ✅ 修复 Node.js 幽灵依赖 - 自动检测安装 Node.js 和 x-crawl 依赖
- ✅ 修复并发读写灾难 - 新增文件锁系统，保护记忆宫殿数据
- ✅ 修复 .command 权限裸奔 - Git 锁死执行权限，避免权限报错
- ✅ 新增 launchd 安装脚本，一键管理守护进程
- ✅ 新增 package.json 配置，规范 Node.js 依赖

### V2.1 (2026-04-02)
- ✅ 新增配置管理模块，支持 YAML/JSON 配置文件
- ✅ 新增性能监控模块，实时统计生成指标
- ✅ 新增命令行配置管理功能
- ✅ 新增生成统计报告功能
- ✅ 优化 cyber_printer_ultimate.py，集成新模块
- ✅ 优化项目结构，新增 configs/ 和 logs/metrics/ 目录

### V2.0 (2026-04-02)
- ✅ 初始版本发布
- ✅ QueryEngine 核心推理引擎
- ✅ 多智能体协调系统
- ✅ Undercover Mode 卧底模式
- ✅ Kairos 持久守护进程

## 📄 许可证

本项目基于 Claude Code 泄露源码和 OpenClaw 项目开发。

## 🙏 致谢

- Claude Code 泄露源码
- OpenClaw 团队
- Trae IDE

---

**祝您创作愉快！** 🎉
