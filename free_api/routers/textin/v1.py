#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : v1
# @Time         : 2025/3/23 13:04
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.llm.openai_utils import ppu_flow
from meutils.apis.textin_apis import Textin
from meutils.schemas.textin_types import WatermarkRemove

from meutils.serving.fastapi.dependencies.auth import get_bearer_token

from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header, Body

router = APIRouter()
TAGS = ["textin"]


@router.post("/{service:path}")
async def create_textin_service(
        request: dict = Body(...),
        service: str = "image/watermark_remove",

        api_key: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(bjson(request))

    if service == "image/watermark_remove":
        logger.debug(service)

        request = WatermarkRemove(**request)
        async with ppu_flow(api_key, post=f"api-textin-{service}"):
            data = await Textin().image_watermark_remove(request)
            return data


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
