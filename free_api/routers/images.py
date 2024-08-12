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

from meutils.apis.siliconflow import api_images, flux
from meutils.apis.kuaishou import klingai
from meutils.apis.hf import kolors

from meutils.notice.feishu import send_message

from openai.types import ImagesResponse

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["文生图"]


@router.post("/images/generations")  # todo: sd3 兜底
async def generate(
        request: ImageRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        base_url: Optional[str] = Query("https://api.siliconflow.cn/v1"),
):
    logger.debug(request.model_dump_json(indent=4))

    image_response = None
    try:
        if request.model.startswith(("stable-diffusion-3",)):
            request.model = REDIRECT_MODEL.get(request.model, request.model)
            image_response = await api_images.api_create_image(request)

        elif request.model.startswith(("flux-pro-max",)):
            request.is_nsfw = False  # 不审核
            request.nsfw_level = "3"  # 不审核
            image_response = await flux.create_image(request)

        elif request.model.startswith(("flux-pro",)):
            image_response = await flux.create_image(request)

        elif request.model.startswith(("flux-dev",)):  # 逆向
            request.model = "black-forest-labs/FLUX.1-schnell"
            image_response = await api_images.create_image(request)

        elif request.model.startswith(("kolors",)):
            image_response = await kolors.create_image(request)

        elif request.model.startswith(("kling",)):
            kling_request = KlingaiImageRequest(
                prompt=request.prompt,
                imageCount=request.n,
                # style=request.style,  # "默认"
                aspect_ratio=request.size if request.size in {'1:1', '2:3', '3:2', '3:4', '4:3', '9:16',
                                                              '16:9'} else "1:1"
            )
            images = await klingai.create_image(kling_request)
            image_response = ImagesResponse(created=int(time.time()), data=images)

    except Exception as e:
        send_message(f"flux兜底：{e}", title=__name__)
        # todo：触发内容监控
        # https://oss.ffire.cc/files/jin.webp

    return image_response or await api_images.api_create_image(request)  # 自动翻译成英文


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
