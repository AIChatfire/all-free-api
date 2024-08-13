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
from meutils.apis.siliconflow.rerankers import rerank
from meutils.schemas.siliconflow_types import RerankRequest

from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header

router = APIRouter()
TAGS = ["reranker"]


@router.post("/reranker")
async def create_reranker(
        request: RerankRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        # upstream_base_url: Optional[str] = Header(None),
        # upstream_api_key: Optional[str] = Header(None),
        # downstream_base_url: Optional[str] = Header(None),
        # background_tasks: BackgroundTasks = BackgroundTasks(),
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth and auth.credentials or None

    async with ppu_flow(api_key, post='api-reranker'):
        return await rerank(request)

    # if upstream_base_url and upstream_api_key:
    #     async with ppu_flow(upstream_api_key, base_url=upstream_base_url, post='ppu-01'):
    #         async with ppu_flow(downstream_api_key, base_url=downstream_base_url, post='ppu-01'):
    #             response = await rerank(request, jina_api_key)
    #         return response
    # else:
    #     async with ppu_flow(downstream_api_key, post='ppu-01'):
    #         response = await rerank(request, jina_api_key)
    #         return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
