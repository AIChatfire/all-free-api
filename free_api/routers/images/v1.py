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
from meutils.io.files_utils import to_base64

from meutils.llm.openai_utils import ppu_flow

from meutils.schemas.image_types import ImageRequest, FluxImageRequest, SDImageRequest, TogetherImageRequest
from meutils.schemas.image_types import KlingImageRequest, CogviewImageRequest, HunyuanImageRequest

from meutils.apis.siliconflow import images as siliconflow_images
from meutils.apis.together import images as together_images
from meutils.apis.chatglm import images as cogview_images
from meutils.apis.kling import images as kling_images
from meutils.llm.completions.yuanbao import Completions as hunyuan_images

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi import File, UploadFile, Query, Form, Body, Request, HTTPException, status

router = APIRouter()
TAGS = ["图片生成"]


@router.post("/images/generations")  # todo: sd3 兜底
async def generate(
        request: dict = Body(...),
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    api_key = auth and auth.credentials or None

    logger.debug(request)

    model = request.get('model', '').lower().lstrip("api-images-").lstrip("api-")
    if model.startswith(("flux.1.1", "flux1.1", "flux1.0-turbo", "flux-turbo")):
        request = TogetherImageRequest(**request)

        N = eval(request.size.replace('x', '*')) / 1024 / 1024  # 计费
        N = None

        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=N):
            response = await together_images.generate(request)
            return response

    elif model.startswith(("flux",)):
        request = FluxImageRequest(**request)

        N = eval(request.size.replace('x', '*')) / 1024 / 1024  # 计费
        N = None

        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=N):
            response = await siliconflow_images.generate(request)
            return response

    elif model.startswith(("stable-diffusion",)):
        request = SDImageRequest(**request)
        request.image = request.image and await to_base64(request.image)  # 图生图

        N = eval(request.size.replace('x', '*')) / 1024 / 1024  # 计费
        N = None

        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=N):
            response = await siliconflow_images.generate(request)
            return response

    elif model.startswith(("cogview",)):  # todo: 官方api
        request = CogviewImageRequest(**request)

        N = 1
        N = None

        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=N):
            response = await cogview_images.generate(request)
            return response

    elif model.startswith(("hunyuan", "yuanbao")):  # 默认4张
        request = HunyuanImageRequest(**request)

        N = None

        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=N):
            response = await hunyuan_images.generate(request)
            return response

    elif model.startswith(("kling",)):  # 默认4张
        request = KlingImageRequest(**request)

        N = request.n / 4
        N = None

        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=N):
            response = await kling_images.generate(request)
            return response

    else:  # 其他
        request = FluxImageRequest(**request)

        N = None

        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=N):
            response = await siliconflow_images.generate(request)
            return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
