# 🚀 赛博印钞机 Pro V2.3 | Cyber Printer Pro
## 基于网传 Claude Code v2.1 51.2万行泄露源码 原生复刻 | Agentic Loop & Context Pruning 核心架构
工业级网文自动化创作全链路系统，让AI帮你稳定写完一本完整的网络小说，彻底解决AI写网文「吃书、人设崩塌、平台检测、并发阻塞」四大行业死穴。

---

## ⚡ 核心黑科技
### 🧠 原生复刻Claude核心架构
- **QueryEngine 原生推理引擎**：基于Claude泄露源码4.6万行核心逻辑原生重构，意图解析、多Agent调度、上下文管理、记忆检索全链路原生实现
- **Coordinator 指挥官并行模式**：5个专业Agent流水线+并行设计，爽点/节奏/钩子/对话同时生成，效率翻倍
- **Context Pruning 三层记忆宫殿**：固定设定层+动态剧情层+AutoDream梦游巩固层，彻底解决AI写网文「吃书」痛点，百万字长篇也不崩人设
- **Undercover Mode 卧底模式**：从思维链底层规避AI写作特征，原生反AI检测，网文平台零拦截

### 🤖 工业级高可用架构
- **全模型兼容**：基于LiteLLM实现，一行代码支持100+大模型，OpenAI/Claude/DeepSeek/豆包/通义千问/本地开源模型全兼容
- **会话级完全隔离**：Streamlit多用户并发场景下，每个用户独立引擎实例，一个用户限流绝不影响其他人，彻底解决并发阻塞死穴
- **原子级数据安全**：跨进程文件锁+临时文件原子写入，Web面板和后台守护进程同时写入也不会出现脏数据、文件损坏
- **Kairos 持久守护进程**：macOS原生launchd实现，支持深度休眠唤醒、开机自启、异常重启，设定一次全自动日更完本

### 🛡️ 企业级安全与体验
- **前置配置校验**：鲁棒的配置校验，无效配置直接可视化提示，绝不让用户踩坑
- **全链路自动化**：生成→去AI化→记忆更新→GitHub归档→Notion分发，全程零人工干预
- **敏感信息三重防护**：Git预提交钩子+强化.gitignore+配置隔离，密钥永不泄露
- **性能监控全链路**：实时统计生成速度、成功率、Agent耗时，支持导出详细报告

---

## 🚀 30秒快速上手
### 前置要求
- macOS 10.15+（支持 Intel/Apple Silicon，Linux 兼容）
- Python 3.10+
- Homebrew（macOS 推荐）

### 一键启动
```bash
# 1. 克隆仓库
git clone https://github.com/bgy8023/cyber-printer-pro.git
cd cyber-printer-pro

# 2. 复制配置模板
cp .env.example .env
# 编辑 .env 填写3个核心配置：LLM_API_KEY、LLM_BASE_URL、LLM_MODEL_NAME

# 3. 双击运行 或 终端执行一键启动脚本
./start_ultimate.command
```

启动后访问 http://localhost:8502 即可使用可视化面板，一键躺平生成。

## 📂 项目结构
```
cyber-printer-pro/
├── builtin_claude_core/          # Claude Code 核心能力原生实现
│   ├── __init__.py                # 模块导出
│   ├── query_engine.py            # 异步推理引擎，会话级隔离
│   ├── kairos_daemon.py           # Kairos 持久守护进程
│   ├── memory_palace_simple.py    # 原子级双层记忆宫殿
│   ├── autodream.py               # AutoDream 梦游记忆巩固
│   ├── coordinator.py             # 并行多Agent协调器
│   ├── skill_manager.py           # 写作技能系统
│   ├── consistency_checker.py     # 代码级硬约束校验
│   ├── config_manager.py          # 配置管理模块
│   ├── metrics.py                 # 性能监控模块
│   └── logger.py                  # 统一日志配置
├── builtin_skills/                # 内置技能库
│   ├── undercover_mode/           # 卧底模式反AI检测
│   ├── novel_generator/           # 网文生成核心技能
│   ├── humanizer/                 # 去AI化润色技能
│   └── xcrawl_scraper/            # 全网素材抓取技能
├── novel_settings/                # 结构化记忆宫殿目录
│   ├── 默认小说/                   # 小说项目独立记忆目录
│   └── 番茄爆款写作心法/          # 默认写作模板
├── configs/                       # 配置文件目录
├── output/                        # 生成的小说章节输出
├── logs/                          # 系统运行日志
├── .locks/                        # 文件锁目录
├── docs/                          # 文档目录
│   ├── QUICKSTART.md              # 快速入门教程
│   └── FAQ.md                      # 常见问题
├── web_panel_ultra.py             # Streamlit 可视化面板
├── cyber_printer_ultimate.py      # 核心生成主脚本
├── start_ultimate.command         # Mac 一键启动器
├── install_daemon.sh              # launchd 守护进程安装脚本
├── validate_install.sh            # 环境一键校验脚本
├── com.cyberprinter.daemon.plist # launchd 守护进程配置
├── requirements.txt               # Python 依赖清单
├── package.json                   # Node.js 依赖配置
├── .env.example                   # 环境变量模板
├── CHANGELOG.md                   # 版本更新日志
├── LICENSE                        # 开源许可证
└── README.md                      # 本文档
```

## 🔧 核心使用方法

### 1. 可视化面板
启动后访问 http://localhost:8502
选择章节号、目标字数、写作风格
开启 / 关闭多智能体模式、卧底模式、记忆系统
点击「一键躺平生成」，等待完成即可

### 2. 命令行生成
```bash
# 生成第1章，7500字，番茄爆款风格
python cyber_printer_ultimate.py --chapter 1 --words 7500 --prompt "废土修仙打脸爽文"

# 查看所有配置项
python cyber_printer_ultimate.py --config-get all

# 修改默认生成字数
python cyber_printer_ultimate.py --config-set generation.default_words 8000

# 查看生成统计报告
python cyber_printer_ultimate.py --stats
```

### 3. 全自动日更守护进程
```bash
# 安装 launchd 守护进程（推荐）
./install_daemon.sh install

# 查看守护进程状态
./install_daemon.sh status

# 卸载守护进程
./install_daemon.sh uninstall
```

## 🔒 安全规范
- 绝对不要把 .env 文件提交到 Git 仓库，项目已内置三重防护拦截
- 大模型 API Key 只授予最小必要权限，定期轮换
- Notion/GitHub Token 只授予最小必要权限
- 守护进程不要用 root 权限运行

## 📄 许可证
本项目基于 MIT 许可证开源，仅供学习研究使用。

## 🙏 致谢
- Claude Code 51.2 万行泄露源码
- OpenClaw 团队
- LiteLLM 开源项目

祝您创作愉快！🎉
