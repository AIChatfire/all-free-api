#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_adapter
# @Time         : 2024/8/7 12:21
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from aiostream import stream

from meutils.pipe import *
from meutils.decorators.contextmanagers import atry_catch

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers
from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, to_openai_params
from meutils.llm.completions import dify, sophnet, qwenllm, yuanbao, chat_gemini

from meutils.apis.search import metaso
from meutils.apis.fal import chat as fal_chat
from meutils.apis.google import chat as google_chat
from meutils.apis.images import mj

from meutils.schemas.openai_types import CompletionRequest, ChatCompletionRequest, chat_completion_chunk

from openai import AsyncClient
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

from free_api.resources.completions import sensechat, chat_qianfan

router = APIRouter()
TAGS = ["文本生成"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/{request_model:path}")  # todo: 映射函数
async def create_chat_completions(
        request: CompletionRequest,

        request_model: str = '目标值模型',  # 源模型
        response_model: str = Query(None),  # 响应模型

        threshold: Optional[int] = Query(None),
        max_turns: Optional[int] = Query(None),

        api_key: Optional[str] = Depends(get_bearer_token),
        base_url: Optional[str] = None,

        headers: dict = Depends(get_headers),
):
    logger.debug(request.model_dump_json(indent=4))
    logger.debug(response_model)

    async with atry_catch(f"{base_url}/{response_model}", api_key=api_key, request=request):

        response_model = response_model or request.model
        if not request_model.startswith("v1"):  # 重定向
            request.model = request_model  # qwen-plus-latest

        if max_turns:  # 限制对话轮次
            request.messages = request.messages[-(2 * max_turns - 1):]

        response = None
        if request.model.lower().startswith(("o1", "openai/o1")) and not api_key.startswith('tune'):  # 适配o1
            request = ChatCompletionRequest(**request.model_dump())

            if "RESPOND ONLY WITH THE TITLE TEXT" in str(request.last_content): return

            base_url = None

            request.model = request.model.removesuffix('-all')
            request.messages = [message for message in request.messages if message['role'] != 'system']

            data = to_openai_params(request)
            data['stream'] = False
            data.pop('max_tokens', None)
            response = await AsyncClient(api_key=api_key, base_url=base_url, timeout=100).chat.completions.create(
                **data)
            if request.stream:
                response = response.choices[0].message.content

        elif request.model.lower().startswith(("perplexity", "net")):  # 前置联网
            # model="net-gpt-4o",
            if request.model.lower().startswith(("net-gpt-4",)):
                request.model = "net-gpt-4o-mini"
            elif request.model.lower().startswith(("net-claude",)):
                request.model = "net-claude-1.3-100k"
            else:
                request.model = "net-gpt-3.5-turbo-16k"

            data = to_openai_params(request)
            client = AsyncClient(api_key=api_key, base_url=os.getenv("GOD_BASE_URL"), timeout=100)
            response = await client.chat.completions.create(**data)

        elif request.model.startswith(("ai-search", "meta")) or "meta" in request.model:  # 搜索
            request = ChatCompletionRequest(**request.model_dump())

            response = metaso.create(request)

        elif request.model.startswith(("ERNIE",)):  # 反向
            request = ChatCompletionRequest(**request.model_dump())
            request.model = "ERNIE-Speed-128K"

            response = await chat_qianfan.Completions().create(request)
        #
        # elif api_key.startswith(("app-",)):  # 适配dify
        #     client = dify.Completions(api_key=api_key)
        #     response = client.create(request)  # List[str]

        elif request.model.lower().startswith(("qwen", "qvq", "qwq")):  # 逆向 o1 c35 ###################
            response = qwenllm.create(request, cookie=headers.get("cookie"))

        elif request.model.lower().startswith(("mj",)):
            response = mj.generate(request, api_key=api_key)

        # google
        elif request.model.startswith(("gemini",)):
            if "|" in api_key:
                base_url, api_key = api_key.split("|")
                client = chat_gemini.Completions(base_url=base_url, api_key=api_key)
                response = await client.create(request)  # 果果兜底：最终弃用

            else:

                logger.debug(request.model)
                if request.model.endswith(("image-generation",)):
                    response = google_chat.Completions(api_key=api_key, base_url=base_url).create_for_images(request)

                elif request.model.endswith(("search",)):
                    response = google_chat.Completions(api_key=api_key, base_url=base_url).create_for_search(request)
                else:  # 多模态问答
                    try:
                        response = google_chat.Completions(api_key=api_key, base_url=base_url).create_for_files(request)
                    except Exception as e:
                        logger.error(e)
                        request.model = "gemini-2.0-flash"
                        client = chat_gemini.Completions(api_key=api_key)
                        response = await client.create(request)  # 果果兜底：最终弃用


        ############ apikey判别
        elif api_key.startswith(("yuanbao",)):
            client = yuanbao.Completions()
            logger.debug(request)
            response = client.create(request)

        elif api_key.startswith("fal-"):  ############ fal
            response = fal_chat.create(request, api_key=api_key)

        elif api_key.startswith(("sophnet", "sop")):
            response = await sophnet.create(request)

        #########################################################################################################
        if request.stream:
            return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=response_model))

        if inspect.isasyncgen(response):  # 非流：将流转换为非流 tdoo 計算tokens
            logger.debug("IS_ASYNC_GEN")

            chunks = await stream.list(response)

            if chunks and isinstance(chunks[0], ChatCompletion):
                response = chunks[0]
            else:
                response = create_chat_completion(chunks)

            # logger.debug(response)
            # logger.debug(chunks)
            if not (response.usage and hasattr(response.usage, "prompt_tokens") and response.usage.prompt_tokens):
                prompt_tokens = int(len(str(request.messages)) // 2)
                completion_tokens = int(len(str(chunks)) // 2)
                response.usage = dict(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens
                )

        if hasattr(response, "model"):
            response.model = response_model  # 以请求体为主
        return response  # chat_completion


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '')

    app.run()

    os.getenv("OPENAI_API_KEY_OPENAI")
