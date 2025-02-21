#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : search
# @Time         : 2024/11/6 11:52
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.apis.search import searxng
from meutils.llm.openai_utils import ppu_flow

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["搜索"]


@router.get("/search")
async def create_query(

        query: str,
        request: Request,

        auth: Optional[str] = Depends(get_bearer_token),
        n: Optional[int] = Query(1),  # 默认收费

):
    api_key = auth

    params = dict(request.query_params)
    params['query'] = query

    logger.debug(params)

    async with ppu_flow(api_key, post="api-search", n=n):
        return await searxng.search(**params)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
