#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : sd
# @Time         : 2024/7/4 08:44
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.notice.feishu import send_message as _send_message
from meutils.db.redis_db import redis_client, redis_aclient
from meutils.config_utils.lark_utils import aget_spreadsheet_values

from meutils.llm.openai_utils import to_openai_completion_params, token_encoder, token_encoder_with_cache
from meutils.schemas.image_types import ImageRequest

from openai import OpenAI, AsyncOpenAI, APIStatusError

from free_api.resources.completions.polling_openai import Completions

send_message = partial(
    _send_message,
    url="https://open.feishu.cn/open-apis/bot/v2/hook/e0db85db-0daf-4250-9131-a98d19b909a9",
    title="轮询api-keys"
)

redis_client.decode_responses = True

OpenAI.images.generate()


class Images(Completions):

    async def generate(self, request: ImageRequest):
        return await AsyncOpenAI().images.generate()

    def create(self, request: ImageRequest):
        pass



if __name__ == '__main__':
    pass
    print(arun(Completions().acreate(
        ChatCompletionRequest(model='deepseek-chat', messages=[{"role": "user", "content": "你是谁"}])
    )))
