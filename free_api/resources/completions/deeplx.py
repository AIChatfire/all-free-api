#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : deeplx
# @Time         : 2024/4/23 17:06
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.notice.feishu import send_message
from meutils.apis.deeplx import translate

from chatllm.schemas.openai_types import chat_completion, chat_completion_chunk as _chat_completion_chunk
from chatllm.schemas.openai_api_protocol import ChatCompletionRequest, UsageInfo

from chatllm.utils.openai_utils import token_encoder


class Completions(object):

    def create(self, request: ChatCompletionRequest):
        # logger.debug(str(request.messages))
        # {'code': 200, 'id': 9324310002, 'data': '你好，世界', 'alternatives': ['世界，你好', '你好，世界！', '大家好']}
        # target_lang, text = request.last_content.split(maxsplit=1)[0] # todo: 兼容沉浸式翻译
        #
        # payload = {
        #     "text": text,
        #     "source_lang": "auto",
        #     "target_lang": target_lang,
        #     **self.payload
        # }

        try:

            response = translate(**request.payload)
            chunk = response.get('data')
            # chunk = f"""```json\n{bjson(response)}\n```"""
        except Exception as e:
            chunk = str(e)

            send_message(str(e), title='deeplx')

        if request.stream:
            chat_completion_chunk = _chat_completion_chunk.model_copy(deep=True)
            chat_completion_chunk.choices[0].delta.content = chunk
            yield chat_completion_chunk

            # 结束标识
            chat_completion_chunk.choices[0].delta.content = ""
            chat_completion_chunk.choices[0].finish_reason = "stop"
            yield chat_completion_chunk

        else:
            chat_completion.usage.prompt_tokens = len(token_encoder.encode(request.payload.get('text')))
            chat_completion.usage.completion_tokens = 1
            chat_completion.choices[0].message.content = chunk
            yield chat_completion

    async def acreate(self, request: ChatCompletionRequest, **kwargs):
        pass


if __name__ == '__main__':
    payload = {
        "text": '火哥AI是最棒的',
        "source_lang": 'auto',
        "target_lang": 'EN'
    }

    request = ChatCompletionRequest(model='deeplx', payload=payload, stream=False)
    response = Completions().create(request)
    print(json.loads(list(response)[0].choices[0].message.content))

    for i in Completions().create(request):
        print(i)

    # import tiktoken
    #
    # print(tiktoken.get_encoding('cl100k_base').encode('我是谁'))

    import openai

    openai.OpenAI.chat.completions.create()
