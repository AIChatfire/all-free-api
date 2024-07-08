#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : reranker
# @Time         : 2024/7/8 09:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import ppu_flow
from meutils.schemas.jina_types import RerankerRequest

from meutils.apis.jina import rerank

from fastapi import APIRouter, Depends, BackgroundTasks

router = APIRouter()
TAGS = ["reranker"]


@router.post("/reranker")
async def create_reranker(
        request: RerankerRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token)
):
    logger.debug(request)

    api_key = auth and auth.credentials or None

    async with ppu_flow(api_key, 'ppu-01'):
        response = await rerank(request)
        return response


@router.post("/rerank")
async def create_rerank(
        request: RerankerRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token)
):
    return await create_reranker(request, auth)


@router.post("/reranking")
async def create_reranking(
        request: RerankerRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token)
):
    return await create_reranker(request, auth)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
