#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : common
# @Time         : 2024/12/20 16:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 适合适配于第三方接口
# 动态路由
import shortuuid

from meutils.pipe import *

from meutils.db.redis_db import redis_aclient
from meutils.decorators.contextmanagers import atry_catch
from meutils.notice.feishu import send_message_for_dynamic_router as send_message

from meutils.apis.utils import make_request
from meutils.schemas.task_types import FluxTaskResponse

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi import File, UploadFile, Header, Query, Form, Body, Request

router = APIRouter()
TAGS = ["通用异步任务", "通用同步任务"]


# 渠道错乱会导致失败，可删除重建
@router.api_route("/flux/v1/{model:path}", methods=["GET", "POST"])  # 走bfl接口透传
async def create_async_task(
        request: Request,
        model: str,  # response_model 计费模型

        id: str = Query(None, description="The ID of the task."),  # local task id

        headers: dict = Depends(get_headers),
        api_key: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(f"model: {model}; api_key: {api_key}")
    logger.debug(bjson(headers))

    if request.method == "GET":  # 同步成功了，异步任务也成功了
        if response := await redis_aclient.get(f"response:{id}"):
            # logger.debug(f"response type: {type(response)}")
            # logger.debug(f"response: {response}")

            response = json.loads(response)
            return response

    # 上游信息
    upstream_base_url, api_key = api_key.split('|')  # 必须配置

    # 获取请求体 todo: formdata
    payload = await request.json()

    async with atry_catch(f"{model}", api_key=api_key, callback=send_message,
                          upstream_base_url=upstream_base_url, request=payload):

        response = await make_request(
            base_url=upstream_base_url,
            payload=payload,

            api_key=api_key,
            method=request.method
        )

        task_id = shortuuid.random()
        response['id'] = task_id

        # 异步任务信号
        flux_task_response = FluxTaskResponse(id=task_id, result=response, status="Ready")
        await redis_aclient.set(f"response:{task_id}", flux_task_response.model_dump_json(exclude_none=True), ex=3600)

        logger.debug(flux_task_response.model_dump_json(exclude_none=True, indent=4))

        return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/async2sync')

    app.run()

"""
API_KEY="https://ai.gitee.com/v1/rerank|5PJFN89RSDN8CCR7CRGMKAOWTPTZO6PN4XVZV2FQ"

curl -X 'POST' 'http://0.0.0.0:8000/async2sync/flux/v1/Qwen3-Reranker-8B' \
    -H "Authorization: Bearer $API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
        "query": "How to read a CSV file in Python?",
        "documents": [
            "You can read CSV files with numpy.loadtxt()",
            "To write JSON files, use json.dump() in Python",
            "CSV means Comma Separated Values. Python files can be opened using read() method."
        ],
        "model": "Qwen3-Reranker-8B"
    }'
    
API_KEY="https://ai.gitee.com/v1/rerank|5PJFN89RSDN8CCR7CRGMKAOWTPTZO6PN4XVZV2FQ"

curl -X 'POST' 'https://openai-dev.chatfire.cn/async2sync/flux/v1/Qwen3-Reranker-8B' \
    -H "Authorization: Bearer $API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
        "query": "How to read a CSV file in Python?",
        "documents": [
            "You can read CSV files with numpy.loadtxt()",
            "To write JSON files, use json.dump() in Python",
            "CSV means Comma Separated Values. Python files can be opened using read() method."
        ],
        "model": "Qwen3-Reranker-8B"
    }'
    
API_KEY="https://ai.gitee.com/v1/rerank|5PJFN89RSDN8CCR7CRGMKAOWTPTZO6PN4XVZV2FQ"

curl -X 'GET' 'https://openai-dev.chatfire.cn/async2sync/flux/v1/get_result?id=8dYZLBnv9TG8k6JMHc6Kpp' \
    -H "Authorization: Bearer $API_KEY"

API_KEY="https://ai.gitee.com/v1/rerank|5PJFN89RSDN8CCR7CRGMKAOWTPTZO6PN4XVZV2FQ"
curl -X 'GET' 'http://0.0.0.0:8000/async2sync/flux/v1/get_result?id=8dYZLBnv9TG8k6JMHc6Kpp' \
    -H "Authorization: Bearer $API_KEY"
    
"""
