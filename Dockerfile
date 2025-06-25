FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-jre-headless \
    graphviz \
    fonts-wqy-zenhei \
    fonts-freefont-ttf \
    fontconfig \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# 创建工作目录
WORKDIR /app

# 复制应用文件
COPY . /app

# 暴露端口（如果需要）
EXPOSE 8080
EXPOSE 8765

# 设置启动命令
CMD ["sh", "start.sh"]