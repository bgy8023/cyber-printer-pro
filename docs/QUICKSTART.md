# 快速入门指南

## 前置要求

- macOS 10.15+（支持 Intel/Apple Silicon）
- Python 3.10+
- Homebrew（macOS 推荐）

## 30秒快速上手

### 1. 克隆项目

```bash
git clone https://github.com/bgy8023/cyber-printer-pro.git
cd cyber-printer-pro
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填写你的大模型配置
# 至少需要填写：LLM_API_KEY、LLM_BASE_URL、LLM_MODEL_NAME
```

### 3. 一键启动

```bash
# 双击运行或在终端执行
./start_ultimate.command
```

启动后访问 http://localhost:8502 即可使用可视化面板。

## 详细配置说明

### 大模型配置

支持所有符合 OpenAI 标准的大模型：

```env
# OpenAI 官方
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-openai-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o

# Anthropic Claude
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-your-claude-key
LLM_BASE_URL=https://api.anthropic.com/v1
LLM_MODEL_NAME=claude-3-5-sonnet-20241022

# DeepSeek
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-deepseek-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL_NAME=deepseek-chat

# 字节豆包
LLM_PROVIDER=openai
LLM_API_KEY=your-doubao-key
LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
LLM_MODEL_NAME=doubao-pro-32k

# 本地 Ollama
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=llama3
```

### 可选功能配置

```env
# Notion 自动分发
NOTION_TOKEN=your-notion-token
NOTION_DATABASE_ID=your-database-id

# GitHub 自动归档
GITHUB_TOKEN=your-github-token
GITHUB_REPO=username/repo-name

# 守护进程配置
DAEMON_GEN_HOUR=3
DAEMON_CHAPTERS_PER_DAY=1
DAEMON_DEFAULT_WORDS=7500

# 功能开关
UNDERCOVER_MODE_ENABLED=true
UNDERCOVER_MODE_STRICTNESS=medium
MEMORY_AUTO_UPDATE=true
```

## 使用方法

### 可视化面板

1. 访问 http://localhost:8502
2. 在侧边栏配置大模型
3. 选择章节号、目标字数、写作风格
4. 开启/关闭多智能体模式、卧底模式、记忆系统
5. 点击「一键躺平生成」

### 命令行使用

```bash
# 生成第1章，7500字
python cyber_printer_ultimate.py --chapter 1 --words 7500

# 查看所有配置项
python cyber_printer_ultimate.py --config-get all

# 修改默认生成字数
python cyber_printer_ultimate.py --config-set generation.default_words 8000

# 查看生成统计报告
python cyber_printer_ultimate.py --stats
```

### 全自动日更守护进程

```bash
# 安装守护进程
./install_daemon.sh install

# 查看守护进程状态
./install_daemon.sh status

# 卸载守护进程
./install_daemon.sh uninstall
```

## 常见问题排查

### Python 版本过低

```bash
# 升级 Python
brew upgrade python3
```

### 依赖安装失败

```bash
# 手动安装依赖
pip install -r requirements.txt
```

### 大模型连接失败

1. 检查 API Key 是否正确
2. 检查 Base URL 是否正确
3. 检查网络连接
4. 尝试更换模型

### 端口被占用

```bash
# 修改启动脚本中的端口号
# 编辑 start_ultimate.command，修改 PORT 变量
```

## 下一步

- 阅读 [README.md](../README.md) 了解完整功能
- 查看 [FAQ.md](./FAQ.md) 了解常见问题
- 探索 [ARCHITECTURE.md](./ARCHITECTURE.md) 了解系统架构
