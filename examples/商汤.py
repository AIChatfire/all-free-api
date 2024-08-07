#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 商汤
# @Time         : 2024/8/5 11:57
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.schemas.openai_types import ChatCompletionChunk
import sensenova

sensenova.access_key_id = "BDABD60C307D4FBB88CB7018E9A2EAAF"
sensenova.secret_access_key = "719BC2D17B4A4D13A5D26B37FB06DA53"


resp = sensenova.ChatCompletion.acreate(
    model="SenseChat",
    max_new_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "你好"
        }
    ],
    repetition_penalty=1.05,
    temperature=0.8,
    top_p=0.7,
    stream=False
)

# resp.data.choices[0].message

# AccessKey ID： BDABD60C307D4FBB88CB7018E9A2EAAF    AccessKey Secret：719BC2D17B4A4D13A5D26B37FB06DA53
#
# for i in resp:
#     print(i.data.choices[0].delta)

    #


arun(resp)