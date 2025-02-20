#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : fal
# @Time         : 2025/2/19 20:25
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
from meutils.pipe import *
from meutils.llm.openai_utils import ppu_flow
from meutils.schemas.image_types import ImageRequest

from meutils.apis.fal.images import generate as fal_generate
from meutils.apis.images.edits import edit_image

from meutils.serving.fastapi.dependencies.auth import get_bearer_token

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi import File, UploadFile, Query, Form, Body, Request, HTTPException, status

router = APIRouter()
TAGS = ["图片生成"]


@router.post("/images/generations")
async def generate(
        request: ImageRequest,
        api_key: Optional[str] = Depends(get_bearer_token),

        n: Optional[int] = Query(1),  # 默认收费
):
    logger.debug(request)

    n = n and request.n or 0
    async with ppu_flow(api_key, post=f"api-images-edits-{request.model}", n=n):
        response = await fal_generate(request)
        return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
