#!/bin/bash
# =============================================
# OpenHarness 启动脚本 - OpenMars
# =============================================

echo "================================================"
echo "  OpenHarness 启动器 - OpenMars"
echo "================================================"
echo ""

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "❌ 错误：未找到 .env 文件！"
    echo "请先复制 .env.example 为 .env 并填写配置"
    exit 1
fi

# 读取 .env 文件
echo "📋 正在读取配置..."
source .env

# 检查 API Key
if [ -z "$LLM_API_KEY" ] || [ "$LLM_API_KEY" = "请在这里填入你的_DeepSeek_API_Key" ]; then
    echo "⚠️  警告：未配置 API Key！"
    echo "请编辑 .env 文件，填入你的 API Key"
    echo ""
    read -p "是否继续？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 设置 OpenHarness 环境变量
export OPENHARNESS_API_FORMAT=openai
export OPENHARNESS_BASE_URL="$API_BASE_URL"
export OPENAI_API_KEY="$LLM_API_KEY"
export OPENHARNESS_MODEL="$LLM_MODEL_NAME"

echo ""
echo "🚀 配置信息："
echo "   API 格式: OpenAI"
echo "   API 地址: $API_BASE_URL"
echo "   模型: $LLM_MODEL_NAME"
echo ""
echo "================================================"
echo ""

# 启动 OpenHarness
echo "正在启动 OpenHarness..."
echo ""

/usr/local/bin/python3.13 -m openharness
