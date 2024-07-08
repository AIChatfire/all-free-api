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
from meutils.config_utils.lark_utils import get_next_token_for_polling
from meutils.apis.jina import rerank

from fastapi import APIRouter, Depends, BackgroundTasks, Query

router = APIRouter()
TAGS = ["reranker"]


@router.post("/{upstream_base_url}/{upstream_api_key}/{downstream_base_url}/reranker")
async def create_reranker_plus(
        upstream_base_url: str,
        upstream_api_key: str,
        downstream_base_url: str,
        request: RerankerRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        feishu_url: Optional[str] = Query("https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=seZj2f"),
        background_tasks: BackgroundTasks = BackgroundTasks(),
):
    logger.debug(request)
    logger.debug(feishu_url)
    jina_api_key = await get_next_token_for_polling(feishu_url=feishu_url)

    upstream_base_url = f"https://{upstream_base_url}/v1"
    downstream_base_url = f"https://{downstream_base_url}/v1"
    downstream_api_key = auth and auth.credentials or None
    async with ppu_flow(upstream_api_key, base_url=upstream_base_url, post='ppu-01'):
        async with ppu_flow(downstream_api_key, base_url=downstream_base_url, post='ppu-01'):
            response = await rerank(request, jina_api_key)
            return response


@router.post("/reranker")
async def create_reranker(
        request: RerankerRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        feishu_url: Optional[str] = Query("https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=seZj2f"),
        background_tasks: BackgroundTasks = BackgroundTasks(),
):
    logger.debug(request)
    logger.debug(feishu_url)
    jina_api_key = await get_next_token_for_polling(feishu_url=feishu_url)

    downstream_api_key = auth and auth.credentials or None
    async with ppu_flow(downstream_api_key, post='ppu-01'):
        response = await rerank(request, jina_api_key)
        return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
