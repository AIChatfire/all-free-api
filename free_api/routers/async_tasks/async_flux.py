#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : async_flux
# @Time         : 2025/6/21 18:45
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
"""
1. 复用flux的异步任务

2. curl 'https://api.bfl.ml/v1/get_result?id='

3. 既然是完全透传 也可以当做其他任务用一下

"""

from meutils.pipe import *
from meutils.apis.utils import make_request

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi import File, UploadFile, Header, Query, Form, Body, Request

router = APIRouter()
TAGS = ["异步任务"]


@router.get("/{path:path}")
async def get_task(
        request: Request,
        path: str = "get_result",  # flux

        headers: dict = Depends(get_headers),
        api_key: Optional[str] = Depends(get_bearer_token),
):
    upstream_method = headers.get('upstream_method') or request.method
    upstream_base_url = headers.get('upstream_base_url')
    upstream_api_key = headers.get('upstream_api_key') or api_key
    upstream_get_path = headers.get('upstream_get_path')
    upstream_post_path = headers.get('upstream_post_path')

    params = dict(request.query_params)
    task_id = params.get('id') or params.get('task_id') or params.get('request_id')
    upstream_params = dict(zip(["id", "task_id", "request_id"], [task_id] * 66))

    if upstream_method == 'POST':  # todo
        upstream_path = upstream_post_path
        payload = {}
    else:
        upstream_path = upstream_get_path

    response = await make_request(
        base_url=upstream_base_url,
        api_key=upstream_api_key,
        headers=headers,

        path=upstream_path,

        params=upstream_params,
        method=upstream_method
    )
    # todo: 适配 oneapi tasks
    # if response.get('status') == 'success':
    #     pass
    return response


@router.post("/{model:path}")
async def create_task(
        request: Request,
        model: str,  # response_model

        headers: dict = Depends(get_headers),
        api_key: Optional[str] = Depends(get_bearer_token),
):
    # request_model: minimax-hailuo-02
    # response_model: minimax-hailuo-02-6s-768p minimax-hailuo-02-6s-1080p

    upstream_base_url = headers.get('upstream_base_url')
    upstream_api_key = headers.get('upstream_api_key') or api_key
    upstream_post_path = headers.get('upstream_post_path')

    response = await make_request(
        base_url=upstream_base_url,
        api_key=upstream_api_key,
        headers=headers,

        path=upstream_post_path,

        method=request.method
    )
    return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
