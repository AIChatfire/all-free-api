#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chatfire
# @Time         : 2024/7/3 13:13
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *

from meutils.llm.openai_utils import to_openai_completion_params, token_encoder, token_encoder_with_cache
from meutils.schemas.openai_types import chat_completion, chat_completion_chunk, ChatCompletionRequest, CompletionUsage

from openai import OpenAI, AsyncOpenAI, APIStatusError


class Completions(object):

    def __init__(self, api_key):
        self.api_key = api_key
        if self.api_key.startswith("sk-"):
            self.client = AsyncOpenAI(
                api_key=api_key,
            )
        else:
            logger.debug(api_key)
            self.client = AsyncOpenAI(
                api_key=os.getenv("ZHIPU_API_KEY", "fdadb5b1088115cb5311c3a74b9ea6ae.9CXVP3fr4UIPNYMO"),
                base_url=os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
            )

    async def create(self, request: ChatCompletionRequest):
        data = to_openai_completion_params(request)

        logger.debug(data)

        stream = await self.client.chat.completions.create(**data)

        return self.chunks_to_markdown(stream)

    @staticmethod
    async def chunks_to_markdown(chunks):
        if not chunks: return

        tool_name = ""
        async for chunk in chunks:
            delta = chunk.choices[0].delta
            if delta.tool_calls:
                tool_delta = delta.tool_calls[0]

                logger.debug(tool_delta)

                tool_type = tool_delta.type
                if tool_name != tool_type:
                    tool_name = tool_type
                    yield f"""> 🔥 **{tool_name.title()}**\n\n"""  # 工具名
                    yield f"""```input\n"""  # 工具输入：开始

                tool_input = tool_delta.__getattr__(tool_type).get('input')  # {'input': 'A'}
                if tool_input:
                    yield tool_input
                if tool_input == '':
                    yield "\n```\n\n"  # 工具输入：结束

                # 工具输出
                tool_outputs = tool_delta.__getattr__(tool_type).get('outputs')  # {'outputs': [...]}
                if tool_outputs:
                    if tool_name == "drawing_tool":
                        for output in tool_outputs:
                            for i in f"![]({output['image']})\n":
                                await asyncio.sleep(0.01)
                                yield i

                    elif tool_name == "web_browser":
                        for output in tool_outputs:
                            yield f"[{output['title']}]({output['link']})\n"  # 太多了

                    elif tool_name == "code_interpreter":  #
                        yield f"```json\n{json.dumps(tool_outputs, indent=4, ensure_ascii=False)}\n```\n"

                    else:
                        yield f"```json\n{json.dumps(tool_outputs, indent=4, ensure_ascii=False)}\n```\n"

                    yield "\n"

            if delta.content:
                yield delta.content
