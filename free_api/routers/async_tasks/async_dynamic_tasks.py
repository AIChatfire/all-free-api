#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : common
# @Time         : 2024/12/20 16:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 适合适配于第三方接口
# 动态路由
import shortuuid

from meutils.pipe import *

from meutils.db.redis_db import redis_aclient
from meutils.decorators.contextmanagers import atry_catch
from meutils.notice.feishu import send_message_for_dynamic_router as send_message
from meutils.llm.openai_utils import billing_flow_for_async_task
from meutils.llm.openai_utils.usage_utils import get_billing_n
from meutils.schemas.task_types import FluxTaskResponse

from meutils.apis.utils import make_request

from meutils.serving.fastapi.dependencies.auth import parse_token
from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi import File, UploadFile, Header, Query, Form, Body, Request

router = APIRouter()
TAGS = ["通用异步任务"]

"""
https://api.ppinfra.com/v3/async/minimax-hailuo-02
"""


@router.get("/{biz}/v1/{path:path}")
async def get_task(
        request: Request,

        biz: str = "zhipuai",
        path: str = "request-path",

        headers: dict = Depends(get_headers),
):
    logger.debug(f"biz: {biz} path: {path}")
    logger.debug(bjson(headers))
    logger.debug(bjson(request.query_params))

    # 获取所有查询参数
    params = dict(request.query_params)
    task_id = params.get("id") or params.get("task_id") or params.get("request_id")

    # 上游信息
    upstream_base_url = headers.get('upstream_base_url')
    upstream_get_path = headers.get('upstream_get_path')
    # https://open.bigmodel.cn/api/paas/v4/async-result/{id}
    if "{" in upstream_get_path:  # task_id 从路径上去
        task_id = Path(path).name
        upstream_get_path = upstream_get_path.format(id=task_id)

    upstream_api_key = await redis_aclient.get(task_id)
    upstream_api_key = upstream_api_key and upstream_api_key.decode()
    logger.debug(upstream_api_key)
    if not upstream_api_key:
        raise HTTPException(status_code=404, detail="TaskID not found")

    response = await make_request(
        base_url=upstream_base_url,
        path=upstream_get_path,
        api_key=upstream_api_key,

        params=params,
        method=request.method
    )

    # 异步任务信号
    flux_task_response = FluxTaskResponse(id=task_id, result=response, details=response)
    if flux_task_response.status in {"Ready", "Error"}:
        await redis_aclient.set(f"response:{task_id}", flux_task_response.model_dump_json(exclude_none=True))

    return response


@router.post("/{biz}/v1/{path:path}")
async def create_task(
        request: Request,

        biz: str = "zhipuai",
        path: str = "request-path",

        headers: dict = Depends(get_headers),
        api_key: Optional[str] = Depends(get_bearer_token),

):
    logger.debug(f"biz: {biz} path: {path}")
    logger.debug(bjson(headers))

    # 上游信息
    upstream_base_url = headers.get('upstream_base_url')
    upstream_api_key = headers.get('upstream_api_key')  # 上游号池管理:
    upstream_api_key = await parse_token(upstream_api_key)

    upstream_post_path = headers.get('upstream_post_path')
    # https://open.bigmodel.cn/api/paas/v4/videos/generations

    # 获取请求体
    payload = await request.json()

    # 获取模型名称
    model = payload.get("model") or payload.get("model_name") or "UNKNOWN"
    if biz == "fal-ai":
        model = f"{biz}/{path}".replace("/", "-")

    # 获取计费次数
    billing_n = get_billing_n(payload)

    local_task_id = str(shortuuid.random())

    async with atry_catch(f"{biz}/{model}", api_key=api_key, callback=send_message, request=payload):
        async with billing_flow_for_async_task(model, task_id=local_task_id, api_key=api_key, n=billing_n):
            response = await make_request(
                base_url=upstream_base_url,
                path=upstream_post_path,
                payload=payload,

                api_key=upstream_api_key,
                method=request.method
            )

            # local_task_id => task_id => response
            task_id = response.get("id") or response.get("task_id") or response.get("request_id")

            await redis_aclient.set(local_task_id, task_id, ex=7 * 24 * 3600)
            await redis_aclient.set(task_id, upstream_api_key, ex=7 * 24 * 3600)

            return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
