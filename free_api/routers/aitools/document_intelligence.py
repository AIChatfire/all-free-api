#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : images
# @Time         : 2024/8/30 10:07
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : Image edit
# :str（默认）：匹配任何字符串，不包括斜杠
# :int：匹配整数
# :float：匹配浮点数
# :uuid：匹配 UUID 字符串


from meutils.pipe import *

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import ppu_flow
from meutils.apis import textin
from meutils.io.files_utils import to_bytes

from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header, Body

router = APIRouter()
TAGS = ["文档智能"]


@router.post("/v1/{service}")  # addition
async def document_process(
        service: str,
        kwargs: dict = Body(),
        response_format: str = Query("url"),
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    api_key = auth and auth.credentials or None

    logger.debug(kwargs)

    file = await to_bytes(kwargs.pop('file', None) or kwargs.pop('image'))

    async with ppu_flow(api_key, post=f"api-{service}".replace('_', '-')):
        if service == 'audio-to-text':
            pass
        else:
            data = await textin.document_process(file, service=service, response_format=response_format, **kwargs)
        return data


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
