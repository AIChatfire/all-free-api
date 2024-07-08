#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : images
# @Time         : 2024/7/8 14:27
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.schemas.openai_types import ImageRequest
from meutils.schemas.oneapi_types import REDIRECT_MODEL
from meutils.apis.siliconflow import text_to_image

from openai.types import ImagesResponse

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

from free_api.resources.completions.polling_openai import Completions

router = APIRouter()
TAGS = ["文生图"]


@router.post("/images/generations")
async def generate(
        request: ImageRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        base_url: Optional[str] = Query("https://api.siliconflow.cn/v1"),
        feishu_url: Optional[str] = Query(None),
        redis_key: Optional[str] = Query(None),
):
    logger.debug(request)

    if any(i in base_url for i in {"xinghuo", "siliconflow", "cloudflare"}):  # 实际调用
        request.model = REDIRECT_MODEL.get(request.model, request.model)


    response = await text_to_image.create_image(request)

    return ImagesResponse(created=int(time.time()), data=response.get('images', []))


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
