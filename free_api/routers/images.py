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
from meutils.schemas.kuaishou_types import KlingaiImageRequest, KolorsRequest
from meutils.schemas.translator_types import DeeplxRequest

from meutils.apis.siliconflow import text_to_image
from meutils.apis.kuaishou import klingai, kolors
from meutils.apis.translator import deeplx

from openai.types import ImagesResponse

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["文生图"]


@router.post("/images/generations")
async def generate(
        request: ImageRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        base_url: Optional[str] = Query("https://api.siliconflow.cn/v1"),
):
    logger.debug(request)

    if request.model.startswith(("stable-diffusion-3",)):
        if any(i in base_url for i in {"xinghuo", "siliconflow", "cloudflare"}):  # 实际调用
            request.model = REDIRECT_MODEL.get(request.model, request.model)

        # 异步任务
        future_task = asyncio.create_task(text_to_image.create_image(request))

        # 自动翻译成英文
        request.n = 1
        request.prompt = await deeplx.translate(DeeplxRequest(text=request.prompt, target_lang="EN"))
        response = await text_to_image.create_image(request)
        data = response.get('images', [])
        data += (await future_task).get('images', [])  # 获取异步任务

        return ImagesResponse(created=int(time.time()), data=data)

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

    else:  # kolors
        kolors_request = KolorsRequest(
            prompt=request.prompt,
            imageCount=request.n,
            style=request.style,
            resolution=request.size
        )
        try:
            images = await kolors.create_image(kolors_request)
            if isinstance(images, dict):  # 异常
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=images)
            return ImagesResponse(created=int(time.time()), data=images)
        except Exception as e:
            kolors.send_message(f"Kolors失败，sd3兜底\n\n{e}")

            request.model = "stable-diffusion-3"
            return await generate(request, auth, base_url)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
