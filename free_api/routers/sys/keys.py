#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : keys
# @Time         : 2025/12/11 17:57
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from meutils.serving.fastapi.dependencies.headers import get_headers

from meutils.decorators.contextmanagers import try_catch

# from meutils.serving.fastapi.lifespans import nacos_lifespan

from fastapi import APIRouter, Body, File, UploadFile, Header, Query, Form, Depends, Request, HTTPException, status, \
    BackgroundTasks

router = APIRouter()
TAGS = ["keys"]


@router.api_route("/{path:path}", methods=["GET", "POST"])
async def polling_key(
        path: str,
        request: Request,

        api_key: Optional[str] = Depends(get_bearer_token),

):
    params = request.query_params._dict

    if not params.get('biz'):  # 防止盗刷
        raise HTTPException(status_code=451, detail="非法操作，用户将封禁")

    payload = {}
    try:
        payload = await request.json()
    except Exception as e:
        logger.debug(e)
        form = (await request.form())._dict  # 优化数组

    data = {
        "method": request.method,
        "path": path,
        "params": params,
        "payload": payload,
        "api_key": api_key,
    }

    # logger.debug(bjson(data))

    return data


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    # app = App(lifespan=nacos_lifespan)
    app = App()

    app.include_router(router, '/v1')

    app.run()

    os.getenv("OPENAI_API_KEY_OPENAI")

"""
curl -X 'POST' \
  'http://0.0.0.0:8000/v1/xxxx?biz=openai' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer xx' \
  -d '{"key": "value"}'
"""
