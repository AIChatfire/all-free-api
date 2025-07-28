#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : common
# @Time         : 2024/12/20 16:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 内置接口: 不计费

from meutils.pipe import *

from meutils.decorators.contextmanagers import atry_catch
from meutils.notice.feishu import send_message_for_dynamic_router as send_message

from meutils.apis.utils import make_request
from meutils.apis.models import create_fal_models

from meutils.apis.oneapi.user import get_user_money
from meutils.llm.openai_utils.billing_utils import billing_for_async_task

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers
from meutils.serving.fastapi.dependencies.auth import parse_token

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi import File, UploadFile, Header, Query, Form, Body, Request

router = APIRouter()
TAGS = ["同步任务"]


@router.api_route("/v1/{path:path}", methods=["POST"])
async def create_fal_task(
        request: Request,

        path: str,  # response_model 计费模型

        api_key: Optional[str] = Depends(get_bearer_token),
        headers: dict = Depends(get_headers),

):
    logger.debug(f"model: {path}")
    logger.debug(bjson(headers))

    # 上游信息
    upstream_api_key = headers.get('upstream_api_key')  # 上游号池管理
    upstream_api_key = await parse_token(upstream_api_key)

    headers = {"Authorization": f"Key {upstream_api_key}"}

    # 获取请求体 todo: formdata
    payload = await request.json()  # get 可能没有

    # 获取模型名称
    model = f'fal-{path.replace("/", "-")}'

    # 计费模型
    fal_model = path.split('/')[0]
    if billing_model := create_fal_models(fal_model, payload):
        model = f"{model}_{billing_model}"

    # 执行
    async with atry_catch(
            f"{model}", callback=send_message, request=payload,
            upstream_api_key=upstream_api_key,
    ):
        # 检查余额
        if user_money := await get_user_money(api_key):
            if user_money < 1:
                raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="余额不足")

        response = await make_request(
            base_url="https://fal.run/fal-ai",
            api_key=upstream_api_key,

            path=path,
            payload=payload,

            method=request.method,
            headers=headers,

            debug=True
        )

        await billing_for_async_task(model=model)  # 计费

        return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/fal-ai-sync')  # https://queue.fal.run/fal-ai/

    app.run()

"""
curl -X 'POST' \
  'http://0.0.0.0:8000/fal-ai-sync/v1/ideogram/v3/reframe' \
  -H 'Authorization: Bearer sk-a0NBq6v0al2JSoViB1x92HOJDaoU6VcojF5V0h9HoKeazvTn' \
  -H 'Content-Type: application/json' \
  -H 'upstream_api_key: redis:https://xchatllm.feishu.cn/sheets/Z59Js10DbhT8wdt72LachSDlnlf?sheet=iFRwmM' \
  -d '{
  "rendering_speed": "TURBO",
  "num_images": 1,
  "image_url": "https://v3.fal.media/files/lion/0qJs_qW8nz0wYsXhFa6Tk.png",
  "image_size": "square_hd",
  "image_urls": []
}'




"""
