#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : free
# @Time         : 2024/11/6 18:14
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 空服务调试

from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["空服务"]


@router.post("/{path:path}")
async def create_request(
        path: str,
        request: Request,
):
    logger.debug(request.method)
    logger.debug(request.headers)
    logger.debug(request.url)

    params = request.query_params._dict
    payload = await request.json()

    data = {
        "params": params,
        "payload": payload,
    }

    logger.debug(bjson(data))

    return data


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

    os.getenv("OPENAI_API_KEY_OPENAI")
