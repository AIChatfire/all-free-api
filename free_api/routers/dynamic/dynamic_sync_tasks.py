#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : common
# @Time         : 2024/12/20 16:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 内置接口: 不计费

from meutils.pipe import *

from meutils.decorators.contextmanagers import atry_catch
from meutils.notice.feishu import send_message_for_dynamic_router as send_message

from meutils.apis.utils import make_request
from meutils.llm.openai_utils import ppu_flow, get_payment_times

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers
from meutils.serving.fastapi.dependencies.auth import parse_token

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi import File, UploadFile, Header, Query, Form, Body, Request

router = APIRouter()
TAGS = ["通用同步任务"]


@router.api_route("/{biz}/v1/{path:path}", methods=["GET", "POST"])
async def create_async_task(
        request: Request,

        biz: str,  # 业务类型
        path: str,  # response_model 计费模型

        api_key: Optional[str] = Depends(get_bearer_token),
        headers: dict = Depends(get_headers),

):
    logger.debug(f"biz: {biz}; path: {path}")
    logger.debug(bjson(headers))

    # 上游信息
    upstream_model = headers.get('upstream_model')
    upstream_model_key = headers.get('upstream_model_key')  # 从payload中映射

    upstream_base_url = headers.get('upstream_base_url')
    upstream_api_key = headers.get('upstream_api_key')  # 上游号池管理
    upstream_api_key = await parse_token(upstream_api_key)

    upstream_path = headers.get('upstream_path') or path  # 路径不一致的时候要传 upstream_post_path

    # 获取请求体 todo: formdata
    payload = await request.json()  # get 可能没有

    # 获取模型名称
    model = (
            payload.get("model")
            or payload.get("model_name")
            or payload.get("search_engine")
            or upstream_model
            or (upstream_model_key and payload.get(upstream_model_key))
            or "UNKNOWN"
    )
    # 计费次数
    N = 1

    # 执行
    async with atry_catch(f"{model}", callback=send_message, request=payload,
                          upstream_base_url=upstream_base_url,
                          upstream_api_key=upstream_api_key,
                          ):
        async with ppu_flow(api_key, post=model, n=N, dynamic=True):
            response = await make_request(
                base_url=upstream_base_url,
                api_key=upstream_api_key,

                path=upstream_path,
                payload=payload,
                params=dict(request.query_params),

                method=request.method,
                headers=headers
            )

            return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/sync')

    app.run()

"""
UPSTREAM_BASE_URL="https://ai.gitee.com/v1"
UPSTREAM_API_KEY="5PJFN89RSDN8CCR7CRGMKAOWTPTZO6PN4XVZV2FQ"
API_KEY=sk-R6y5di2fR3OAxEH3idNZIc4sm3CWIS4LAzRfhxSVbhXrrIej

curl -X 'POST' 'http://0.0.0.0:8000/sync/gitee/v1/rerank' \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY" \
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

    
"""
