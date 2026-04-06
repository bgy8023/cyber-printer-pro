# 多阶段构建，瘦身优化
FROM python:3.10-slim as builder

WORKDIR /app
COPY requirements.txt .
# 构建阶段安装依赖，无缓存
RUN pip install --no-cache-dir -r requirements.txt

# 最终运行阶段
FROM python:3.10-slim

WORKDIR /app
# 从构建阶段复制依赖，避免重复安装
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制项目代码
COPY . .

# 创建必要目录
RUN mkdir -p /app/novel_settings /app/output /app/logs

# 暴露端口
EXPOSE 8501

# 健康检查，自动重启异常容器
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 启动命令，适配老设备优化
CMD ["streamlit", "run", "web_panel_industrial.py", "--server.port=8501", "--server.address=0.0.0.0", "--browser.gatherUsageStats=false", "--server.headless=true"]
