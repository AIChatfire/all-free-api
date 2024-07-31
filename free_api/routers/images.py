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

from meutils.apis.siliconflow import api_images
from meutils.apis.kuaishou import klingai
from meutils.apis.hf import kolors

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

        image_response = await api_images.api_create_image(request)  # 自动翻译成英文
        return image_response

    elif request.model.startswith(("kling",)):  # 国际版

        kling_request = KlingaiImageRequest(
            prompt=request.prompt,
            imageCount=request.n,
            # style=request.style,  # "默认"
            aspect_ratio=request.size if request.size in {'1:1', '2:3', '3:2', '3:4', '4:3', '9:16', '16:9'} else "1:1"
        )
        images = await klingai.create_image(kling_request)
        if isinstance(images, dict):  # 异常
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=images)

        if images:
            return ImagesResponse(created=int(time.time()), data=images)
        else:
            klingai.send_message(f"SD兜底\n\n{kling_request}")

            return await api_images.api_create_image(request)

    else:  # kolors 官网死了
        try:
            image_response = await kolors.create_image(request)
            return image_response
        except Exception as e:
            image_response = await api_images.api_create_image(request)
            klingai.send_message(f"SD兜底\n\n{e}\n\n{image_response}")
            return image_response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
