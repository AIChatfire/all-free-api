#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : dynamic_routers
# @Time         : 2025/5/30 15:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : todo: 合并到 oai


from meutils.pipe import *
from meutils.io.files_utils import to_url, to_url_fal

from meutils.llm.openai_utils.adapters import chat_for_image
from meutils.notice.feishu import send_message_for_dynamic_router as send_message

from meutils.schemas.image_types import ImageRequest, ImageEditRequest
from meutils.schemas.openai_types import CompletionRequest

from meutils.apis.fal.images import generate as fal_generate
from meutils.apis.images.generations import generate

from meutils.decorators.contextmanagers import try_catch, atry_catch

from meutils.serving.fastapi.dependencies import get_headers, get_bearer_token

from sse_starlette import EventSourceResponse
from starlette.datastructures import UploadFile

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi import File, UploadFile, Query, Form, Body, Request, HTTPException, status

router = APIRouter()
TAGS = ["Images"]


@router.post("/{dynamic_router:path}")
async def create_generations(
        dynamic_router: str,
        request: Request,

        api_key: Optional[str] = Depends(get_bearer_token),

        headers: dict = Depends(get_headers),

        base_url: Optional[str] = Query(None),
):
    logger.debug(f"dynamic_router: {dynamic_router}, api_key: {api_key}")

    base_url = base_url or headers.get("x-base-url")  # 转发兼容 chat

    async with atry_catch(f"{dynamic_router}", base_url=base_url, api_key=api_key, callback=send_message,
                          request=request):

        if "images/generations" in dynamic_router:  # "v1/images/generations"
            request = await request.json()

            request = ImageRequest(**request)

            response = await generate(request, api_key=api_key, base_url=base_url)
            return response

        elif "chat/completions" in dynamic_router:
            request = await request.json()
            # logger.debug(request)

            request = CompletionRequest(**request)

            chunks = await chat_for_image(generate, request, api_key=api_key, base_url=base_url)

            if request.stream:
                return EventSourceResponse(chunks)

            return chunks


        elif "images/edits" in dynamic_router:
            """
            {'prompt': 'A cute baby sea otter wearing a beret', 'model': 'dall-e-3', 'n': '1', 'size': '1024x1024', 'image': UploadFile(filename='test.png', size=24809, headers=Headers({'content-disposition': 'form-data; name="image"; filename="test.png"', 'content-type': 'image/png'})), 'mask': UploadFile(filename='test.png', size=24809, headers=Headers({'content-disposition': 'form-data; name="mask"; filename="test.png"', 'content-type': 'image/png'}))}
            """
            form_data = await request.form()

            # logger.debug(form_data)
            # logger.debug(form_data._dict)
            #
            # logger.debug(form_data.multi_items())
            # logger.debug(form_data._list)
            #
            # logger.debug(form_data.getlist("image[]"))

            request = form_data._dict
            if images := form_data.getlist("image[]"):
                request["image"] = images
            request = ImageEditRequest(**request)  # todo: 优化

            file_object: UploadFile
            for file_object in request.image:
                image_url = await to_url_fal(file_object.file.read(), content_type=file_object.content_type)  # 国外：fal
                request.prompt = f"{request.prompt}\n{image_url}"

            request = ImageRequest(
                model=request.model,
                prompt=request.prompt,
                n=request.n,
                size=request.size,  # aspect_ratio
                response_format=request.response_format
            )

            return await generate(request, api_key)  # token

        else:
            raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED,
                                detail=f"Not implemented: {dynamic_router}")


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
