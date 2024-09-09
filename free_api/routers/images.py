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
from meutils.config_utils.lark_utils import get_next_token_for_polling
from meutils.llm.openai_utils import to_openai_images_params
from meutils.io.image import base64_to_url, image2nowatermark_image

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.schemas.openai_types import ImageRequest
from meutils.schemas.oneapi_types import REDIRECT_MODEL
from meutils.schemas.kuaishou_types import KlingaiImageRequest, KolorsRequest

from meutils.apis.kuaishou import klingai
from meutils.apis.hf import kolors
from meutils.apis.ideogram import ideogram_images
from meutils.apis.siliconflow import text_to_image, image_to_image

from openai.types import ImagesResponse
from openai import AsyncClient
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
    # return await text_to_image.create(request)

    if request.model.startswith(("stable-diffusion", "dreamshaper")) and not request.url:
        request.model = REDIRECT_MODEL.get(request.model, request.model)
        image_response = await text_to_image.create(request)
        return image_response

    elif request.model.startswith(("flux-pro",)):
        request.model = "black-forest-labs/FLUX.1-dev"
        request.model = "black-forest-labs/FLUX.1-schnell"

        if request.size in {'1024x1024', '1:1'}:
            request.size = "1366x1366"
        image_response = await text_to_image.create(request)
        return image_response

    elif request.model.startswith(("flux-dev",)):
        request.model = "black-forest-labs/FLUX.1-dev"
        request.model = "black-forest-labs/FLUX.1-schnell"

        image_response = await text_to_image.create(request)
        return image_response

    elif request.model.startswith(("kolors",)):
        try:
            image_response = await kolors.create_image(request)
        except Exception as e:
            logger.error(e)
            request.model = "black-forest-labs/FLUX.1-schnell"
            image_response = await text_to_image.create(request)
        return image_response

    elif request.model.startswith(("ideogram",)):
        request.model = "V_1_5" if 'pro' in request.model else "V_0_3"
        image_response = await ideogram_images.create(request)
        return image_response

    elif request.model.startswith(("kling",)):  # 支持图生图
        kling_request = KlingaiImageRequest(
            prompt=request.prompt,
            imageCount=request.n,
            # style=request.style,  # "默认"

            url=request.url,  # 垫图

            aspect_ratio=request.size if request.size in {'1:1', '2:3', '3:2', '3:4', '4:3', '9:16',
                                                          '16:9'} else "1:1"
        )
        try:
            images = await klingai.create_image(kling_request)
            image_response = ImagesResponse(created=int(time.time()), data=images)
        except Exception as e:
            logger.error(e)
            request.model = "black-forest-labs/FLUX.1-schnell"
            image_response = await text_to_image.create(request)

        return image_response

    elif request.model.startswith(('step',)):  # 转存： todo check api-key

        FEISHU_URL = "https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=KVClcs"
        request.response_format = 'b64_json'

        api_key = await get_next_token_for_polling(FEISHU_URL)
        response = await AsyncClient(
            api_key=api_key,
            base_url='https://api.stepfun.com/v1',
        ).images.generate(**to_openai_images_params(request))
        # 正方形：256x256, 512x512, 768x768, 1024x1024；长方形（16:9）：1280x800, 800x1280。

        response.data = [{"url": await base64_to_url(image.b64_json)} for image in response.data]
        return response

    elif request.url:  # 支持图生图：只支持几个
        request.model = REDIRECT_MODEL.get(request.model, request.model)  # todo 完善
        request.model = "TencentARC/PhotoMaker"
        return await image_to_image.create(request)

    elif request.model.startswith(('cogview',)):  # 去水印
        response = await AsyncClient().images.generate(
            model='cogview-3',
            prompt=request.prompt,
        )

        response.data[0].url = image2nowatermark_image(response.data[0].url)
        return response

    else:
        request.model = "black-forest-labs/FLUX.1-schnell"
        return await text_to_image.create(request)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
