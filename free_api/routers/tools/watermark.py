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

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import ppu_flow
from meutils.apis import textin
from meutils.apis.baidu import bdaitpzs
from meutils.io.files_utils import to_bytes, to_url

from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header

router = APIRouter()
TAGS = ["图片编辑"]


@router.get("/watermark/remove")  # addition
async def remove_watermark(
        url: str,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    api_key = auth and auth.credentials or None

    async with ppu_flow(api_key, post="api-watermark-remove"):
        try:
            request = bdaitpzs.BDAITPZSRequest(original_url=url, thumb_url=url)
            data = await bdaitpzs.create_task(request, is_async=False, response_format="url")
            url = data['url']
            return {'code': 200,
                    'data': {
                        'file_data': '',
                        'file_type': '',
                        'result': {'image': url}
                    },
                    'msg': 'success'}
        except Exception as e:
            logger.error(e)

            file = await to_bytes(url)
            data = await textin.document_process(file, service="watermark-remove")
            return data


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
