#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : images
# @Time         : 2024/8/30 10:07
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : Image edit
# :str（默认）：匹配任何字符串，不包括斜杠
# :int：匹配整数
# :float：匹配浮点数
# :uuid：匹配 UUID 字符串


from meutils.pipe import *
from fastapi import FastAPI, HTTPException

from urllib.parse import unquote

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import ppu_flow
from meutils.apis import textin
from meutils.io.files_utils import to_bytes, to_url
from meutils.config_utils.lark_utils import get_next_token_for_polling
from meutils.apis.baidu import bdaitpzs
from meutils.io.image import base64_to_bytes

from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header
from fastapi.responses import StreamingResponse

router = APIRouter()
TAGS = ["图片编辑"]


@router.get("/watermark/remove/{url:path}")  # addition
async def remove_watermark(
        url: str,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    api_key = auth and auth.credentials or None

    # 解码 URL
    # url = unquote(url)

    file = await to_bytes(url)

    async with ppu_flow(api_key, post="api-watermark-remove"):
        data = await textin.textin_fileparser(file, service="watermark-remove")

        base64_data = data['data']['result']['image']

        data['data']['result']['image'] = await to_url(base64_data)
        return data


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
