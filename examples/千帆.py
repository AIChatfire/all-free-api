#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 千帆
# @Time         : 2024/8/19 13:28
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *

import os
import qianfan
from qianfan import QfResponse

# 【推荐】使用安全认证AK/SK鉴权，通过环境变量初始化认证信息
# 替换下列示例中参数，安全认证Access Key替换your_iam_ak，Secret Key替换your_iam_sk
os.environ["QIANFAN_AK"] = "BDFfKLrzBxDjqPwDUPQYz3gpp"
os.environ["QIANFAN_SK"] = "ER3XaVE73TV3rg0GpJoCeJac2vEz33Foo"

chat_comp = qianfan.ChatCompletion()

# 指定特定模型
resp = chat_comp.do(stream=True, model="ERNIE-", messages=[{
    "role": "user",
    "content": "1+1"
}])

# print(resp["body"])

# {'id': 'as-qcvv76bava', 'object': 'chat.completion', 'created': 1724047506, 'result': '这是一个非常基础的数学问题。当我们把1和1相加时，结果是2。\n\n所以，1 + 1 = 2。', 'is_truncated': False, 'need_clear_history': False, 'finish_reason': 'normal', 'usage': {'prompt_tokens': 3, 'completion_tokens': 28, 'total_tokens': 31}}

for i in resp:
    print(i.body['result'])
