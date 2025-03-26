#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : reader
# @Time         : 2025/3/26 18:36
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.apis.jina import url_reader
from meutils.llm.openai_utils import ppu_flow

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks
from fastapi.responses import PlainTextResponse

router = APIRouter()
TAGS = ["url"]


@router.get("/reader/{url:path}")
async def read(
        url: str,

        # api_key: Optional[str] = Depends(get_bearer_token),

):
    # async with ppu_flow(api_key, post="api-search", n=n):
    #     return await searxng.search(**params)

    _ = await url_reader(url)
    return PlainTextResponse(_)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
