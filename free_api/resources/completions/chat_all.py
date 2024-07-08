#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chat_multimodal
# @Time         : 2024/4/22 13:36
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
"""
结构体通用化转发

"""

from meutils.pipe import *
from meutils.notice.feishu import send_message
from meutils.str_utils.regular_expression import parse_url

from chatllm.schemas.openai_types import chat_completion, chat_completion_chunk
from chatllm.schemas.openai_api_protocol import ChatCompletionRequest, UsageInfo
from chatllm.utils.openai_utils import openai_response2sse, to_openai_completion_params

from openai import OpenAI, AsyncOpenAI


class Completions(object):
    def __init__(self, api_key=None):
        params = dict(
            api_key=api_key,
            base_url='https://api.chatfire.cn/v1',
            max_retries=1,
        )
        # 如果这一步就报错呢
        self.client = AsyncOpenAI(**params)

    def create(self, request: ChatCompletionRequest):
        logger.debug(str(request.messages))

        prompt = request.messages[-1].get('content')
        request.messages[-1]['content'] = self.url2part_content(prompt)
        data = to_openai_completion_params(request)

        logger.debug(request.messages)

        return OpenAI().chat.completions.create(**data)

    async def acreate(self, request: ChatCompletionRequest, **kwargs):
        logger.debug(str(request.messages))

        prompt = request.messages[-1].get('content')
        request.messages[-1]['content'] = self.url2part_content(prompt)
        data = to_openai_completion_params(request)

        logger.debug(str(request.messages))

        _ = await self.client.chat.completions.create(**data)

        return _

    @staticmethod
    def url2part_content(content):  # todo: 文件url无法放image_url里
        """几种处理方式
        1. url放入[{"type": "image_url", "image_url": {"url": ""}}]
        2. 根据url提取出内容 [content](url)  待确认
        """
        # part content
        # if isinstance(content, list):  # [{'role': 'user', 'content':  [{"type": "text", "text": ""}]]
        #     for part in content:
        #         if part.get("type")==""

        # content = f"{content}\n```url\n{reader(url)}\n```"

        if isinstance(content, str):  # 当前针对text，单轮
            text = content
            urls = parse_url(text, for_image=True)

            content = [
                {"type": "text", "text": text},
                *[{"type": "image_url", "image_url": {"url": url}} for url in urls]
            ]
        elif isinstance(content, list):  # 识图标准化
            parts = []
            for part in content:
                if part.get("type") == "image_url" and isinstance(part.get("image_url"), str):
                    # {'type': 'image_url', 'image_url': 'http://ai.chatfire.cn/files/images/xx.jpg'}
                    part["image_url"] = {"url": part["image_url"]}
                parts.append(part)

        return content


if __name__ == '__main__':
    messages = [
        {
            'role': 'user',
            'content': "解释下这张照片https://img-home.csdnimg.cn/images/20201124032511.png"
        },
    ]

    # messages = [
    #     {
    #         'role': 'user',
    #         'content': [{"type": "text", "text": "解释下这张照片 https://img-home.csdnimg.cn/images/20201124032511.png"}]
    #     }
    # ]

    messages = [
        {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': '解释下这张照片'},
                {'type': 'image_url', 'image_url': 'https://img-home.csdnimg.cn/images/20201124032511.png'}]  # 不标准
        }
    ]

    request = ChatCompletionRequest(model="step-1", messages=messages)  # 针对all
    print(Completions().create(request))


    # async def main():
    #     async for i in Completions().acreate(request):
    #         print(i)
    #
    # arun(main())

