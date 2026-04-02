
# 赛博印钞机 Pro Ultra

一个功能强大的全自动小说生成桌面应用，基于 OpenClaw 构建。

## ✨ 核心功能

### 📖 小说生成
- **多种小说类型模板**：番茄爆款爽文、玄幻修仙、都市神医、科幻末世
- **实时编辑预览**：生成后可直接编辑和优化
- **批量生成**：支持一次生成多章，自动衔接剧情
- **灵活配置**：自定义字数、Agent、功能开关

### 🗂️ 多工作区支持
- 独立的工作区管理
- 项目隔离，互不干扰
- 轻松切换不同的创作项目

### 🤖 Agent 管理
- 查看和管理所有 Agent
- 模型配置编辑
- 技能挂载管理

### 🔧 系统设置
- 环境变量配置
- Gateway 控制（启动/停止）
- 消息渠道配置

### 🩺 系统诊断
- 全面的系统健康检查
- OpenClaw 状态检测
- 网络连接测试
- 资源使用监控
- 诊断报告导出

## 🚀 快速开始

### 前置要求
- macOS 系统
- Python 3.10+
- OpenClaw 已安装并配置好

### 一键启动

```bash
# 克隆或进入项目目录
cd OpenClaw_Arch_Ultra

# 双击运行或在终端执行
./start_ultra.command
```

### 手动启动

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建必要目录
mkdir -p logs workspaces/default configs

# 启动应用
python3 desktop_main_ultra.py
```

## 📂 项目结构

```
OpenClaw_Arch_Ultra/
├── core/                      # 核心模块
│   ├── __init__.py
│   ├── config_manager.py      # 配置管理
│   └── system_diagnostic.py   # 系统诊断
├── modules/                   # 功能模块（待添加）
├── configs/                   # 配置文件
├── workspaces/                # 工作区目录
│   └── default/              # 默认工作区
├── logs/                      # 日志文件
├── assets/                    # 资源文件
├── builtin_skills/           # 内置技能（从原项目复制）
├── novel_settings/           # 小说设定（从原项目复制）
├── web_panel_ultra.py       # 增强版 Web 面板
├── desktop_main_ultra.py    # 增强版桌面应用
├── requirements.txt          # 依赖列表
├── start_ultra.command      # 一键启动脚本
└── README_ULTRA.md          # 本文件
```

## 🎨 功能详解

### 小说类型模板

#### 番茄爆款爽文
- 仇不过夜，当场打脸
- 节奏紧凑，2000-2500字/章
- 绝对禁止出现内部标签

#### 玄幻修仙
- 升级打怪，宗门斗争
- 境界分明，3000-4000字/章
- 战斗描写精彩

#### 都市神医
- 医术超凡，扮猪吃虎
- 都市暧昧，2500-3000字/章
- 多位美女围绕

#### 科幻末世
- 末日求生，科技进化
- 人性考验，3000-3500字/章
- 求生细节到位

### 工作区管理

每个工作区都是独立的，可以：
- 创建不同的小说项目
- 独立的输出文件存储
- 互不干扰的配置

### 系统诊断功能

诊断检查包括：
- ✅ 系统信息（OS、CPU、内存）
- ✅ Python 环境
- ✅ OpenClaw 安装状态
- ✅ Gateway 运行状态
- ✅ 网络连接
- ✅ API 可达性
- ✅ 工作区状态
- ✅ 资源使用情况

## 🔧 配置说明

### 环境变量 (.env)

```env
# Notion配置（可选）
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id

# GitHub配置（可选）
GITHUB_TOKEN=your_github_token
GITHUB_REPO=username/repository

# 系统配置（可选）
SYSTEM_LOG_PATH=logs/system.log
GENERATE_SCRIPT_PATH=run_openclaw.sh
```

### OpenClaw 配置

确保你的 OpenClaw 已正确配置：
- agents.yaml 在 ~/.openclaw/ 目录
- config.yaml 在 ~/.openclaw/ 目录
- Gateway 可以正常启动

## 📝 使用指南

### 第一步：配置 OpenClaw

1. 确保 OpenClaw 已安装
2. 配置好你的 agents.yaml 和 config.yaml
3. 测试 Gateway 能否正常启动

### 第二步：启动应用

1. 双击 `start_ultra.command`
2. 首次启动会自动创建虚拟环境
3. 配置 .env 文件（可选）
4. 重启应用

### 第三步：开始创作

1. 选择小说类型模板
2. 配置生成参数
3. 点击「一键生成」
4. 在编辑预览中优化内容
5. 导出或保存到工作区

## 🤝 与原项目的关系

本项目是 OpenClaw_Arch 的增强版，保留了所有原有功能：
- 保留了原有的 run_openclaw.sh
- 保留了原有的小说设定
- 保留了原有的内置技能
- 增强了 UI/UX 体验
- 添加了更多实用功能

## 🐛 故障排除

### 应用无法启动

1. 检查 Python 版本是否 &gt;= 3.10
2. 查看 logs/ 目录下的日志
3. 确保端口 8502 未被占用

### OpenClaw 连接失败

1. 确认 OpenClaw 已正确安装
2. 检查 ~/.openclaw/ 目录是否存在
3. 尝试手动启动 Gateway：`openclaw gateway start`

### 生成失败

1. 检查 API Key 是否正确
2. 查看系统诊断报告
3. 确认网络连接正常

## 📄 许可证

本项目基于原 OpenClaw_Arch 项目开发。

## 🙏 致谢

- OpenClaw 团队
- 所有贡献者

---

**祝您创作愉快！** 🎉

