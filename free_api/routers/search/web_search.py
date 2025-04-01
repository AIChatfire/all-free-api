#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : web_search
# @Time         : 2025/2/20 14:53
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
"""
web-search
web-search + 重排序
"""

from meutils.pipe import *
from meutils.apis.search import ark_web_search, zhipu_web_search
from meutils.llm.openai_utils import ppu_flow

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["搜索"]


@router.get("/web-search")
async def create_query(

        q: str,

        # api_key: Optional[str] = Depends(get_bearer_token),

):
    return await ark_web_search.Completions().query(q=q)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
