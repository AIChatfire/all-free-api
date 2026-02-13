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
from meutils.io.files_utils import to_url, to_url_fal, to_png, to_base64, do_file_data

from meutils.llm.openai_utils.adapters import chat_for_image
from meutils.notice.feishu import send_message_for_dynamic_router as send_message

from meutils.schemas.image_types import ImageRequest, ImageEditRequest
from meutils.schemas.openai_types import CompletionRequest

from meutils.apis.images.generations import generate

from meutils.decorators.contextmanagers import try_catch, atry_catch

from meutils.serving.fastapi.dependencies import get_headers, get_bearer_token
from meutils.serving.fastapi.utils import form_to_dict

from sse_starlette import EventSourceResponse
from starlette.datastructures import UploadFile as _UploadFile

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
    backup_api_key = headers.get("x-backup-api-key")
    base_url = base_url or headers.get("x-base-url")
    http_url = headers.get("http-url")
    input_reference_format = headers.get("input-reference-format") or ""

    logger.debug(f"\n\ndynamic_router/base_url/api_key: \n{dynamic_router}\n{base_url}\n{api_key}\n\n")

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
                http_url=http_url
            )

            if request.stream:
                return EventSourceResponse(chunks)

            return chunks


        elif "images/edits" in dynamic_router:  # todo 通用化
            """
            {'prompt': 'A cute baby sea otter wearing a beret', 'model': 'dall-e-3', 'n': '1', 'size': '1024x1024', 'image': UploadFile(filename='test.png', size=24809, headers=Headers({'content-disposition': 'form-data; name="image"; filename="test.png"', 'content-type': 'image/png'})), 'mask': UploadFile(filename='test.png', size=24809, headers=Headers({'content-disposition': 'form-data; name="mask"; filename="test.png"', 'content-type': 'image/png'}))}
            """

            formdata = await request.form()
            formdata = form_to_dict(formdata)
            input_reference, mask = formdata.pop("image", None), formdata.pop("mask", None)

            logger.debug(f"input_reference: {input_reference}, mask: {mask}")

            request = ImageRequest(**formdata)
            request.image = await do_file_data(input_reference, input_reference_format)

            logany(request)

            response = await generate(request, api_key=api_key, base_url=base_url, http_url=http_url)
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
