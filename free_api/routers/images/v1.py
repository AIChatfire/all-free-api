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
from meutils.schemas.image_types import ImageRequest, FluxImageRequest, SDImageRequest, TogetherImageRequest, \
    RecraftImageRequest

from meutils.schemas.image_types import KlingImageRequest, CogviewImageRequest, HunyuanImageRequest

from meutils.apis.images import deepinfra, recraft
from meutils.apis.siliconflow import images as siliconflow_images

from meutils.apis.chatglm import images as cogview_images
from meutils.apis.kling import images as kling_images
from meutils.apis.gitee.images import kolors
from meutils.apis.hailuoai import images as hailuo_images

from meutils.llm.completions.yuanbao import Completions as hunyuan_images

from meutils.serving.fastapi.dependencies.auth import get_bearer_token

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi import File, UploadFile, Query, Form, Body, Request, HTTPException, status

router = APIRouter()
TAGS = ["Images"]


@router.post("/images/generations")  # todo: sd3 兜底
async def generate(
        request: dict = Body(..., examples=[{"model": "recraftv3", "prompt": "画条狗"}]),
        api_key: Optional[str] = Depends(get_bearer_token),

        redirect_flux: Optional[bool] = Query(None),

        n: Optional[int] = Query(1),  # 默认收费
):
    logger.debug(request)

    model = request.get('model', '').lower().removeprefix("api-images-").removeprefix("api-")

    if model.startswith("flux") and redirect_flux:  # 重定向 flux
        request["model"] = "flux"

    if model.startswith(("kolors",)):  # kolors 1.0
        request = kolors.KolorsRequest(**request)
        async with ppu_flow(api_key, post="kolors", n=n):
            response = await kolors.generate(request)
            return response

    elif model.startswith(("flux",)):  # flux.1.1-pro
        request = FluxImageRequest(**request)

        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
            response = await siliconflow_images.generate(request)
            return response

    elif model.startswith(("stable-diffusion",)):
        request = SDImageRequest(**request)
        request.image = request.image and await to_base64(request.image)  # 图生图

        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
            response = await siliconflow_images.generate(request)
            return response

    elif model.startswith(("cogview",)):  # todo: 官方api
        request = CogviewImageRequest(**request)

        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
            response = await cogview_images.generate(request)
            return response

    elif model.startswith(("hunyuan", "yuanbao")):  # 默认4张
        request = HunyuanImageRequest(**request)

        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
            response = await hunyuan_images.generate(request)
            return response

    elif model.startswith(("hailuo", "minimax")):
        request = ImageRequest(**request)

        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
            response = await hailuo_images.generate(request)
            return response

    elif model.startswith(("kling",)):  # 默认4张
        request = KlingImageRequest(**request)

        n *= request.n or 1
        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
            response = await kling_images.generate(request)
            return response




    # elif model.startswith(("kolors-virtual-try-on",)):
    #     request = ImageRequest(**request)
    #
    #     n *= request.n or 1
    #     async with ppu_flow(api_key, post="kolors-virtual-try-on", n=n):
    #         response = await kolors_virtual_try_on.generate(request)
    #         return response

    elif model.startswith(("recraft",)):
        request = RecraftImageRequest(**request)

        n *= request.n or 1
        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
            response = await recraft.generate(request)
            return response

    elif model.startswith(("seededit",)):  # 即梦
        from meutils.apis.jimeng import images as jimeng_images

        request = ImageRequest(**request)

        return await jimeng_images.generate(request)

    elif model.startswith(("gemini",)):  # 即梦
        from meutils.apis.google.chat import Completions

        request = ImageRequest(**request)

        return await Completions().generate(request)

    else:  # 其他
        request = FluxImageRequest(**request)
        request.model = "black-forest-labs/FLUX.1-schnell"

        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
            response = await siliconflow_images.generate(request)
            return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
