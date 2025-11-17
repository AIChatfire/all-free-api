#!/bin/bash
# minio-clean-15d-root.sh
# 只删 15 天前 date 目录（cdn/YYYYMMDD/）下的全部对象

set -e

# ---------- 用户配置 ----------
ENDPOINT="http://110.42.51.201:19000"
ACCESS_KEY="**********"
SECRET_KEY="*************************"
ALIAS="minio"
BUCKET="cdn"
DAYS_AGO=15
DRY_RUN=false          # true=只预览，false=真删
# ------------------------------

CUTOFF_DATE=$(date -d "$DAYS_AGO days ago" +%Y%m%d)

mc alias set "$ALIAS" "$ENDPOINT" "$ACCESS_KEY" "$SECRET_KEY" >/dev/null

echo "=== MinIO 15-day root cleanup ==="
echo "Cutoff : $CUTOFF_DATE (<= 该日期目录将被清空)"
echo "Mode   : $([ "$DRY_RUN" = true ] && echo 'DRY-RUN' || echo 'EXECUTE')"

DIRS=$(mc find "${ALIAS}/${BUCKET}" \
       | sed -E "s|${ALIAS}/${BUCKET}/([0-9]{8})/.*|\1|" | sort -u)

TO_DEL=$(echo "$DIRS" | awk -v cut="$CUTOFF_DATE" '$1 <= cut')
[ -z "$TO_DEL" ] && { echo "没有需要清空的目录。"; exit 0; }

echo "待清空目录："
echo "$TO_DEL"

[ "$DRY_RUN" = true ] && { echo "干跑完成，未删除。"; exit 0; }

echo "开始清空..."
for d in $TO_DEL; do
    echo "Removing ${ALIAS}/${BUCKET}/${d}/"
    mc rm --recursive --force "${ALIAS}/${BUCKET}/${d}/"
done
echo "清空完成。"