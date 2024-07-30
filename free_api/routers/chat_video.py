#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chat_video
# @Time         : 2024/7/25 10:59
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.schemas.runwayml_types import RunwayRequest, Options
from meutils.schemas.openai_types import ChatCompletionRequest
from meutils.schemas.task_types import Task

from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, chat_completion

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body
from sse_starlette import EventSourceResponse
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai import AsyncOpenAI

router = APIRouter()
TAGS = ["VIDEO"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/chat/completions")
async def create_chat_completions(
        request: ChatCompletionRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        vip: Optional[bool] = Query(False),
        backgroundtasks: BackgroundTasks = BackgroundTasks,
):
    api_key = auth and auth.credentials or None
    logger.debug(request.model_dump_json(indent=4))

    if request.last_content.startswith(  # 跳过nextchat
            ("使用四到五个字直接返回这句话的简要主题",
             "简要总结一下对话内容，用作后续的上下文提示 prompt，控制在 200 字以内")):
        return

        # todo: 其他模型，目前 gen3

    video_request = RunwayRequest(options=Options(text_prompt=request.last_content, exploreMode=not vip))

    async def create_video(task_type="runwayml"):
        headers = {'Authorization': f'Bearer {api_key}'}
        payload = video_request.model_dump(exclude_none=True)

        async with httpx.AsyncClient(base_url="https://api.chatfire.cn/tasks", headers=headers, timeout=100) as client:
            response = await client.post(f"/{task_type}", json=payload)
            if response.is_success:
                return Task(**response.json())

    future_task = asyncio.create_task(create_video())  # 异步执行
    if request.stream:
        async def gen_chunks():
            for i in f"> ▶️ 正在制作中\n\n```json\n{video_request.model_dump_json(indent=4, exclude_none=True)}\n```\n\n":
                await asyncio.sleep(0.03)
                yield i

            task = await future_task
            task_url = f"https://api.chatfire.cn/tasks/{task.id}"
            logger.debug(task_url)
            yield f"> 🤫 任务创建成功，[任务详情]({task_url})\n\n"

            yield f" 🤫 [任务进度]("
            for i in range(100):
                await asyncio.sleep(3)

                data = (await httpx.AsyncClient().get(task_url)).json().get("task")
                if data.get("status") != "SUCCEEDED":
                    # progressText = data.get("progressText")
                    progressRatio = float(data.get("progressRatio") or 0)
                    if progressRatio:
                        yield f"{progressRatio:.2%}"
                else:
                    yield ")🎉🎉🎉\n\n"  # 隐藏进度条
                    video_url = data.get("artifacts")[0].get("url")
                    yield f"[下载地址]({video_url})\n\n"
                    yield f"![视频地址]({video_url})\n\n"
                    break

        chunks = create_chat_completion_chunk(gen_chunks())
        return EventSourceResponse(chunks)
    else:
        return create_chat_completion(chat_completion)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
    # for i in range(10):
    #     send_message(f"兜底模型", title="github_copilot")
