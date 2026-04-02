#!/bin/bash
# Notion 数据库环境变量设置脚本
# 网文自动化中台 - 核心数据库 ID

export NOTION_BODY_DB_ID="3335eb3b-5abc-81a4-9df4-cc284bd50bdb"
export NOTION_OUTLINE_DB_ID="3335eb3b-5abc-8122-b74d-db80b9d61f16"
export NOTION_INTEL_DB_ID="3335eb3b-5abc-8104-8a40-f70bf27a8141"
export NOTION_LOG_DB_ID="3335eb3b-5abc-81b9-b838-e888282fa6f9"

echo "✅ Notion 数据库环境变量已设置："
echo "   NOTION_BODY_DB_ID: $NOTION_BODY_DB_ID"
echo "   NOTION_OUTLINE_DB_ID: $NOTION_OUTLINE_DB_ID"
echo "   NOTION_INTEL_DB_ID: $NOTION_INTEL_DB_ID"
echo "   NOTION_LOG_DB_ID: $NOTION_LOG_DB_ID"

# 可以将这些变量添加到 .zshrc 或 .bashrc 以持久化
# echo 'export NOTION_BODY_DB_ID="3335eb3b-5abc-81a4-9df4-cc284bd50bdb"' >> ~/.zshrc
# echo 'export NOTION_OUTLINE_DB_ID="3335eb3b-5abc-8122-b74d-db80b9d61f16"' >> ~/.zshrc
# echo 'export NOTION_INTEL_DB_ID="3335eb3b-5abc-8104-8a40-f70bf27a8141"' >> ~/.zshrc
# echo 'export NOTION_LOG_DB_ID="3335eb3b-5abc-81b9-b838-e888282fa6f9"' >> ~/.zshrc