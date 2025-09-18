#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : kv
# @Time         : 2025/9/18 18:40
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.db.redis_db import redis_aclient

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body

router = APIRouter()
TAGS = ["sys"]

"""
MY_IP=$(ip -4 -o addr show scope global | awk '{print $4}' | cut -d/ -f1 | head -n1)
echo "$MY_IP"

# 尝试使用 ip 命令获取 IP 地址
MY_IP=$(ip -4 -o addr show scope global | awk '{print $4}' | cut -d/ -f1 | head -n1)

# 如果 MY_IP 为空，尝试使用 ifconfig 命令获取 IP 地址
if [ -z "$MY_IP" ]; then
    MY_IP=$(ifconfig | awk '/inet / && $2!="127.0.0.1"{print $2; exit}')
fi

# 输出最终获取的 IP 地址
echo "$MY_IP"

# 发起 curl 请求
response=$(curl -s -X GET "http://localhost:8000/sys/r/pods?exclude=$MY_IP" -H "Content-Type: application/json")

# 输出响应内容（调试用）
echo "Response: $response"

# 解析 JSON 数据
json_status=$(echo $response | grep -o '"status":\s*true' | grep -o 'true')

# 判断 status 是否为 true
if [ "$json_status" = "true" ]; then
  echo "Status is true, proceeding to the next step."
  # 在这里执行下一步操作
else
  echo "Status is not true, stopping."
fi


1. 获取当前IP
2. 接口返回更新信号，更新完成后删除ip

"""


@router.get("/{key}")
async def get_kv(
        key: str,
        exclude: Optional[str] = Query(None),  # value 去除里的字符串

):
    # if (rtype := await redis_aclient.type(key)) and rtype.decode() == 'string':
    data = {
        'biz': key,
    }
    if key.startswith(("pod",)):
        if (v := await redis_aclient.get(key)) and (ips := v.decode()):
            logger.debug(v)

            if exclude and exclude in ips:
                ips = ips.replace(exclude, '')
                await redis_aclient.set(key, ips, ex=100)

                data['status'] = True
                data['pods'] = ips

                return data
            else:
                data['status'] = False
                data['pods'] = ips

                return data


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/r')

    app.run()
