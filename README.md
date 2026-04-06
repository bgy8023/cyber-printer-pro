# 🚀 OpenMars

基于 Streamlit + LiteLLM 的工业级小说创作 AI 助手，提供简洁稳定的 Web 面板、大模型配置、小说生成和历史记录功能。

## ✨ 核心特性

### 🎯 小说创作功能
- **一键生成**：简洁的界面，30 秒上手
- **大模型配置**：支持 DeepSeek/OpenAI/豆包/智谱 AI 等主流大模型
- **参数预设**：创意写作/平衡模式/精准回答三种预设，小白也能用
- **历史记录**：查看已生成的章节内容
- **移动端告警**：支持 Bark/Server 酱/飞书/钉钉推送

### 🛠️ 技术亮点
- **全模型兼容**：LiteLLM 统一接口，支持所有主流大模型
- **SQLite 记忆宫殿**：工业级存储，零膨胀，毫秒级查询
- **原子化写入**：TempFile + os.replace，断电不丢数据
- **同步/异步桥接**：nest_asyncio，面板永不假死
- **Docker 容器化**：一键部署，环境隔离

### 🎨 工业级 Web 面板
- **5 个精简工作区**：AI 助手、快速模式、大模型配置、历史记录、系统设置
- **专业 UI 设计**：工业级主题，流畅的交互体验
- **小白友好**：预设服务商选择，一键保存配置

## 🚀 快速开始

### 方式一：本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/bgy8023/cyber-printer-pro.git
cd cyber-printer-pro

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填写：LLM_API_KEY、API_BASE_URL、LLM_MODEL_NAME

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动 Web 面板
streamlit run web_panel_industrial.py --server.port 8501
```

访问 http://localhost:8501 即可使用。

### 方式二：Docker 部署

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

访问 http://localhost:8501 即可使用。

## 📂 项目结构

```
cyber-printer-pro/
├── builtin_claude_core/    # 核心模块
│   ├── query_engine.py      # 推理引擎（同步/异步桥接）
│   ├── memory_palace.py     # SQLite 记忆宫殿
│   ├── llm_adapter.py       # LLM 适配器
│   └── logger.py            # 日志工具
├── .streamlit/               # Streamlit 配置
│   └── config.toml           # 工业级主题配置
├── novel_settings/           # 小说设置（用户创建）
│   └── 默认小说/             # 默认小说模板
├── output/                   # 输出目录（自动创建）
│   └── 第N章_时间戳.md       # 生成的章节
├── web_panel_industrial.py   # 工业级 Web 面板
├── cyber_printer_ultimate.py # 主控调度脚本
├── Dockerfile                # Docker 镜像
├── docker-compose.yml        # Docker Compose 配置
├── .env.example              # 环境变量模板
└── requirements.txt          # 依赖清单
```

## 🎯 5 个工作区

| 工作区 | 功能 |
|--------|------|
| 💬 **AI 助手** | 对话管理、小说命令、自然语言理解 |
| ⚡ **快速模式** | 30 秒上手、小说配置、一键生成 |
| 🤖 **大模型配置** | API 设置、参数预设、一键保存 |
| 📜 **历史记录** | 已生成章节浏览 |
| 🔧 **系统设置** | 系统信息、文件检查 |

## 🔧 核心使用

### 1. 大模型配置
在"🤖 大模型配置"工作区中设置：
- **选择服务商**：DeepSeek（推荐）/ OpenAI / 豆包 / 智谱 AI / 自定义
- **API Key**：你的大模型 API Key
- **选择模型**：根据服务商选择对应的模型
- **参数预设**：创意写作/平衡模式/精准回答
- **一键保存到 .env**：点击按钮自动保存

### 2. 快速生成小说
在"⚡ 快速模式"工作区中：
1. 设置章节号和目标字数
2. 选择目标平台、小说类型、写作风格
3. （可选）填写自定义指令
4. 点击"🔥 一键躺平生成"

### 3. AI 助手命令
在"💬 AI 助手"工作区中可用：
- `/help` - 显示帮助
- `/status` - 查看项目状态
- `/clear` - 清空对话历史
- `/novel list` - 列出小说章节
- `/novel chapter N` - 设置章节号
- `/novel words N` - 设置目标字数
- `/novel generate` - 生成当前章节
- 自然语言："生成第 5 章"、"写 10000 字"

## 📊 技术架构

### 核心模块
- **query_engine.py**：同步/异步桥接，nest_asyncio 保证事件循环稳定
- **memory_palace.py**：SQLite 记忆宫殿，自动迁移旧 JSON 数据
- **llm_adapter.py**：LiteLLM 统一接口，兼容所有主流大模型
- **cyber_printer_ultimate.py**：主控调度，全链路告警推送

### 安全保障
- **状态隔离**：Web 面板任何误触、刷新，绝不打断底层生成任务
- **原子写入**：100% 原子化，断电不丢数据
- **环境隔离**：.env 文件本地配置，绝不提交到 Git

## 📱 移动端告警配置

在 `.env` 中添加：
```env
# Bark iOS 极客首选
WEBHOOK_URL=https://api.day.app/你的BarkToken

# Server 酱 全平台通用
# WEBHOOK_URL=https://sctapi.ftqq.com/你的SendKey.send

# 飞书/钉钉 自定义机器人
# WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
```

## 🎨 环境变量说明

在 `.env` 中配置：
```env
# 大模型配置
LLM_PROVIDER=DeepSeek
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
API_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL_NAME=deepseek-chat

# 生成参数
LLM_TEMPERATURE=0.7
LLM_TOP_P=0.9
LLM_MAX_TOKENS=15000
MAX_RETRY=3

# 移动端告警（可选）
WEBHOOK_URL=
```

## 🔒 安全规范

- 绝不把 `.env` 提交到 Git（已在 .gitignore 中）
- API Key 只授予最小必要权限
- 定期轮换密钥

## 📄 许可证

MIT License，仅供学习研究使用。

## 🙏 致谢

- Streamlit（⭐38.7k Stars）
- LiteLLM 统一接口
- OpenClaw 自主 AI Agent 理念

---

**OpenMars 祝您创作愉快！** 🎉
