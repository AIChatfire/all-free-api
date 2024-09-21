#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : vision_llm
# @Time         : 2024/8/20 13:37
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import jsonpath

from meutils.pipe import *
from meutils.schemas.openai_types import ChatCompletionRequest, ChatCompletion, chat_completion

from meutils.apis.minicpm import luca


class Completions(object):

    async def create(self, request: ChatCompletionRequest):

        urls = (
                jsonpath.jsonpath(request.last_content, expr='$..url') or
                jsonpath.jsonpath(request.last_content, expr='$..image_url')
        )
        prompts = jsonpath.jsonpath(request.last_content, expr='$..text') or "一步一步思考，解释图片"

        logger.debug(urls)
        logger.debug(prompts)

        if urls:
            content = await luca.create_chat(prompt=prompts[0], image_data=urls[0])
        else:
            content = "请输入正确的图片格式：base64/url"

        return content


if __name__ == '__main__':
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "解释"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://dss2.bdstatic.com/5bVYsj_p_tVS5dKfpU_Y_D3/res/r/image/2021-3-4/hao123%20logo.png"
                    }
                }

            ]
        }
    ]

    # messages[0]['content'] = [
    #     {
    #         "type": "text",
    #         "text": "解释下"
    #     },
    #     {
    #         "type": "image_url",
    #         "image_url": "http://ai.chatfire.cn/files/images/image-1725418399272-d7b71012f.png"
    #     }
    # ]

    arun(Completions().create(ChatCompletionRequest(messages=messages)))
