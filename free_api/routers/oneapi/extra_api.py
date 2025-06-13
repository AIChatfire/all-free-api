#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : extra_api
# @Time         : 2024/9/18 13:45
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.notice.feishu import send_message

from meutils.llm.openai_utils import create_chat_completion_chunk

from meutils.schemas.openai_types import CompletionRequest, chat_completion, chat_completion_chunk, \
    chat_completion_chunk_stop

from meutils.schemas.image_types import ImageRequest, ImagesResponse

from meutils.apis.oneapi.user import get_user, get_api_key_log
from meutils.apis.oneapi.channel import ChannelInfo, create_or_update_channel

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body

router = APIRouter()
TAGS = ["oneapi"]


@router.get("/token")
async def get_user_info(
        api_key: Optional[str] = Depends(get_bearer_token),
):
    data = await get_api_key_log(api_key)
    if data and (user_id := data[0]['user_id']):
        if data := await get_user(user_id):
            data['data']['access_token'] = '🔥chatfire'
            return data


@router.post("/channel")
async def create_channel(
        request: ChannelInfo,
        api_key: Optional[str] = Depends(get_bearer_token),
        headers: dict = Depends(get_headers),
):
    upstream_base_url = headers.get('upstream-base-url')
    upstream_api_key = headers.get('upstream-api-key')

    if "volc" in request.base_url:  # 火山渠道
        from meutils.apis.volcengine_apis.videos import get_valid_token

        token = await get_valid_token()
        request.key = token

    response = await create_or_update_channel(request, upstream_base_url, upstream_api_key)
    response['request'] = request
    return response


@router.post("/billing/v1/{dynamic_router:path}")  # 动态计费
async def chat_completions(
        dynamic_router: str,  # chat/completions

        request: dict,

):
    if "chat/completions" in dynamic_router:
        request = CompletionRequest(**request)

        if request.stream:
            chat_completion_chunk.usage = request.usage

            def gen():

                yield chat_completion_chunk
                yield chat_completion_chunk_stop.model_dump_json()
                yield "[DONE]"  # 兼容标准格式

            return EventSourceResponse(gen())
        else:
            chat_completion.usage = request.usage

            return chat_completion


    elif "images/generations" in dynamic_router:
        request = ImageRequest(**request)

        return ImagesResponse(usage=request.usage)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
