#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : news
# @Time         : 2024/9/10 09:36
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://tophub.today/

from meutils.pipe import *
from meutils.request_utils.crawler import Crawler

from meutils.llm.openai_utils import ppu_flow

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header

router = APIRouter()
TAGS = ["热榜"]


@router.get("/news/{biz}")
@alru_cache(ttl=30)
async def translate(
        biz: str = "baidu",
        # auth: Optional[str] = Depends(get_bearer_token),
):
    # api_key = auth

    if biz == "baidu":
        url = "https://top.baidu.com/board?tab=realtime"

        _ = Crawler(url).xpath('//*[@id="sanRoot"]/main/div[2]/div/div[2]/div[*]/div[2]/a/div[1]//text()')
        _ = [f"{i}. {news}" for i, news in enumerate(_)]
        return "\n".join(_)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
