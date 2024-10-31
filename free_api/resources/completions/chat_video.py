#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chat_video
# @Time         : 2024/8/1 09:05
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from meutils.pipe import *

from meutils.schemas.openai_types import ChatCompletionRequest
from meutils.schemas.task_types import Task

from meutils.schemas.runwayml_types import RunwayRequest, Options
from meutils.schemas.vidu_types import ViduRequest


class Completions(object):

    def __init__(self, api_key):
        self.api_key = api_key

    async def create(self, request: ChatCompletionRequest) -> AsyncGenerator:

        vip = "vip" in request.model  # todo: 增强

        task_type = "vidu"
        if request.model.__contains__('gen'):
            task_type = "runwayml"
        elif request.model.__contains__('vidu'):
            task_type = "vidu"
        elif request.model.__contains__('kling'):
            task_type = "kling"
        elif request.model.__contains__('cogvideox'):
            task_type = "cogvideox"

        func = lambda x: x
        if task_type == "runwayml":
            video_request = RunwayRequest(options=Options(text_prompt=request.last_content, exploreMode=True))
            future_task = asyncio.create_task(self.create_task(task_type, video_request))  # 异步执行

            def func(data):
                data = data.get("task")
                if data.get("status") != "SUCCEEDED":
                    # progressText = data.get("progressText")
                    progressRatio = float(data.get("progressRatio") or 0)
                    if progressRatio:
                        yield f"{progressRatio:.2%}"
                else:
                    yield ")🎉🎉🎉\n\n"  # 隐藏进度条
                    video_url = data.get("artifacts")[0].get("url")
                    yield f"[下载地址]({video_url})\n\n"
                    # yield f"![视频地址]({video_url})\n\n"
                    yield "DONE"

        elif task_type == "vidu":
            video_request = ViduRequest(prompt=request.last_content)
            future_task = asyncio.create_task(self.create_task(task_type, video_request, vip))  # 异步执行

            def func(data):
                if data.get("state") == "success":
                    yield ")🎉🎉🎉\n\n"  # 隐藏进度条
                    video_url = data.get("creations")[0].get("uri")
                    yield f"[下载地址]({video_url})\n\n"
                    # yield f"![视频地址]({video_url})\n\n"
                    yield "DONE"
                else:
                    yield "✨"

        async def gen_chunks(func):
            for i in f"> ▶️ 正在制作中\n\n```json\n{video_request.model_dump_json(indent=4, exclude_none=True)}\n```\n\n":
                await asyncio.sleep(0.03)
                yield i

            task = await future_task
            task_url = f"https://api.chatfire.cn/tasks/{task.id}"
            logger.debug(task_url)
            yield f"> 🤫 任务创建成功，[任务详情]({task_url})\n\n"

            yield f" 🤫 [任务进度]("

            chunk = None
            for i in range(100):
                await asyncio.sleep(2)
                try:
                    response = await httpx.AsyncClient(timeout=30).get(task_url)
                    data = response.json()
                except Exception as e:
                    logger.error(e)
                    continue

                for chunk in func(data):
                    yield chunk

                if chunk == "DONE": break

        return gen_chunks(func)
        # async for i in gen_chunks(func):
        #     yield i

    async def create_task(self, task_type, video_request, vip: bool = False):
        headers = {'Authorization': f'Bearer {self.api_key}'}
        payload = video_request.model_dump(exclude_none=True)
        params = {"vip": vip}

        async with httpx.AsyncClient(base_url="https://api.chatfire.cn/tasks", headers=headers, timeout=100) as client:
            response = await client.post(f"/{task_type}", json=payload, params=params)
            if response.is_success:
                return Task(**response.json())

    async def create_task_upscale(self, task_id, creation_id):
        task_type = "vidu-upscale"

        headers = {'Authorization': f'Bearer {self.api_key}'}
        payload = {
            "task_id": task_id,
            "creation_id": creation_id
        }

        async with httpx.AsyncClient(base_url="https://api.chatfire.cn/tasks", headers=headers, timeout=100) as client:
            response = await client.post(f"/{task_type}", json=payload)
            if response.is_success:
                return Task(**response.json())


if __name__ == '__main__':
    _ = Completions(os.getenv("OPENAI_API_KEY_SSVIP")).create(
        ChatCompletionRequest(messages = [{'role': 'user', 'content': '比卡丘'}])
    )

    # async def main():
    #     async for i in await _:
    #         print(i, end='')

    # print(inspect.isasyncgen( _))
    # print(inspect.isasyncgenfunction(_))
    # print(type(_))
    #
    # print(inspect.isawaitable(_))

    arun(_)

    # arun(main())


