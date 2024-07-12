# 使用官方python基础镜像
FROM python:3.10-slim
LABEL maintainer="313303303@qq.com"

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000


# Install pip requirements
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade -r requirements.txt


# 创建工作目录
WORKDIR /app

# 复制当前目录下的所有文件到工作目录
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser






# 容器启动时运行命令
# 设置容器启动后默认执行的命令及其参数。不过，CMD 指定的命令可以通过 docker run 命令行参数来覆盖。它主要用于为容器设定默认启动行为。如果 Dockerfile 中有多个 CMD 指令，只有最后一个生效。
# docker run myimage <bash> # bash 将会替换掉Dockerfile中的  CMD 指令。
# ${WORKERS:-1} 默认1
#ENV WORKERS=${WORKERS:-1}

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "3"]

#CMD ["python",  "-m",  "meutils.clis.server",  "gunicorn-run",  "main:app",  "--port",  "8000",  "--workers", "${WORKERS:-1}",  "--threads",  "2",  "--timeout",  "100"]

CMD ["sh", "-c", "sh rq-worker.sh & python -m meutils.clis.server gunicorn-run main:app --port 8000 --workers ${WORKERS:-1} --threads 2"]

