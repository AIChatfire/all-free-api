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
from meutils.schemas.kuaishou_types import KlingaiImageRequest

from meutils.apis.siliconflow import text_to_image
from meutils.apis.kuaishou import klingai

from openai.types import ImagesResponse

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

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

    if request.model.startswith(("stable-diffusion-3",)):
        if any(i in base_url for i in {"xinghuo", "siliconflow", "cloudflare"}):  # 实际调用
            request.model = REDIRECT_MODEL.get(request.model, request.model)

        response = await text_to_image.create_image(request)

        return ImagesResponse(created=int(time.time()), data=response.get('images', []))

    elif request.model.startswith(("kling",)):

        request = KlingaiImageRequest(
            prompt=request.prompt,
            imageCount=request.n,
            # style=request.style,  # "默认"
            aspect_ratio=request.size if request.size in {'1:1', '2:3', '3:2', '3:4', '4:3', '9:16', '16:9'} else "1:1"
        )
        images = await klingai.create_image(request)
        if isinstance(images, dict):  # 异常
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=images)

        return ImagesResponse(created=int(time.time()), data=images)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
