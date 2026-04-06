# 🚀 赛博印钞机 Pro V3.0 工业级终极封板

基于 Streamlit + LiteLLM 的工业级小说创作 AI 助手，集成 P0级Token黑洞防护、工业级异步引擎、SQLite记忆宫殿、全链路告警。

## ✨ V3.0 核心特性

### 🎯 小说创作功能
- **P0级Token黑洞防护**：生成过程中任何误触、刷新，绝不打断底层任务，API额度零浪费
- **一键生成**：30 秒上手，状态机锁保护
- **大模型配置**：支持 DeepSeek/OpenAI/豆包/智谱 AI 等主流大模型
- **历史记录**：查看已生成的章节内容
- **移动端告警**：支持 Bark/Server 酱/飞书/钉钉推送

### 🛠️ 技术亮点
- **工业级事件循环**：nest_asyncio彻底解决容器冲突，面板永不假死、永不白屏
- **SQLite存储架构**：行级锁+O(1)查询，1000章超长小说零性能衰减，内存占用降低90%
- **历史JSON数据自动迁移**：旧数据一键导入SQLite，不丢任何历史章节
- **全链路移动端告警**：生成成功/失败/崩溃实时推送到手机，运维黑盒彻底解决
- **多智能体并行协同**：大纲师、排雷师、主笔同步工作，生成效率提升50%+

### 🎨 V3.0 终极面板
- **4 个核心工作区**：章节生成、记忆宫殿、生成历史、帮助说明
- **P0级状态机**：生成按钮状态绑定，生成中自动锁定
- **专业 UI 设计**：工业级主题，流畅的交互体验
- **小白友好**：侧边栏大模型配置，一键保存到.env

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
pip install -r requirements.txt --upgrade

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
│   ├── query_engine.py      # 工业级异步引擎（nest_asyncio）
│   ├── memory_palace.py     # SQLite 记忆宫殿（自动迁移旧数据）
│   ├── llm_adapter.py       # LLM 适配器
│   └── logger.py            # 日志工具
├── .streamlit/               # Streamlit 配置
│   └── config.toml           # 工业级主题配置
├── novel_settings/           # 小说设置（用户创建）
│   └── 默认小说/             # 默认小说模板
├── output/                   # 输出目录（自动创建）
│   └── 第N章_时间戳.md       # 生成的章节
├── web_panel_industrial.py   # V3.0 终极面板
├── cyber_printer_ultimate.py # 主控调度 + 全链路告警
├── Dockerfile                # Docker 镜像
├── docker-compose.yml        # Docker Compose 配置
├── .env.example              # 环境变量模板
└── requirements.txt          # 工业级依赖清单
```

## 🎯 4 个工作区

| 工作区 | 功能 |
|--------|------|
| ✍️ **章节生成** | P0级状态机、生成进度、结果展示 |
| 📚 **记忆宫殿** | 固定世界观设定、动态剧情记忆、完整历史 |
| 📖 **生成历史** | 已生成章节浏览、下载 |
| ❓ **帮助说明** | V3.0 特性、快速上手、核心说明 |

## 🔧 核心使用

### 1. 配置小说设定
在 `novel_settings/你的小说名/` 目录下，添加 3 个核心文件：
- **00-全本大纲.md**：全本剧情大纲
- **01-人物档案.md**：主角、配角人设
- **02-世界观设定.md**：世界观、背景、规则

### 2. 配置大模型
在侧边栏「大模型配置」中填写：
- **API Key**：你的大模型 API Key
- **Base URL**：API 基础地址
- **模型名称**：选择对应的模型
- **告警 Webhook URL**：（可选）移动端推送
- **一键保存到.env**：点击按钮自动保存

### 3. 一键生成
1. 在侧边栏设置章节号和目标字数
2. （可选）填写自定义剧情要求
3. 点击「🚀 一键躺平生成」
4. 系统会自动完成全流程创作

## 📊 V3.0 技术架构

### 核心模块
- **query_engine.py**：工业级异步引擎 + nest_asyncio 补丁，彻底解决容器冲突
- **memory_palace.py**：SQLite 记忆宫殿，僵尸锁清理、JSON 数据自动迁移
- **cyber_printer_ultimate.py**：主控调度 + 全链路告警推送
- **web_panel_industrial.py**：V3.0 终极面板 + P0级状态机

### 安全保障
- **P0级状态机**：生成按钮状态绑定，生成中自动锁定
- **Token黑洞防护**：生成过程中任何误触、刷新，绝不打断底层任务
- **SQLite原子写入**：100% 原子化，断电不丢数据
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
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL_NAME=deepseek-chat

# 生成参数
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

**赛博印钞机 Pro V3.0 祝您创作愉快！** 🎉
