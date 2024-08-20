#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : sensechat
# @Time         : 2024/8/7 10:37
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.schemas.openai_types import ChatCompletionRequest, ChatCompletion, chat_completion
from meutils.config_utils.lark_utils import get_next_token_for_polling
from meutils.llm.openai_utils import to_openai_completion_params
from meutils.notice.feishu import send_message

FEISHU_URL = "https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=LCOPGF"

import sensenova
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
            # api_key="06B21A0AE0C94980868BD457DD5AB7FA:AEB14BD3D772499897E8306B08D1D258"
            access_key_id, secret_access_key = api_key.strip().split(':')

            resp = await sensenova.ChatCompletion.acreate(
                **request.model_dump(exclude_none=True),
                access_key_id=access_key_id,
                secret_access_key=secret_access_key
            )
            if request.stream:
                async def gen():
                    async for i in resp:
                        yield i.data.choices[0].delta

                return gen()

            else:
                chat_completion.choices[0].message.content = resp.data.choices[0].message
                chat_completion.usage = dict(resp.data.usage)

                return chat_completion
        except Exception as e:
            logger.error(e)
            send_message(e, title=__name__)

            request.model = "glm-4"
            data = to_openai_completion_params(request)
            return await AsyncOpenAI().chat.completions.create(**data)


if __name__ == '__main__':
    request = ChatCompletionRequest(model='SenseChat', stream=False, messages=[{'role': 'user', 'content': '你是谁'}])


    async def main():
        for i in await Completions().create(request):
            print(i)


    arun(main())
