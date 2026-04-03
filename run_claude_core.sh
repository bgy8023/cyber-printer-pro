#!/bin/bash
# 赛博印钞机 Pro - 核心胶水脚本（Claude 核心版）

# ================= 系统兼容处理 =================
# Mac用gtimeout，Linux用timeout
if command -v gtimeout &> /dev/null; then
    TIMEOUT_CMD="gtimeout"
else
    TIMEOUT_CMD="timeout"
fi

# ================= 入参处理 =================
CHAPTER_NUM=$1
PROMPT=$2
TARGET_WORDS=$3
AGENT_NAME=${4:-"main-2"}
ENABLE_HUMANIZER=${5:-"true"}
ENABLE_MULTI_AGENT=${6:-"true"}

# ================= 路径处理 =================
# 动态确定内置资源目录（兼容打包前后）
if [ -n "$APP_BUILTIN_RESOURCES" ]; then
  RESOURCE_DIR="$APP_BUILTIN_RESOURCES"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  RESOURCE_DIR="$SCRIPT_DIR"
fi

# ================= 路径定义 =================
BUILTIN_SKILLS_DIR="$RESOURCE_DIR/builtin_skills"
NOVEL_SETTINGS_DIR="$RESOURCE_DIR/novel_settings"
OUTPUT_DIR="$RESOURCE_DIR/output"
mkdir -p "$OUTPUT_DIR"

# ================= 前置校验 =================
# 确保虚拟环境激活
if [ -f "$RESOURCE_DIR/venv/bin/activate" ]; then
    source "$RESOURCE_DIR/venv/bin/activate"
fi

# ================= 内置技能加载 =================
echo "🔗 正在加载内置技能..."
mkdir -p "$NOVEL_SETTINGS_DIR"
if [ ! -f "$NOVEL_SETTINGS_DIR/1_番茄爆款写作心法.md" ]; then
  cat << 'DEFAULT_SETTING' > "$NOVEL_SETTINGS_DIR/1_番茄爆款写作心法.md"
# 番茄爆款写作心法
## 核心铁律
1. 开头300字必须有冲突
2. 每章必有打脸高潮
3. 结尾必须留悬念钩子
4. 主角永远不废话，直接降维打击
5. 详细描写围观群众震惊、倒吸一口凉气的反应
DEFAULT_SETTING
fi

# ================= 结构化记忆加载 =================
echo "🧠 正在加载结构化记忆..."
MEMORY_FILE="$NOVEL_SETTINGS_DIR/2_剧情自动推演记录.md"
STRUCTURED_MEMORY=""
if [ -f "$MEMORY_FILE" ]; then
  STRUCTURED_MEMORY=$(grep -E "主角|反派|核心设定|第${CHAPTER_NUM-1}章|伏笔" "$MEMORY_FILE" | head -50)
fi

# ================= 核心生成函数 =================
function generate_with_claude_core() {
    local chapter_num="$1"
    local prompt="$2"
    local target_words="$3"
    local output_file="$4"
    
    echo "🤖 正在调用 Claude 核心生成内容..."
    
    # 使用 Python 脚本调用 Claude 核心
    python3 -c "
import sys
import os
sys.path.insert(0, '$RESOURCE_DIR')
from builtin_claude_core.query_engine import ClaudeQueryEngine
from builtin_claude_core.memory_palace import get_memory_palace

# 初始化引擎
engine = ClaudeQueryEngine()

# 绑定记忆宫殿
memory_palace = get_memory_palace()

# 生成内容
try:
    agent_result = engine.multi_agent_coordinate(
        chapter_num=$chapter_num,
        target_words=$target_words,
        custom_prompt='$prompt',
        chapter_outline='',
        chapter_name=''
    )
    final_content = agent_result['content']
    real_chars = agent_result['real_chars']
    
    # 写入文件
    with open('$output_file', 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f'✅ 生成成功，字数：{real_chars}')
except Exception as e:
    print(f'❌ 生成失败：{str(e)}')
    sys.exit(1)
"
    
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "❌ 生成失败，退出码：$exit_code"
        return 1
    fi
    
    if [ ! -s "$output_file" ]; then
        echo "❌ 生成内容为空"
        return 1
    fi
    
    echo "✅ 生成成功"
    return 0
}

# ================= 汉字统计函数 =================
function count_real_chars() {
    local text="$1"
    echo "$text" | grep -o "[\u4e00-\u9fa5]" | wc -l | awk '{print $1}'
}

# ================= 生成执行 =================
FINAL_CONTENT=""
OUTPUT_FILE="$OUTPUT_DIR/第${CHAPTER_NUM}章_$(date +%Y%m%d%H%M).md"

# 调用 Claude 核心生成
generate_with_claude_core "$CHAPTER_NUM" "$PROMPT" "$TARGET_WORDS" "$OUTPUT_FILE"
if [ $? -ne 0 ]; then
    echo "❌ 正文生成失败"
    exit 1
fi

# 读取生成的内容
FINAL_CONTENT=$(cat "$OUTPUT_FILE")

# ================= 字数统计与校验 =================
REAL_CHARS=$(count_real_chars "$FINAL_CONTENT")
echo "📊 最终有效汉字：${REAL_CHARS}字（目标${TARGET_WORDS}字）"
if [ $REAL_CHARS -lt $TARGET_WORDS ]; then
    echo "ℹ️  提示：实际字数少于目标，但继续执行"
else
    echo "✅ 字数达标"
fi

echo "✅ 全流程执行完成"
echo "✅ 最终文件已写入：$OUTPUT_FILE"
