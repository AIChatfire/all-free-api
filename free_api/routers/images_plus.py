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
from meutils.io.image import image2nowatermark_image

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

        vip: Optional[bool] = Query(True),
):
    api_key = auth and auth.credentials or None

    logger.debug(request.model_dump_json(indent=4))

    if request.image:  # 图生图
        if request.model.startswith(("kling",)):
            pass
        elif request.model.startswith(("kolors",)):
            pass

    else:  # 文生图
        if request.model.startswith(("stable-diffusion", "dreamshaper")):
            pass

        else:
            request.model = "black-forest-labs/FLUX.1-schnell"
            return await text_to_image.create(request)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
