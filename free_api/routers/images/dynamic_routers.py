#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : dynamic_routers
# @Time         : 2025/5/30 15:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.llm.openai_utils import ppu_flow
from meutils.llm.openai_utils.adapters import chat_for_image
from meutils.notice.feishu import send_message_for_dynamic_router as send_message

from meutils.schemas.image_types import ImageRequest, ImageEditRequest
from meutils.schemas.openai_types import CompletionRequest

from meutils.apis.fal.images import generate as fal_generate
from meutils.apis.images.recraft import generate as recraft_generate
from meutils.apis.volcengine_apis.images import generate as volcengine_generate

from meutils.decorators.contextmanagers import try_catch, atry_catch

from meutils.serving.fastapi.dependencies.auth import get_bearer_token

from sse_starlette import EventSourceResponse

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi import File, UploadFile, Query, Form, Body, Request, HTTPException, status

router = APIRouter()
TAGS = ["Images"]


@router.post("/{dynamic_router:path}")
async def generate(
        dynamic_router: str,
        request: Request,

        api_key: Optional[str] = Depends(get_bearer_token),

        # n: Optional[int] = Query(1),  # 不计费
):
    logger.debug(dynamic_router)

    async with atry_catch(f"{dynamic_router}", api_key=api_key, callback=send_message, request=request):
        if "images/generations" in dynamic_router:  # "v1/images/generations"
            request = await request.json()
            request = ImageRequest(**request)

            response = await fal_generate(request)
            return response

        elif "images/edits" in dynamic_router:
            """
            {'prompt': 'A cute baby sea otter wearing a beret', 'model': 'dall-e-3', 'n': '1', 'size': '1024x1024', 'image': UploadFile(filename='test.png', size=24809, headers=Headers({'content-disposition': 'form-data; name="image"; filename="test.png"', 'content-type': 'image/png'})), 'mask': UploadFile(filename='test.png', size=24809, headers=Headers({'content-disposition': 'form-data; name="mask"; filename="test.png"', 'content-type': 'image/png'}))}
            """
            request = (await request.form())._dict
            logger.debug(request)

            return request

        elif "chat/completions" in dynamic_router:
            request = await request.json()
            request = CompletionRequest(**request)

            chunks = await chat_for_image(fal_generate, request)

            return EventSourceResponse(chunks)




if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
