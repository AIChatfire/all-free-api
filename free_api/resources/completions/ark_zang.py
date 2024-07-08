#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : ark_completions
# @Time         : 2024/5/16 09:50
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.apis.niutrans import translate

from chatllm.schemas.openai_api_protocol import ChatCompletionRequest
from chatllm.schemas.openai_types import chat_completion, chat_completion_chunk as _chat_completion_chunk

from chatllm.utils.openai_utils import to_openai_completion_params

from openai import OpenAI, AsyncOpenAI


class Completions(object):
    def __init__(self, api_key=None):
        api_key = self.get_and_update_api_key(resource_ids=list(self.endpoint_map.values()))

        params = dict(
            api_key=api_key,
            base_url=os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
            max_retries=1,
        )
        # 如果这一步就报错呢
        self.client = OpenAI(**params)
        self.aclient = AsyncOpenAI(**params)

    def create(self, request: ChatCompletionRequest):
        request.model = self.endpoint_map.get(request.model, "ep-20240515062545-nnq8b")

        data = to_openai_completion_params(request)
        return self.client.chat.completions.create(**data)

    async def acreate(self, request: ChatCompletionRequest, **kwargs):
        request.model = self.endpoint_map.get(request.model, "ep-20240515062545-nnq8b")
        request.last_content = translate(request.last_content, 'auto', 'zh')  # 藏语翻译成中文
        # request.last_content = translate(request.last_content, 'auto', 'ti')
        logger.debug(request)

        if request.stream:
            chunk = f"""> {request.last_content}\n\n"""
            chat_completion_chunk = _chat_completion_chunk.model_copy(deep=True)
            chat_completion_chunk.choices[0].delta.content = chunk
            yield chat_completion_chunk

            request.messages[-1]['content'] = request.last_content
            data = to_openai_completion_params(request)
            chunks = await self.aclient.chat.completions.create(**data)
            content = ""
            async for chunk in chunks:  # 异步迭代
                yield chunk
                content += chunk.choices[0].delta.content

            content = translate(content, 'auto', 'ti')  # 中文翻译成藏语
            chunk = f"""\n\n---\n{content}\n"""
            chat_completion_chunk.choices[0].delta.content = chunk
            yield chat_completion_chunk
            # 结束标识
            chat_completion_chunk.choices[0].delta.content = ""
            chat_completion_chunk.choices[0].finish_reason = "stop"
            yield chat_completion_chunk

        else:
            data = to_openai_completion_params(request)
            yield await self.aclient.chat.completions.create(**data)

    @staticmethod
    @ttl_cache(ttl=15 * 24 * 3600)
    def get_and_update_api_key(resource_ids):
        """pip install volcengine-python-sdk --no-deps -U"""
        import volcenginesdkcore
        import volcenginesdkark
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = os.getenv("ARK_ACCESS_KEY")
        configuration.sk = os.getenv("ARK_SECRET_ACCESS_KEY")
        configuration.region = "cn-beijing"

        # set default configuration
        volcenginesdkcore.Configuration.set_default(configuration)

        # use global default configuration
        api_instance = volcenginesdkark.ARKApi()

        # for endpoint in endpoint_map.values():
        get_api_key_request = volcenginesdkark.GetApiKeyRequest(
            duration_seconds=30 * 24 * 3600,  # 有效期
            resource_type="endpoint",
            resource_ids=resource_ids
            # resource_ids=list(endpoint_map.values()),
            # resource_ids=["ep-20240515062545-nnq8b"]
        )

        resp = api_instance.get_api_key(get_api_key_request)

        return resp.api_key

    @property
    def endpoint_map(self):
        return {
            "doubao-lite-128k": "ep-20240515062839-jsvtz",
            "doubao-lite-32k": "ep-20240515062431-rkhfp",
            "doubao-lite-4k": "ep-20240515062545-nnq8b",

            "doubao-pro-128k": "ep-20240515073409-dlpqp",
            "doubao-pro-32k": "ep-20240515073434-s4skk",
            "doubao-pro-4k": "ep-20240515073524-xj4m2",  # fc

            "moonshot-v1-8k": "ep-20240516010405-mwthf",
            "moonshot-v1-32k": "ep-20240516010345-f88rs",
            "moonshot-v1-128k": "ep-20240516010323-zfzwj",

            "doubao-embedding": "ep-20240516005609-9c9pq",
        }


if __name__ == '__main__':
    client = Completions()
    r = client.create(ChatCompletionRequest(stream=True))

    for i in r:
        print(i)
