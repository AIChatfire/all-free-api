#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : fal
# @Time         : 2025/2/19 20:25
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
from meutils.pipe import *
from meutils.llm.openai_utils import ppu_flow
from meutils.notice.feishu import send_message_for_images

from meutils.schemas.image_types import ImageRequest, RecraftImageRequest

from meutils.apis.fal.images import generate as fal_generate
from meutils.apis.images.recraft import generate as recraft_generate
from meutils.apis.volcengine_apis.images import generate as volcengine_generate

from meutils.decorators.contextmanagers import try_catch, atry_catch

from meutils.serving.fastapi.dependencies.auth import get_bearer_token

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi import File, UploadFile, Query, Form, Body, Request, HTTPException, status

router = APIRouter()
TAGS = ["图片生成"]


@router.post("/{biz}/v1/images/generations")
async def generate(
        biz: str,
        request: ImageRequest,
        api_key: Optional[str] = Depends(get_bearer_token),

        n: Optional[int] = Query(1),  # 默认收费
):
    async with atry_catch(f"{biz}", api_key=api_key, callback=send_message_for_images, request=request):
        if biz == 'fal':
            async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
                response = await fal_generate(request)
                return response

        elif biz == 'recraft':
            n = n and request.n or 0
            async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
                request = RecraftImageRequest(**request.model_dump())
                response = await recraft_generate(request)
                return response

        elif biz == 'volcengine':
            n = request.n
            async with ppu_flow(api_key, post=f"api-images-{request.model}", n=n):
                response = await volcengine_generate(request, token=api_key)
                return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
