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

from openai import AsyncClient

from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import ppu_flow

from meutils.apis.utils import make_request

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi import File, UploadFile, Header, Query, Form, Body, Request

router = APIRouter()
TAGS = ["视频生成"]


@router.get("/tasks/{path:path}")
@router.get("/tasks")
@alru_cache(ttl=15)
async def get_task(
        request: Request,
        path: str = "task_id",

        upstream_model: Optional[str] = Header(None),  # 计费名称
        upstream_base_url: Optional[str] = Header(None),
        upstream_path: Optional[str] = Header(None),
        upstream_api_key: Optional[str] = Header(None),
):
    # 获取路径参数
    path_parts = path.split('/')  # todo

    # 获取所有查询参数
    params = dict(request.query_params)

    response = await make_request(
        base_url=upstream_base_url,
        path=upstream_path,
        api_key=upstream_api_key,

        params=params,
        method=request.method
    )
    return response


@router.post("/tasks")
async def create_task(
        request: Request,
        api_key: Optional[str] = Depends(get_bearer_token),

        upstream_model: Optional[str] = Header(None),  # 计费名称
        upstream_base_url: Optional[str] = Header(None),
        upstream_path: Optional[str] = Header(None),
        upstream_api_key: Optional[str] = Header(None),

):
    # 获取请求体
    payload = await request.json()
    # 获取请求头
    headers = dict(request.headers)
    # 移除一些不需要转发的头部
    headers.pop('host', None)
    logger.debug(bjson(headers))
    logger.debug(bjson(payload))

    async with ppu_flow(api_key, post=upstream_model):
        response = await make_request(
            base_url=upstream_base_url,
            path=upstream_path,
            payload=payload,

            api_key=upstream_api_key,
            method=request.method
        )
        return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
