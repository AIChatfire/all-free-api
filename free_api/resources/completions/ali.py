#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : ali
# @Time         : 2024/5/24 11:11
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
from asgiref.sync import sync_to_async, async_to_sync

from meutils.pipe import *
from meutils.io.image import base64_to_bytes, image_to_base64
from dashscope import Application, Generation, MultiModalConversation

from chatllm.schemas.openai_api_protocol import ChatCompletionRequest, UsageInfo
from chatllm.schemas.openai_types import chat_completion, chat_completion_chunk


class Completions(object):
    def __init__(self, api_key=None):
        self.api_key = api_key

    @sync_to_async
    def acreate(self, request: ChatCompletionRequest):
        return self.create(request)

    def create(self, request: ChatCompletionRequest):
        # {"text": null, "finish_reason": null, "choices": [
        #      {"finish_reason": "null", "message": {"role": "assistant", "content": [{"text": "这张"}]}}]},

        if request.model.__contains__("-vl"):  # 多模态
            # [{'role': 'user', 'content': [
            #   {"type": "text","text": "xx"},
            #   {"type": "image_url", "image_url": {"url": "xxx"}}]}
            # ]
            text = image_url = ""
            for content in request.messages[-1].get("content"):
                text = text or content.get("text")
                image_url = content.get("image_url", {}).get("url")

            # 兼容 base64
            if image_url.startswith("data:image"):
                from chatllm.llmchain.completions import chatglm_web
                upload = async_to_sync(chatglm_web.Completions().put_object_for_openai)

                file_object = upload(base64_to_bytes(image_url), purpose="file_upload")
                image_url = file_object.filename

                logger.debug(file_object)

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"text": text},
                        {"image": image_url},
                    ]
                }
            ]
            logger.debug(messages)

            response = MultiModalConversation.call(
                model=request.model,  # app当做一个模型
                messages=messages,  # Message
                api_key=self.api_key,
                stream=request.stream,
                temperature=request.temperature,
            )


        elif request.model.startswith("qwen-") or request.model in {"farui-plus"}:
            response = Generation.call(
                model=request.model,  # app当做一个模型
                messages=request.messages,  # Message
                api_key=self.api_key,
                stream=request.stream,
                temperature=request.temperature,
                # incremental_output=True,
                # result_format='message',  # 设置输出为'message'格式
            )


        else:
            response = Application.call(
                app_id=request.model,  # app当做一个模型
                prompt=request.last_content,
                api_key=self.api_key,
                stream=request.stream,
                temperature=request.temperature,
            )

        if request.stream:
            content = ''
            for chunk in response:
                if chunk.status_code != 200:
                    logger.error(chunk)
                    chat_completion_chunk.choices[0].delta.content = chunk
                    chat_completion_chunk.choices[0].finish_reason = 'stop'
                    yield chat_completion_chunk
                    return

                output = chunk.get("output", {})

                _content = output.get("text")
                if _content:
                    chat_completion_chunk.choices[0].delta.content = _content.replace(content, '')
                    yield chat_completion_chunk
                    chat_completion_chunk.choices[0].finish_reason = output.get("finish_reason")
                    content = _content
                else:
                    _ = output.get("choices")[0]
                    finish_reason = _.get("finish_reason")
                    _content = _.get("message").get("content")
                    if isinstance(_content, list):
                        _content = _content[0].get("text")

                    chat_completion_chunk.choices[0].delta.content = _content.replace(content, '')
                    if finish_reason != 'stop':
                        chat_completion_chunk.choices[0].finish_reason = finish_reason
                    yield chat_completion_chunk
                    content = _content
        else:
            if response.status_code != 200:
                logger.error(response)
                chat_completion.choices[0].message.content = response
                yield chat_completion
                return

            chat_completion.choices[0].message.content = response.get("output", {}).get("text")

            if "models" in (usage := response.get("usage")):
                usage = response.get("usage").get("models")[0]

            prompt_tokens = usage.get("input_tokens")
            completion_tokens = usage.get("output_tokens")
            total_tokens = prompt_tokens + completion_tokens
            chat_completion.usage = UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )

            # logger.debug(chat_completion)

            yield chat_completion


if __name__ == '__main__':
    app_id = '3e27fc43adf5410c919cc4aaae03c88d'
    prompt = '你是谁'
    api_key = 'sk-4e6489ba597541dfa7a51f43e3912ca2'
    api_key = 'sk-9c519f1bffd4486f8c3c308ac3d89b66'

    model = "farui-plus"
    # model = "qwen-max"
    model = "qwen-vl-max"

    client = Completions(api_key=api_key)
    # print(client.get_and_update_api_key(resource_ids=list(client.endpoint_map.values())))

    # r = client.create(ChatCompletionRequest(stream=False, model=app_id))
    # r = client.create(ChatCompletionRequest(stream=False, model='qwen-max'))
    # r = client.create(
    #     ChatCompletionRequest(stream=True, model=model, messages=[{'role': 'user', 'content': '你是谁'}]))
    messages = [
        {'role': 'user', 'content': [
            {"type": "text", "text": "解释下"},
            # {"type": "image_url", "image_url": {"url": "https://oss.chatfire.cn/app/qun.png"}},
            # {"type": "image_url", "image_url": {"url": image_to_base64('x.png')}},

        ]
         }
    ]
    r = client.create(
        ChatCompletionRequest(stream=True, model=model, messages=messages)
    )

    for i in r:
        print(i)
