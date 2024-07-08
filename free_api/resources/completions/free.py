#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : free
# @Time         : 2024/4/25 11:18
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://free.p0.ee # 逆向画图吧

import httpx

from meutils.pipe import *
from meutils.notice.feishu import send_message
from meutils.str_utils.regular_expression import parse_url

from chatllm.schemas.openai_types import chat_completion, chat_completion_chunk
from chatllm.schemas.openai_api_protocol import ChatCompletionRequest, UsageInfo
from chatllm.utils.openai_utils import openai_response2sse, to_openai_completion_params

from openai import OpenAI, AsyncOpenAI

base_url = "https://free.p0.ee/api/auth"
model = "gpt-3.5-turbo"  # "@cf/bytedance/stable-diffusion-xl-lightning"


# Provider

class Completions(object):

    def __init__(self, ):
        self.base_url = "https://free.p0.ee/api/auth"

    def create(self, request: ChatCompletionRequest):
        provider = "/workers/image"
        if request.model.startswith(('gpt',)):
            provider = "/openai"
        elif request.model.startswith(('gemini',)):
            provider = '/gemini'

        with httpx.Client(base_url=self.base_url, timeout=20) as client:
            payload = {"endpoint": "/v1/chat/completions", **request.model_dump()}
            print(payload)

            response: httpx.Response
            with client.stream("POST", url=provider, json=payload) as response:

                for chunk in response.iter_lines():

                    print(chunk)

                # return response



if __name__ == '__main__':

    messages = [
        {
            "role": "user",
            "content": "hi"
        },
        {
            "role": "user",
            "content": "讲个故事"
        },

    ]
    request = ChatCompletionRequest(model='gpt-4', messages=messages)
    Completions().create(request)
