#!/bin/bash
# 赛博印钞机 Pro - 核心胶水脚本（openmars路径自动检测版）

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

# ================= 【核心修复】自动检测openmars命令 =================
CLAW_BIN=""
# 优先从环境变量读取
if [ -n "$OPENMARS_CLAW_PATH" ]; then
  if [ -f "$OPENMARS_CLAW_PATH" ]; then
    CLAW_BIN="$OPENMARS_CLAW_PATH"
  fi
fi
# 从常见位置查找
if [ -z "$CLAW_BIN" ]; then
  for possible_path in \
    "$HOME/.openmars/workspace/openmars" \
    "$HOME/.openmars/openmars" \
    "$HOME/.claude/openmars" \
    "/usr/local/bin/openmars" \
    "/opt/homebrew/bin/openmars"; do
    if [ -f "$possible_path" ]; then
      CLAW_BIN="$possible_path"
      break
    fi
  done
fi
# 用which查找
if [ -z "$CLAW_BIN" ]; then
  if command -v openmars &> /dev/null; then
    CLAW_BIN="$(command -v openmars)"
  fi
fi
# 最终校验
if [ -z "$CLAW_BIN" ] || [ ! -f "$CLAW_BIN" ]; then
  echo "❌ 致命错误：未找到openmars命令！"
  echo "💡 请确认OpenMars/Claude Code已正确安装，或设置环境变量OPENMARS_CLAW_PATH指定openmars路径"
  exit 1
fi
chmod +x "$CLAW_BIN" 2>/dev/null
echo "✅ 使用openmars命令：$CLAW_BIN"

# ================= 路径定义 =================
BUILTIN_SKILLS_DIR="$RESOURCE_DIR/builtin_skills"
NOVEL_SETTINGS_DIR="$RESOURCE_DIR/novel_settings"
OPENMARS_WORKSPACE="$HOME/.openmars/workspace"

# ================= 前置校验 =================
# 确保工作区存在
mkdir -p "$OPENMARS_WORKSPACE"
cd "$OPENMARS_WORKSPACE" || { echo "❌ 无法进入OpenMars工作区：$OPENMARS_WORKSPACE"; exit 1; }

# ================= 内置技能加载 =================
echo "🔗 正在加载内置技能..."
mkdir -p "$OPENMARS_WORKSPACE/skills"
for skill_dir in "$BUILTIN_SKILLS_DIR"/*; do
  if [ -d "$skill_dir" ]; then
    skill_name=$(basename "$skill_dir")
    rm -rf "$OPENMARS_WORKSPACE/skills/$skill_name"
    cp -r "$skill_dir" "$OPENMARS_WORKSPACE/skills/"
    echo "✅ 已加载内置技能：$skill_name"
  fi
done

# 确保novel_settings存在
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

# ================= 技能列表自动加载 =================
SKILL_LIST=()
for skill_dir in "$BUILTIN_SKILLS_DIR"/*; do
  if [ -d "$skill_dir" ]; then
    SKILL_LIST+=("$(basename "$skill_dir")")
  fi
done
SKILL_STR=$(IFS=,; echo "${SKILL_LIST[*]}")

# ================= 核心生成函数 =================
function safe_openmars_chat() {
    local prompt="$1"
    local timeout="${2:-240}"
    local output_file="$3"
    
    echo "🤖 正在调用大模型生成内容..."
    "$TIMEOUT_CMD" "$timeout" "$CLAW_BIN" agent --agent "$AGENT_NAME" --message "$prompt" --local --thinking low > "$output_file" 2>&1
    
    local exit_code=$?
    if [ $exit_code -eq 124 ]; then
        echo "⚠️  生成超时，已终止命令"
        return 1
    fi
    if [ $exit_code -ne 0 ]; then
        echo "❌ 生成失败，退出码：$exit_code"
        cat "$output_file"
        return 1
    fi
    
    # 清理输出 - 只移除 OpenMars 开头的日志行
    # 保留所有其他内容
    
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

# ================= 多智能体协调模式 =================
FINAL_CONTENT=""
if [ "$ENABLE_MULTI_AGENT" = "true" ]; then
  echo "🤝 多智能体协调模式已激活"
  
  # 子代理1：大纲规划
  echo "📋 子代理1（大纲师）：正在规划剧情"
  OUTLINE_PROMPT="你是专业网文大纲师，基于以下结构化记忆和核心要求，规划第${CHAPTER_NUM}章的详细剧情大纲，要求有冲突、有打脸、有悬念，严格防吃书，不崩人设，只输出大纲，不要多余解释。结构化记忆：${STRUCTURED_MEMORY}。核心要求：${PROMPT}"
  safe_openmars_chat "$OUTLINE_PROMPT" 60 "/tmp/chapter_outline.txt"
  if [ $? -ne 0 ]; then
    echo "❌ 大纲规划失败，切换单Agent模式"
    ENABLE_MULTI_AGENT="false"
  else
    CHAPTER_OUTLINE=$(cat /tmp/chapter_outline.txt)
    echo "✅ 子代理1：大纲规划完成"
  fi
  
  # 子代理2：正文生成
  if [ "$ENABLE_MULTI_AGENT" = "true" ]; then
    echo "✍️ 子代理2（主笔）：正在生成正文"
    CONTENT_PROMPT="你是专业网文主笔，严格遵循以下大纲，使用Undercover Mode生成第${CHAPTER_NUM}章完整正文，字数要求${TARGET_WORDS}字，严格保留人设，爽点密集，结尾留悬念，只输出正文，不要任何多余解释。大纲：${CHAPTER_OUTLINE}。核心要求：${PROMPT}"
    safe_openmars_chat "$CONTENT_PROMPT" 240 "/tmp/chapter_content.txt"
    if [ $? -ne 0 ]; then
        echo "❌ 正文生成失败"
        exit 1
    fi
    GENERATED_CONTENT=$(cat /tmp/chapter_content.txt)
    echo "✅ 子代理2：正文生成完成"
  fi
  
  # 子代理3：校验优化
  if [ "$ENABLE_MULTI_AGENT" = "true" ]; then
    echo "🔍 子代理3（校验师）：正在校验内容"
    CHECK_PROMPT="你是专业网文校验师，检查下面的小说正文，核对人设和剧情是否符合结构化记忆，核对字数是否达标，优化结尾悬念，修正吃书问题，只输出优化后的完整正文，不要任何多余解释。结构化记忆：${STRUCTURED_MEMORY}。目标字数：${TARGET_WORDS}字。正文：${GENERATED_CONTENT}"
    safe_openmars_chat "$CHECK_PROMPT" 120 "/tmp/chapter_final.txt"
    if [ $? -ne 0 ]; then
        echo "⚠️  校验优化失败，保留原始正文"
        FINAL_CONTENT="$GENERATED_CONTENT"
    else
        FINAL_CONTENT=$(cat /tmp/chapter_final.txt)
        echo "✅ 子代理3：校验优化完成"
    fi
  fi
fi

# ================= 单Agent模式（兜底） =================
if [ "$ENABLE_MULTI_AGENT" = "false" ] || [ -z "$FINAL_CONTENT" ]; then
  echo "🤖 单Agent模式已激活，正在生成正文"
  SINGLE_PROMPT="生成第 ${CHAPTER_NUM} 章。字数要求：${TARGET_WORDS}字。核心要求：${PROMPT}。结构化记忆：${STRUCTURED_MEMORY}。只输出正文，不要任何多余解释。"
  safe_openmars_chat "$SINGLE_PROMPT" 300 "/tmp/chapter_final.txt"
  if [ $? -ne 0 ]; then
    echo "❌ 正文生成失败"
    exit 1
  fi
  FINAL_CONTENT=$(cat /tmp/chapter_final.txt)
fi

# ================= Humanizer二次去AI化 =================
if [ "$ENABLE_HUMANIZER" = "true" ]; then
  echo "🧹 正在调用Humanizer技能，二次去AI化"
  HUMANIZE_PROMPT="请使用Humanizer技能，对下面的小说正文进行二次去AI化处理，严格保留原剧情、人设、爽点、节奏和字数，只去除残留的AI痕迹，让文本更像真人写的网文，直接输出改写后的完整正文，不要任何额外解释：\n\n${FINAL_CONTENT}"
  safe_openmars_chat "$HUMANIZE_PROMPT" 180 "/tmp/chapter_humanized.txt"
  if [ $? -eq 0 ]; then
    FINAL_CONTENT=$(cat /tmp/chapter_humanized.txt)
    echo "✅ 二次去AI化完成"
  else
    echo "⚠️  去AI化失败，保留原始正文"
  fi
fi

# ================= 最终文件写入 =================
OUTPUT_FILE="$OPENMARS_WORKSPACE/第${CHAPTER_NUM}章_$(date +%Y%m%d%H%M).md"
echo "${FINAL_CONTENT}" > "$OUTPUT_FILE"
echo "✅ 最终文件已写入：$OUTPUT_FILE"

# ================= 字数统计与校验 =================
REAL_CHARS=$(count_real_chars "$FINAL_CONTENT")
echo "📊 最终有效汉字：${REAL_CHARS}字（目标${TARGET_WORDS}字）"
if [ $REAL_CHARS -lt $TARGET_WORDS ]; then
    echo "ℹ️  提示：实际字数少于目标，但继续执行"
else
    echo "✅ 字数达标"
fi

echo "✅ 全流程执行完成"
