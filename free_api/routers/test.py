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
from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from meutils.serving.fastapi.lifespans import nacos_lifespan

from fastapi import APIRouter, File, UploadFile, Header, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["空服务"]


@router.api_route("{path:path}", methods=["GET", "POST"])
async def create_request(
        path: str,
        request: Request,
        api_key: Optional[str] = Depends(get_bearer_token),

        reasoning_stream: bool = Header(True),

):
    logger.debug(request.method)
    logger.debug(request.headers)
    logger.debug(request.url)

    logger.debug(api_key)
    logger.debug(path)

    logger.debug(reasoning_stream)


    params = request.query_params._dict

    try:
        payload = await request.json()
    except Exception as e:
        payload = (await request.body()).decode()

    form = (await request.form())._dict

    data = {
        "id": "test",
        "status": "SUBMITTED",
        "headers": dict(request.headers),
        "url": str(request.url),
        "method": request.method,
        "path": path,
        "payload": payload,
        "form": form,
        "params": params,
        **params
    }
    if isinstance(payload, dict):
        data.update(payload)

    logger.debug(bjson(data))

    return data


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App(lifespan=nacos_lifespan)

    app.include_router(router, '/v0')

    app.run()

    os.getenv("OPENAI_API_KEY_OPENAI")



