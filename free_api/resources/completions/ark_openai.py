#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : ark_openai
# @Time         : 2024/5/15 15:52
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from meutils.pipe import *

'''
Usage:
Ark v3 sdk
pip install volcengine-python-sdk
'''

from volcenginesdkarkruntime import Ark

# follow this document (https://www.volcengine.com/docs/82379/1263279) to generate API Key
# put API Key into environment variable ARK_API_KEY or specify api_key directly in Ark()
client = Ark()

# if __name__ == "__main__":
#
#     # Non-streaming:
#     print("----- standard request -----")
#     completion = client.chat.completions.create(
#         model="ep-20240515062431-rkhfp",
#         messages=[
#             {
#                 "role": "user",
#                 "content": "Say this is a test",
#             },
#         ],
#     )
#     print(completion.choices[0].message.content)
#
#     # Streaming:
#     print("----- streaming request -----")
#     stream = client.chat.completions.create(
#         model="ep-20240515073434-s4skk",
#         messages=[
#             {
#                 "role": "user",
#                 "content": "1+1",
#             },
#         ],
#         stream=True,
#     )
#     for chunk in stream:
#         if not chunk.choices:
#             continue
#
#         print(chunk.choices[0].delta.content, end="")


if __name__ == '__main__':
    from openai import OpenAI

    client = OpenAI(
        base_url="https://test.chatfire.cn/v1",
        # base_url=os.getenv("ARK_BASE_URL"),
        api_key=os.getenv("ARK_API_KEY")
    )

    messages = [
        {
            "role": "user",
            "content": "你是誰",
        },
    ]
    r = client.chat.completions.create(
        messages=messages,
        model="ep-20240515073524-xj4m2",
        # model="doubao-pro-4k",
        # model="test",
        # model='hailuo',
        stream=True,
    )
    print(r)
    for i in r:
        print(i)


