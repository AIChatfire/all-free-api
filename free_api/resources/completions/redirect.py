#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : doubao
# @Time         : 2024/8/12 15:44
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.notice.feishu import send_message as _send_message

from meutils.llm.openai_utils import to_openai_completion_params, token_encoder, token_encoder_with_cache
from meutils.schemas.openai_types import chat_completion, chat_completion_chunk, ChatCompletionRequest, CompletionUsage

from openai import OpenAI, AsyncOpenAI, APIStatusError

send_message = partial(
    _send_message,
    url="https://open.feishu.cn/open-apis/bot/v2/hook/e0db85db-0daf-4250-9131-a98d19b909a9",
    title=__name__
)


# doubao-lite-4k
# doubao-pro-4k


class Completions(object):

    def __init__(self,
                 model,
                 base_url,
                 api_key,

                 redirect_model,
                 redirect_base_url,
                 redirect_api_key,

                 threshold: int = 32000
                 ):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.redirect_client = AsyncOpenAI(base_url=redirect_base_url, api_key=redirect_api_key)

        self.model = model
        self.redirect_model = redirect_model
        self.threshold = threshold
        # self.redirect_base_url
        # self.redirect_api_key

    async def create(self, request: ChatCompletionRequest):

        if len(str(request.messages)) > self.threshold:  # 动态切模型
            request.model = self.redirect_model
            data = to_openai_completion_params(request)
            return await self.redirect_client.chat.completions.create(**data)

        try:
            request.model = self.model
            data = to_openai_completion_params(request)
            logger.debug(data)

            return await self.client.chat.completions.create(**data)
        except APIStatusError as e:
            logger.error(e)

            if e.status_code == 400:  # todo: 细分错误
                send_message(f"{e.response}\n\n{e}\n\n{request.model_dump()}")

            request.model = self.redirect_model
            data = to_openai_completion_params(request)
            return await self.redirect_client.chat.completions.create(**data)
