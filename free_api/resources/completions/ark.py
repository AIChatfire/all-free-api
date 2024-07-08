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

from chatllm.schemas.openai_api_protocol import ChatCompletionRequest, UsageInfo
from chatllm.utils.openai_utils import openai_response2sse, to_openai_completion_params

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

        data = to_openai_completion_params(request)
        return await self.aclient.chat.completions.create(**data)

    @staticmethod
    # @ttl_cache(ttl=15 * 24 * 3600)
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
            # resource_type="endpoint",
            resource_type="bot" if resource_ids[0].startswith("bot") else "endpoint",

            resource_ids=resource_ids
            # resource_ids=list(endpoint_map.values()),
            # resource_ids=["ep-20240515062545-nnq8b"]
        )

        resp = api_instance.get_api_key(get_api_key_request)

        return resp.api_key

    @property
    def endpoint_map(self):
        return {
            "doubao-lite-128k": "ep-20240520010805-566f7",
            "doubao-lite-32k": "ep-20240515062431-rkhfp",
            "doubao-lite-4k": "ep-20240515062545-nnq8b",

            "doubao-pro-128k": "ep-20240515073409-dlpqp",
            "doubao-pro-32k": "ep-20240515073434-s4skk",
            "doubao-pro-4k": "ep-20240515073524-xj4m2",  # fc

            "moonshot-v1-8k": "ep-20240516010405-mwthf",
            "moonshot-v1-32k": "ep-20240516010345-f88rs",
            "moonshot-v1-128k": "ep-20240516010323-zfzwj",

            "doubao-embedding": "ep-20240516005609-9c9pq",
            "name-20240606": "bot-20240605032421-b4j9j"
        }


if __name__ == '__main__':
    client = Completions()
    # print(client.get_and_update_api_key(resource_ids=list(client.endpoint_map.values())))
    print(client.get_and_update_api_key(resource_ids=["bot-20240605032421-b4j9j"]))

    # r = client.create(ChatCompletionRequest(stream=True, model="moonshot-v1-8k"))

    for i in r:
        print(i)
