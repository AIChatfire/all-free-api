#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : dynamic_routers
# @Time         : 2025/5/30 15:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : todo: 合并到 oai
import os

from meutils.pipe import *
from meutils.io.files_utils import to_url, to_url_fal, to_png, to_base64

from meutils.llm.openai_utils.adapters import chat_for_image
from meutils.notice.feishu import send_message_for_dynamic_router as send_message

from meutils.schemas.image_types import ImageRequest, ImageEditRequest
from meutils.schemas.openai_types import CompletionRequest

from meutils.apis.images.generations import generate

from meutils.decorators.contextmanagers import try_catch, atry_catch

from meutils.serving.fastapi.dependencies import get_headers, get_bearer_token

from sse_starlette import EventSourceResponse
from starlette.datastructures import UploadFile

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi import File, Query, Form, Body, Request, HTTPException, status

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

    base_url = base_url or headers.get("x-base-url")
    http_url = headers.get("http-url")

    async with atry_catch(f"{dynamic_router}", base_url=base_url, api_key=api_key, callback=send_message,
                          request=request):

        if "images/generations" in dynamic_router:  # "v1/images/generations"
            request = await request.json()

            request = ImageRequest(**request)

            response = await generate(request, api_key=api_key, base_url=base_url, http_url=http_url)

            if not response:
                raise HTTPException(status_code=500, detail=f"image response is null")

            return response

        elif "chat/completions" in dynamic_router:
            # logger.debug(headers.get("x-nochat"))
            # if headers.get("x-nochat"): raise HTTPException(status_code=500, detail=f"SkipChat")

            request = await request.json()
            # logger.debug(request)

            request = CompletionRequest(**request)

            # logger.debug(request)

            chunks = await chat_for_image(
                generate, request,
                api_key=api_key,
                base_url=base_url,
                http_client=http_client
            )

            if request.stream:
                return EventSourceResponse(chunks)

            return chunks


        elif "images/edits" in dynamic_router: # todo 优化 form
            """
            {'prompt': 'A cute baby sea otter wearing a beret', 'model': 'dall-e-3', 'n': '1', 'size': '1024x1024', 'image': UploadFile(filename='test.png', size=24809, headers=Headers({'content-disposition': 'form-data; name="image"; filename="test.png"', 'content-type': 'image/png'})), 'mask': UploadFile(filename='test.png', size=24809, headers=Headers({'content-disposition': 'form-data; name="mask"; filename="test.png"', 'content-type': 'image/png'}))}
            """
            form_data = await request.form()

            # logger.debug(form_data)
            # logger.debug(form_data._dict)

            # logger.debug(form_data.multi_items())
            # logger.debug(form_data._list)
            # 93 - [('image', UploadFile(filename='edit1.webp', size=236232, headers=Headers(
            #     {'content-disposition': 'form-data; name="image"; filename="edit1.webp"',
            #      'content-type': 'image/webp'}))), ('image', UploadFile(filename='edit2.webp', size=134912,
            #                                                             headers=Headers({
            #                                                                                 'content-disposition': 'form-data; name="image"; filename="edit2.webp"',
            #                                                                                 'content-type': 'image/webp'}))),
            #       ('prompt', '将小黄鸭放到T恤上'), ('model', 'doubao-seedream-4-0-250828')]

            # logger.debug(form_data.getlist("image[]"))

            request = form_data._dict
            # if images := form_data.getlist("image[]"):  # 数组
            #     request["image"] = images
            files = []
            for k, v in form_data.multi_items():  # images
                # logger.debug(type(v))
                if isinstance(v, UploadFile):
                    files.append(v)

            request["image"] = [file_object.file.read() for file_object in files]  # file_objects

            request = ImageEditRequest(**request)  # todo: 优化

            # for file_object in request.image:  # 并发 + b64
            #     if request.model.startswith("fal-"):  # 国外：fal
            #         # image_url = await to_url_fal(file_object.file.read(), content_type="image/png")
            #         image_url = await to_url_fal(file_object.file.read(), content_type=file_object.content_type)
            #         image_urls.append(image_url)
            #
            #     else:
            #         image_url = await to_url(file_object.file.read(), content_type=file_object.content_type)
            #         image_urls.append(image_url)

            # todo 是不是直接传 b64 就可以了， 逻辑放在generate 中
            # if request.model.startswith("fal-"):  # 国外：fal
            #     image_urls = await to_url_fal(request.image, content_type="image/png")  # file_object.content_type
            # elif request.model.startswith(("doubao-seed",)):  # todo: 拓展
            #     # image_urls = await to_png(request.image, response_format='b64_json')  # 临时方案
            #     image_urls = request.image
            # else:  # 默认转 url
            #     image_urls = await to_url(request.image, filename='.png', content_type="image/png")

            if request.model.startswith(("doubao-seed",)):  # todo: 拓展
                # image_urls = await to_png(request.image, response_format='b64_json')  # 临时方案
                image_urls = request.image
            else:  # 默认转 url
                image_urls = await to_url(request.image, filename='.png', content_type="image/png")

            request = ImageRequest(
                model=request.model,
                prompt=request.prompt,
                image=image_urls,
                n=request.n,
                size=request.size,  # aspect_ratio
                response_format=request.response_format
            )

            response = await generate(request, api_key=api_key, base_url=base_url, http_client=http_client)
            if not response:
                raise HTTPException(status_code=500, detail=f"image response is null")
            return response

        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Not implemented: {dynamic_router}")


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

"""

curl --location --request POST 'http://0.0.0.0:8000/v1/images/generations' \
--header 'User-Agent: Apifox/1.0.0 (https://apifox.com)' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer sk_f1ScGw5Q2RxkNUk6fFSX32CtzSokjtsOJmZWLVveLHA' \
--data-raw '{
  "model": "doubao-seedream-4-0-250828",
  "n": 1,
  "prompt": "生成3张女孩和奶牛玩偶在游乐园开心地坐过山车的图片，涵盖早晨、中午、晚上",
  "size": "1024x1024"
  
}'
"""
