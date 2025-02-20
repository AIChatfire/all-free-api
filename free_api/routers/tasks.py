#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : task
# @Time         : 2024/7/11 13:35
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import ppu_flow
from meutils.schemas.task_types import TaskType, Task
from meutils.schemas.kuaishou_types import KlingaiVideoRequest, Camera
from meutils.apis.kuaishou import klingai_video, klingai
from meutils.schemas.runwayml_types import RunwayRequest
from meutils.apis.runwayml import gen

from meutils.schemas.suno_types import SunoAIRequest, LyricsRequest
from meutils.apis.sunoai import suno, haimian

from meutils.schemas.haimian_types import HaimianRequest

from meutils.schemas.chatglm_types import VideoRequest
from meutils.apis.chatglm import glm_video

from meutils.schemas.vidu_types import ViduRequest, ViduUpscaleRequest
from meutils.apis.vidu import vidu_video

from meutils.schemas.prodia_types import FaceswapRequest
from meutils.apis.images.prodia import faceswap

from meutils.schemas.baidu_types import BDAITPZSRequest
from meutils.apis.baidu import bdaitpzs

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, Depends, BackgroundTasks, Request, Query, Body, Header, HTTPException, status
from fastapi.responses import JSONResponse

router = APIRouter()
TAGS = ["异步任务"]


@router.get("/tasks/{task_id}")
@alru_cache(maxsize=2048, ttl=15)  # 延迟10s
async def get_tasks(
        task_id: str,
        response_format: Optional[str] = Query(None),
        # auth: Optional[str] = Depends(get_bearer_token),
        # backgroundtasks: BackgroundTasks = BackgroundTasks,
):
    # api_key = auth

    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="Task ID not found")

    task_type = None
    if "-" in task_id:
        task_type, _ = task_id.split("-", 1)  # 区分业务

    data = {}
    if task_type is None:  # 通用业务：默认从redis获取
        data = await redis_aclient.get(task_id)

    elif task_type.startswith(TaskType.kling):  # 从个业务线获取: 获取token => 在请求接口 （kling-taskid: cookie）

        mode = "mini" if "vip" not in task_id else ""
        task_id = f"{mode}-image-{task_id}"
        data = await klingai.get_task_plus(task_id, token)
        return data

    elif task_type.startswith(TaskType.vidu):
        data = await vidu_video.get_task(task_id, token)
        return data

    elif task_type == TaskType.runwayml:
        data = await gen.get_task(task_id, token)
        return data

    elif task_type == TaskType.suno:
        data = await suno.get_task(task_id, token)  # todo： 获取任务 失败补偿加你分
        return data

    elif task_type == TaskType.haimian:
        data = await haimian.get_task(task_id, token)
        return data

    elif task_type == TaskType.fish:  # todo: 语音克隆
        data = await suno.get_task(task_id, token)
        return data

    elif task_type == TaskType.cogvideox:
        data = await glm_video.get_task(task_id, token)
        return data

    elif task_type == TaskType.faceswap:
        data = await faceswap.get_task(task_id, token)
        return data

    elif task_type == TaskType.pcedit:
        data = await bdaitpzs.get_task(task_id, token, response_format=response_format)
        return data

    return JSONResponse(content=data, media_type="application/json")


@router.post(f"/tasks/{TaskType.kling}")
async def create_tasks(
        request: KlingaiVideoRequest,
        # task_type: TaskType,
        api_key: Optional[str] = Depends(get_bearer_token),
        vip: Optional[bool] = Query(False),

        background_tasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))

    task_type = TaskType.kling_vip if vip else TaskType.kling

    async with ppu_flow(api_key, post=f"api-{request.model}-{request.mode}-{request.duration}s"):
        task = await klingai_video.create_task(request, vip=vip)
        if task and task.status:
            klingai_video.send_message(f"任务提交成功：\n\n{task.id}")

            await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
            return task.model_dump(exclude={"system_fingerprint"})

        raise HTTPException(status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS, detail=task)


@router.post(f"/tasks/{TaskType.runwayml}")
async def create_tasks(
        request: RunwayRequest,
        # task_type: TaskType,
        auth: Optional[str] = Depends(get_bearer_token),
        upstream_base_url: Optional[str] = Header(None),
        upstream_api_key: Optional[str] = Header(None),
        downstream_base_url: Optional[str] = Header(None),

        background_tasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth
    task_type = TaskType.runwayml

    async with ppu_flow(api_key, post="api-runwayml-gen3"):
        task = await gen.create_task(request)
        if task and task.status:
            gen.send_message(f"任务提交成功：\n\n{task_type}-{task.id}")

            task.id = f"{task_type}-{task.id}"
            await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
            return task.model_dump(exclude={"system_fingerprint"})
        elif task is None:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=task)

        else:
            raise HTTPException(status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS, detail=task)


@router.post(f"/tasks/{TaskType.suno}")
async def create_tasks(
        request: SunoAIRequest,
        # task_type: TaskType,
        auth: Optional[str] = Depends(get_bearer_token),
        upstream_base_url: Optional[str] = Header(None),
        upstream_api_key: Optional[str] = Header(None),
        downstream_base_url: Optional[str] = Header(None),

        background_tasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth
    task_type = TaskType.suno
    token = request.continue_clip_id and await redis_aclient.get(request.continue_clip_id)  # 针对上传的音频
    token = token and token.decode()

    async with ppu_flow(api_key, post="api-sunoai-chirp"):
        pass
        # task = await suno.create_task(request, token)
        # if task and task.status:
        #     suno.send_message(f"任务提交成功：\n\n{task.id}")  # 三种查询方式
        #
        #     await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
        #     for task_id in task.id.split(','):
        #         await redis_aclient.set(task_id, task.system_fingerprint, ex=7 * 24 * 3600)
        #
        #     return task.model_dump(exclude={"system_fingerprint"})
        #
        # else:
        #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=task)


@router.post(f"/tasks/suno-cover")
async def create_tasks(
        request: dict = Body(),  # audio lyrics
        auth: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(request)

    api_key = auth

    async with ppu_flow(api_key, post="api-sunoai-cover"):
        pass
        # task = await suno.create_task_for_cover(request.get("audio"), request.get("lyrics"))
        # if task and task.status:
        #     suno.send_message(f"任务提交成功：\n\n{task.id}")  # 三种查询方式
        #
        #     await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
        #
        #     return task.model_dump(exclude={"system_fingerprint"})
        #
        # else:
        #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=task)


@router.post(f"/tasks/suno-stems")
async def create_tasks(
        request: dict = Body(),  # audio
        auth: Optional[str] = Depends(get_bearer_token),

):
    logger.debug(request)

    api_key = auth

    async with ppu_flow(api_key, post="api-sunoai-stems"):
        pass
        # task = await suno.create_task_for_stems(request.get("audio"))
        # if task and task.status:
        #     suno.send_message(f"任务提交成功：\n\n{task.id}")  # 三种查询方式
        #
        #     await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
        #
        #     return task.model_dump(exclude={"system_fingerprint"})
        #
        # else:
        #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=task)


@router.post(f"/tasks/{TaskType.haimian}")
async def create_tasks(
        request: HaimianRequest,
        auth: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth
    task_type = TaskType.haimian

    async with ppu_flow(api_key, post="api-haimian"):
        task = await haimian.create_task(request)
        if task and task.status:
            haimian.send_message(f"{task_type} 任务提交成功：\n\n{task.id}")

            await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
            return task.model_dump(exclude={"system_fingerprint"})
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=task)


@router.post(f"/tasks/{TaskType.lyrics}")
async def create_tasks(
        request: LyricsRequest,
        # task_type: TaskType,
        auth: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth
    task_type = TaskType.lyrics

    async with ppu_flow(api_key, post="api-sunoai-lyrics"):
        pass
        # if request.model == "haimian":
        #     data = haimian.generate_lyrics(prompt=request.prompt)
        # else:
        #     data = await suno.generate_lyrics(prompt=request.prompt)
        # if isinstance(data, str):
        #     raise HTTPException(status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS, detail=data)  # 内容审核
        #
        # return data


@router.post(f"/tasks/{TaskType.cogvideox}")
async def create_tasks(
        request: VideoRequest,
        # task_type: TaskType,
        auth: Optional[str] = Depends(get_bearer_token),
        upstream_base_url: Optional[str] = Header(None),
        upstream_api_key: Optional[str] = Header(None),
        downstream_base_url: Optional[str] = Header(None),

        background_tasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth
    task_type = TaskType.cogvideox

    token = request.source_list and await redis_aclient.get(request.source_list[0])  # 照片对应的token
    token = token and token.decode()

    async with ppu_flow(api_key, post="official-api-cogvideox"):
        task = await glm_video.create_task(request, token)
        if task and task.status:
            glm_video.send_message(f"{task_type} 任务提交成功：\n\n{task.id}")

            await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)

            return task.model_dump(exclude={"system_fingerprint"})


@router.post(f"/tasks/{TaskType.vidu}")
async def create_tasks(
        request: ViduRequest,
        # task_type: TaskType,
        auth: Optional[str] = Depends(get_bearer_token),
        vip: Optional[bool] = Query(False),

        upstream_base_url: Optional[str] = Header(None),
        upstream_api_key: Optional[str] = Header(None),
        downstream_base_url: Optional[str] = Header(None),

        background_tasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth
    task_type = TaskType.vidu_vip if vip else TaskType.vidu

    token = request.url and await redis_aclient.get(request.url)  # 照片对应的token
    token = token and token.decode()

    async with ppu_flow(api_key, post="api-vidu-vip" if vip else "api-vidu", n=int(np.ceil(request.duration / 4))):
        task = await vidu_video.create_task(request, token, vip)
        logger.debug(task)
        if task and task.status:
            vidu_video.send_message(f"{task_type} 任务提交成功：\n\n{task.id}")

            await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
            return task.model_dump(exclude={"system_fingerprint"})
        else:
            raise HTTPException(status_code=task.status_code, detail=task and task.data)


@router.post(f"/tasks/{TaskType.vidu}-upscale")
async def create_tasks(
        request: ViduUpscaleRequest,
        # task_type: TaskType,
        auth: Optional[str] = Depends(get_bearer_token),

        upstream_base_url: Optional[str] = Header(None),
        upstream_api_key: Optional[str] = Header(None),
        downstream_base_url: Optional[str] = Header(None),

        background_tasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth
    task_type = TaskType.vidu
    vip = 'vip' in request.task_id

    # 任务对应的 token
    token = await redis_aclient.get(request.task_id)
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="Task ID not found")

    async with ppu_flow(api_key, post="api-vidu-vip" if vip else "api-vidu"):
        task = await vidu_video.create_task_upscale(request, token)
        if task and task.status:
            vidu_video.send_message(f"{task_type}-upscale 任务提交成功：\n\n{task.id}")

            await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
            return task.model_dump(exclude={"system_fingerprint"})


@router.post(f"/tasks/{TaskType.faceswap}")
async def create_tasks(
        request: FaceswapRequest,
        auth: Optional[str] = Depends(get_bearer_token),

        background_tasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth
    task_type = TaskType.faceswap
    token = None  ###

    async with ppu_flow(api_key, post=f"api-{task_type}"):
        task = await faceswap.create_task(request, token)
        if task and task.status:
            faceswap.send_message(f"{task_type} 任务提交成功：\n\n{task.id}")

            await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
            return task.model_dump(exclude={"system_fingerprint"})


@router.post(f"/tasks/{TaskType.pcedit}")
async def create_tasks(
        request: BDAITPZSRequest,
        auth: Optional[str] = Depends(get_bearer_token),

        background_tasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth
    task_type = TaskType.pcedit
    token = None

    async with ppu_flow(api_key, post=f"api-{task_type}"):
        task = await bdaitpzs.create_task(request, token)
        if task:
            # bdaitpzs.send_message(f"{task_type} {request.type} 任务提交成功：\n\n{task.id}")

            await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
            return task.model_dump(exclude={"system_fingerprint"})


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

# print(arun(redis_aclient.get("kling-28377631")).decode())
