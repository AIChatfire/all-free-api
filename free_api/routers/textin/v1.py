#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : v1
# @Time         : 2025/3/23 13:04
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.llm.openai_utils import ppu_flow
from meutils.apis.textin_apis import Textin
from meutils.schemas.textin_types import WatermarkRemove, PdfToMarkdown, CropEnhanceImage

from meutils.serving.fastapi.dependencies.auth import get_bearer_token

from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header, Body, Request

router = APIRouter()
TAGS = ["textin"]


@router.post("/{service:path}")
async def create_textin_service(
        request: Request,

        service: str = "image/watermark_remove",

        api_key: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(service)

    logger.debug(bjson(request))

    params = request.query_params._dict
    request = await request.json()

    textin = Textin()
    if service == "image/watermark_remove":
        request = WatermarkRemove(**request)
        async with ppu_flow(api_key, post=f"api-textin-{service}"):
            data = await textin.image_watermark_remove(request)
            return data

    elif service == "pdf_to_markdown":
        request = PdfToMarkdown(**request)
        async with ppu_flow(api_key, post=f"api-textin-{service}"):
            data = await textin.__getattribute__(service.replace("/", "_"))(request, params)
            return data

    elif service == "crop_enhance_image":
        request = CropEnhanceImage(**request)
        async with ppu_flow(api_key, post=f"api-textin-{service}"):
            data = await textin.__getattribute__(service.replace("/", "_"))(request, params)
            return data


"""

curl -X 'POST' \
  'http://0.0.0.0:8000/v1/image%2Fwatermark_remove' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer sk-iPNbgHSRkQ9VUb6iAcCa7a4539D74255A6462d29619d65199' \
  -d '{"image": "https://oss.ffire.cc/files/sese1.jpg","response_format": "url"}'
  

curl -X 'POST' \
  'http://0.0.0.0:8000/v1/pdf_to_markdown' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer sk-iPNbgHSRkQ9VUb6iAcCa7a4539D74255A6462d29619d65199' \
  -d '{"data": "https://s3.ffire.cc/files/pdf_to_markdown.jpg","response_format": "url"}'
  
  
curl -X 'POST' \
  'http://0.0.0.0:8000/v1/crop_enhance_image' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer sk-WEmN6rbcmEu5jRUT5c6b2d672119435c999d308bCc124009' \
  -d '{"data": "https://s3.ffire.cc/files/pdf_to_markdown.jpg","response_format": "url"}'
  
  
curl -X 'POST' \
  'https://api.chatfire.cn/textin/v1/crop_enhance_image' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer sk-WEmN6rbcmEu5jRUT5c6b2d672119435c999d308bCc124009' \
  -d '{"data": "https://s3.ffire.cc/files/pdf_to_markdown.jpg","response_format": "url"}'                 
                    
"""

if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
