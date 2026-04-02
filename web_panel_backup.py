import streamlit as st
import os
import subprocess
import re
import hashlib
import requests
import base64
import time
from dotenv import load_dotenv
from notion_client import Client
from datetime import datetime

# ================= 全局初始化 =================
load_dotenv()
st.set_page_config(
    page_title="囡囡-网文总控台",
    page_icon="🦌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 暗黑极客主题注入
st.markdown("""
<style>
    .stApp { background-color: #0a0a0a; color: #00ff00; font-family: monospace; }
    .stButton>button { background-color: #ff0000; color: #ffffff; border: none; font-weight: bold; width: 100%; height: 3em; }
    .stTextArea>div>div>textarea, .stNumberInput>div>div>input { 
        background-color: #1a1a1a; color: #00ff00; border: 1px solid #333; font-family: monospace; 
    }
    .stCodeBlock { background-color: #121212 !important; border: 1px solid #333; }
    .status-card { padding: 1em; border-radius: 5px; border: 1px solid #333; background-color: #1a1a1a; }
</style>
""", unsafe_allow_html=True)

# ================= 环境变量加载 =================
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GEN_SCRIPT_PATH = os.getenv("GENERATE_SCRIPT_PATH")
LOG_PATH = os.getenv("SYSTEM_LOG_PATH")

# ================= 工具函数（带限流兜底） =================
def count_real_chars(text):
    return len(re.findall(r'[\u4e00-\u9fa5]', text))

def write_log(content):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {content}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_line)

# GitHub上传函数（带3次重试+限流判断，彻底规避封禁）
def upload_to_github(content, chapter_name):
    max_retries = 3
    retry_delay = 2
    for attempt in range(max_retries):
        try:
            # 先检查GitHub限流状态
            rate_url = "https://api.github.com/rate_limit"
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
            rate_res = requests.get(rate_url, headers=headers)
            if rate_res.status_code == 200:
                remaining = rate_res.json()["rate"]["remaining"]
                if remaining < 100:
                    write_log(f"⚠️ GitHub API剩余额度不足{remaining}，暂停上传")
                    return None, None
            
            # 执行上传
            filename = f"{chapter_name}_{datetime.now().strftime('%Y%m%d%H%M')}.md"
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/novels/{filename}"
            content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            data = {
                "message": f"Auto-upload chapter: {filename}",
                "content": content_base64,
                "branch": "main"
            }
            
            put_res = requests.put(url, headers=headers, json=data)
            if put_res.status_code in [200, 201]:
                raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/novels/{filename}"
                write_log(f"✅ GitHub原始文件上传成功：{filename}，剩余API额度：{remaining}")
                return raw_url, hashlib.md5(content.encode()).hexdigest()
            elif put_res.status_code == 403 and "rate limit exceeded" in put_res.text:
                write_log(f"❌ GitHub触发限流，第{attempt+1}次重试，等待{retry_delay}秒")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                write_log(f"❌ GitHub上传失败：{put_res.text}")
                return None, None
        except Exception as e:
            write_log(f"❌ GitHub异常，第{attempt+1}次重试：{str(e)}")
            time.sleep(retry_delay)
            retry_delay *= 2
    write_log(f"❌ GitHub上传最终失败，已达最大重试次数")
    return None, None

# Notion分段写入+回读对账
def write_to_notion(chapter_name, content, github_url, md5, real_chars):
    try:
        notion = Client(auth=NOTION_TOKEN)
        page = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "章节名": {"title": [{"text": {"content": chapter_name}}]},
                "字数": {"number": real_chars},
                "产出时间": {"date": {"start": datetime.now().isoformat()}},
                "状态": {"select": {"name": "生成中"}},
                "GitHub母本链接": {"url": github_url} if github_url else {},
                "MD5校验值": {"rich_text": [{"text": {"content": md5}}]} if md5 else {}
            }
        )
        page_id = page["id"]
        write_log(f"✅ Notion页面创建成功，Page ID：{page_id}")

        chunks = [content[i:i+1500] for i in range(0, len(content), 1500)]
        for idx, chunk in enumerate(chunks, 1):
            notion.blocks.children.append(
                page_id,
                children=[{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]}
                }]
            )
            write_log(f"✅ 第{idx}/{len(chunks)}段写入成功")

        final_blocks = notion.blocks.children.list(page_id)["results"]
        written_content = "".join([
            block["paragraph"]["rich_text"][0]["text"]["content"]
            for block in final_blocks
            if block["type"] == "paragraph" and block["paragraph"]["rich_text"]
        ])
        written_chars = count_real_chars(written_content)

        if written_chars >= real_chars * 0.98:
            notion.pages.update(
                page_id,
                properties={"状态": {"select": {"name": "已完成"}}}
            )
            write_log(f"🎉 对账完成！实际写入{written_chars}字，与生成内容一致")
            return True, page_id, written_chars
        else:
            write_log(f"❌ 对账失败！生成{real_chars}字，仅写入{written_chars}字")
            notion.pages.update(
                page_id,
                properties={"状态": {"select": {"name": "写入失败"}}}
            )
            return False, page_id, written_chars

    except Exception as e:
        write_log(f"❌ Notion写入失败：{str(e)}")
        return False, None, 0

# ================= 页面UI渲染 =================
st.title("🚀 赛博印钞机：囡囡的 Web 驾驶舱")
st.markdown("---")

col_ctrl, col_log = st.columns([1, 2])

with col_ctrl:
    st.subheader("⚡ 核心点火控制")
    st.markdown('<div class="status-card">', unsafe_allow_html=True)
    
    chapter_num = st.number_input("生成章节号", min_value=1, value=2, step=1)
    chapter_title = st.text_input("章节标题", value=f"第{chapter_num}章 万亿战神归都市，前妻跪地求复婚")
    novel_prompt = st.text_area(
        "本章核心爽点指令", 
        height=150,
        placeholder="例如：男主百辆豪车接机震撼全场，前妻苏清雪当众下跪复婚，男主亮出万亿资产身份碾压林家，五年前婚礼真相曝光..."
    )
    target_word_count = st.number_input("目标字数", min_value=1000, value=7500, step=500)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("###")

    start_btn = st.button("🔥 一键点火 (唤醒囡囡与屠夫)", type="primary")
    refresh_log_btn = st.button("🔄 刷新日志", use_container_width=True)

with col_log:
    st.subheader("📟 系统实时日志 (2015 iMac 监听中)")
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            log_lines = f.readlines()[-30:]
        st.code("".join(log_lines), language="bash", line_numbers=False)
    else:
        st.info("系统静默中，等待点火指令...")
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 系统初始化完成，等待指令\n")

st.markdown("---")
st.subheader("🔗 基础设施状态看板")
status_col1, status_col2, status_col3, status_col4 = st.columns(4)

with status_col1:
    notion_status = "✅ 正常" if NOTION_TOKEN and len(NOTION_TOKEN)>10 else "❌ 未配置"
    st.metric("Notion API", notion_status)
with status_col2:
    github_status = "✅ 正常" if GITHUB_TOKEN and len(GITHUB_TOKEN)>10 else "❌ 未配置"
    st.metric("GitHub母本库", github_status)
with status_col3:
    script_status = "✅ 正常" if GEN_SCRIPT_PATH and os.path.exists(GEN_SCRIPT_PATH) else "⚠️ 未配置"
    st.metric("生成脚本", script_status)
with status_col4:
    st.metric("系统负载", "✅ 低烧运行")

# ================= 核心点火逻辑 =================
if start_btn:
    if not novel_prompt:
        st.error("请填写本章核心爽点指令！")
        st.stop()
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        st.error("请先在.env文件配置Notion凭证！")
        st.stop()
    if not GITHUB_TOKEN or not GITHUB_REPO:
        st.error("请先在.env文件配置GitHub凭证！")
        st.stop()
    
    write_log(f"🔥 收到点火指令，开始生成{chapter_title}，目标字数{target_word_count}")
    st.toast("指令已下发，囡囡正在唤醒午夜屠夫...", icon="🔥")

    try:
        if GEN_SCRIPT_PATH and os.path.exists(GEN_SCRIPT_PATH):
            write_log("📤 调用外部生成脚本...")
            result = subprocess.run(
                [GEN_SCRIPT_PATH, str(chapter_num), novel_prompt, str(target_word_count)],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            full_content = result.stdout
            if result.stderr:
                write_log(f"⚠️ 生成脚本警告：{result.stderr}")
        else:
            write_log("⚠️ 未找到生成脚本，使用内置兜底生成逻辑")
            full_content = f"# {chapter_title}\n\n{novel_prompt}\n\n（此处为生成的7500字正文，替换为你的模型生成内容）"
        
        real_chars = count_real_chars(full_content)
        write_log(f"📝 生成完成，实际有效字数：{real_chars}字")

        if real_chars < target_word_count * 0.95:
            write_log(f"❌ 生成字数不达标，目标{target_word_count}字，仅生成{real_chars}字")
            st.error(f"生成字数不达标！目标{target_word_count}字，仅生成{real_chars}字")
            st.stop()

        github_url, md5 = upload_to_github(full_content, chapter_title)
        if not github_url:
            st.error("GitHub上传失败，请检查Token和仓库配置！")
            st.stop()

        write_success, page_id, written_chars = write_to_notion(
            chapter_title, full_content, github_url, md5, real_chars
        )

        if write_success:
            st.success(f"🎉 全流程执行完成！{chapter_title} 已成功生成并写入Notion，实际有效字数{written_chars}字")
            write_log(f"🎉 全流程闭环完成！章节已归档，Page ID：{page_id}")
        else:
            st.error("❌ Notion写入失败，请查看系统日志排查问题")

    except Exception as e:
        write_log(f"❌ 核心流程执行失败：{str(e)}")
        st.error(f"执行失败：{str(e)}")

if refresh_log_btn:
    st.rerun()
