#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chat_qianfan
# @Time         : 2024/8/19 13:49
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
from meutils.pipe import *
from meutils.schemas.openai_types import ChatCompletionRequest, ChatCompletion, chat_completion
from meutils.config_utils.lark_utils import get_next_token_for_polling
from meutils.llm.openai_utils import to_openai_completion_params
from meutils.notice.feishu import send_message

FEISHU_URL = "https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=Wb5BPv"

import qianfan
from openai import AsyncOpenAI


class Completions(object):

    def __init__(self, api_key: Optional[str] = None, threshold: Optional[int] = None):
        self.api_key = api_key
        self.threshold = threshold

    async def create(self, request: ChatCompletionRequest):
        try:
            if self.threshold and len(str(request.messages)) > self.threshold:
                raise Exception("pass")

            api_key = self.api_key or await get_next_token_for_polling(FEISHU_URL)
            os.environ["QIANFAN_AK"], os.environ["QIANFAN_SK"] = api_key.split('|')

            kwargs = request.model_dump(exclude_none=True)
            if request.messages[0]['role'] == 'system':
                kwargs['system'] = request.messages[0]['content']
                kwargs['messages'] = request.messages[1:]

            resp = await qianfan.ChatCompletion().ado(
                **kwargs
            )
            if request.stream:
                async def gen():
                    async for i in resp:
                        yield i.body['result']

                return gen()

            else:
                chat_completion.choices[0].message.content = resp["body"]['result']
                chat_completion.usage = resp["body"]['usage']

                return chat_completion
        except Exception as e:
            logger.error(e)
            send_message(e, title=__name__)

            request.model = "glm-4"  # BACKUP_MODEL
            data = to_openai_completion_params(request)
            return await AsyncOpenAI().chat.completions.create(**data)


if __name__ == '__main__':
    messages = [{'role': 'system', 'content': '你是数学家'}, {'role': 'user', 'content': '你能干嘛'}]

    arun(Completions().create(ChatCompletionRequest(model="ERNIE-4.0-8K", messages=messages)))
