# 🚀 快速开始指南 - 赛博印钞机 Pro

## 最简单的方式（推荐）

### 方式 1：用 Web 面板（最推荐）

在终端中运行：
```bash
cd /Users/mars/cyber-printer-pro
streamlit run web_panel_ultimate.py
```

然后浏览器会自动打开（或打开显示的地址，通常是 http://localhost:8501）

---

### 方式 2：用 OpenHarness 对话

在终端中运行：
```bash
cd /Users/mars/cyber-printer-pro
./start_openharness.sh
```

或者复制粘贴下面这一行：
```bash
export OPENHARNESS_API_FORMAT=openai && export OPENHARNESS_BASE_URL=https://api.deepseek.com/v1 && export OPENAI_API_KEY=sk-455b11f8c9ef45538722b390f542ee45 && export OPENHARNESS_MODEL=deepseek-chat && /usr/local/bin/python3.13 -m openharness
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `.env` | 配置文件（已填好 API Key） |
| `web_panel_ultimate.py` | Web 面板主程序 |
| `start_openharness.sh` | OpenHarness 启动脚本 |
| `START_HERE.md` | 本文档 |

---

## 就这么简单！

推荐先用 **方式 1（Web 面板）**，最直观易用！
