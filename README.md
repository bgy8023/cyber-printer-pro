
# 赛博印钞机 Pro 终极优化版

基于 Claude Code 51.2 万行泄露源码原生实现，结合 Trae 双引擎，打造工业级网文自动化创作全链路系统。

## ✨ 核心功能

- **QueryEngine 推理引擎**：4.6 万行核心逻辑，负责意图解析、多 Agent 调度、上下文管理、记忆检索
- **多智能体协调系统**：Coordinator 指挥官模式，5 个专业 Agent 分工协作，流水线式创作
- **Undercover Mode 卧底模式**：从思维链底层规避 AI 写作特征，原生反 AI 检测，平台零拦截
- **结构化记忆系统**：三层上下文压缩机制，自动记录人设、剧情、伏笔，彻底解决吃书问题
- **Kairos 持久守护进程**：后台休眠运行，到点自动唤醒生成，零 CPU 占用，支持异常重启
- **Trae 双引擎对接**：无缝对接 Trae 的多模型能力、MCP 工具链，支持 Notion/GitHub/ 全网搜索
- **全链路自动化**：生成→去 AI 化→记忆更新→GitHub 归档→Notion 分发，全流程无人值守

## 🚀 快速开始

### 前置要求
- macOS 10.15+（支持 Intel/Apple Silicon）
- Python 3.10+
- Trae IDE 最新版
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
│   └── kairos_daemon.py           # Kairos持久守护进程
├── builtin_skills/                # 内置技能库
│   ├── undercover_mode/           # 卧底模式反AI检测
│   ├── novel_generator/           # 网文生成核心技能
│   ├── humanizer/                 # 去AI化润色技能
│   └── xcrawl_scraper/            # 全网素材抓取技能
├── novel_settings/                # 结构化记忆宫殿
├── output/                        # 生成的小说章节输出
├── logs/                          # 系统运行日志
├── .env                           # 环境变量配置
├── .gitignore                     # Git忽略文件
├── requirements.txt               # Python依赖清单
├── cyber_printer_ultimate.py      # 核心生成主脚本
├── web_panel_ultra.py             # Streamlit可视化面板
├── start_ultimate.command         # Mac一键启动器
└── README.md                      # 本文档
```

## 🔧 环境配置

1. **复制环境配置模板**
   ```bash
   cp .env.example .env
   ```

2. **填写配置**
   - `TRAE_API_KEY`：Trae IDE API Key
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
```

### 3. 自动日更守护进程
```bash
# 每天凌晨3点自动生成
python cyber_printer_ultimate.py --daemon --daemon-hour 3
```

## 🔒 安全规范

- 绝对不要把 `.env` 文件提交到 Git 仓库
- Notion/GitHub Token 只授予最小必要权限
- 定期轮换 API Token，避免泄露风险
- 守护进程不要用 root 权限运行

## 📄 许可证

本项目基于 Claude Code 泄露源码和 OpenClaw 项目开发。

## 🙏 致谢

- Claude Code 泄露源码
- OpenClaw 团队
- Trae IDE

---

**祝您创作愉快！** 🎉
