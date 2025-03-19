#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : images
# @Time         : 2024/8/30 10:07
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 
# :str（默认）：匹配任何字符串，不包括斜杠
# :int：匹配整数
# :float：匹配浮点数
# :uuid：匹配 UUID 字符串


from meutils.pipe import *
from fastapi import FastAPI, HTTPException

from urllib.parse import unquote

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import ppu_flow
from meutils.apis.kuaishou import klingai_video
from meutils.config_utils.lark_utils import get_next_token_for_polling
from meutils.apis.baidu import bdaitpzs
from meutils.io.files_utils import base64_to_bytes

from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header
from fastapi.responses import StreamingResponse

router = APIRouter()
TAGS = ["图片编辑"]


@router.get("/no_watermark/{url:path}")
async def remove_watermark(url: str):
    # 解码 URL
    url = unquote(url)

    request = bdaitpzs.BDAITPZSRequest(original_url=url, thumb_url=url)
    data = await bdaitpzs.create_task(request, is_async=False)

    base64_image_string = data['picArr'][0]['src']

    # content_type, _ = base64_image_string.split(";base64,", 1)
    # logger.debug(content_type)

    image_stream = base64_to_bytes(base64_image_string)

    return StreamingResponse(io.BytesIO(image_stream))




if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
