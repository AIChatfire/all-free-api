#!/usr/bin/env bash
# @Project      : AI @by PyCharm
# @Time         : 2024/11/28 10:04
# @Author       : betterme
# @Email        : 313303303@qq.com
# @Software     : PyCharm
# @Description  :

# 检查WORKER_TYPE环境变量是否设置
if [ -z "$WORKER_TYPE" ]; then
  echo "Error: WORKER_TYPE environment variable is not set"
  exit 1
fi

# 使用case语句根据WORKER_TYPE执行不同的任务
case "$WORKER_TYPE" in
"web")
  echo "开启 fastapi..."
  python -m meutils.clis.server gunicorn-run main:app --port 8000 --workers ${WORKERS:-1} --threads 2
  ;;

"worker")
  echo "开启异步队列..."
  python -m celery --app celery-worker -A meutils.serving.celery.tasks worker -l DEBUG -c 3
  ;;

"flower")
  echo "开启异步任务监控..."
  python -m celery --app celery-flower -A meutils.serving.celery.tasks flower --port=5001
  ;;

"scheduler")
  echo "Starting scheduler..."
  python scheduler.py
  ;;
*)
  echo "Error: Unknown WORKER_TYPE: $WORKER_TYPE"
  echo "Supported types: web, worker, scheduler"
  exit 1
  ;;
esac
