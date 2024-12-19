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
from meutils.apis.together import images as together_images
from meutils.apis.chatglm import images as cogview_images
from meutils.apis.kling import images as kling_images
from meutils.llm.completions.yuanbao import Completions as hunyuan_images

from meutils.serving.fastapi.dependencies.auth import get_bearer_token

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi import File, UploadFile, Query, Form, Body, Request, HTTPException, status

router = APIRouter()
TAGS = ["图片生成"]


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

    # if model.startswith(("flux.1.1", "flux1.1", "flux1.0-turbo", "flux-turbo")):
    #     request = TogetherImageRequest(**request)
    #
    #     async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
    #         response = await together_images.generate(request)
    #         return response

    if model.startswith(("flux",)):  # flux.1.1-pro
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

    elif model.startswith(("kling",)):  # 默认4张
        request = KlingImageRequest(**request)

        n *= request.n or 1
        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
            response = await kling_images.generate(request)
            return response

    elif model.startswith(("recraftv3",)):
        request = RecraftImageRequest(**request)

        n *= request.n or 1
        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
            response = await recraft.generate(request)
            return response

    elif model.startswith(("seededit",)):  # 即梦
        from meutils.apis.jimeng import images

        request = ImageRequest(**request)

        n *= request.n or 1
        task_response = await images.create_task(request)
        for i in range(1, 10):
            await asyncio.sleep(5 / i)
            response = await images.get_task(task_response.task_id, task_response.system_fingerprint)
            if data := response.data:
                return {"data": data}

    else:  # 其他
        request = FluxImageRequest(**request)

        async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
            response = await siliconflow_images.generate(request)
            return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
