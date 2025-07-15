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
from meutils.io.files_utils import to_url, get_file_duration, to_bytes

from meutils.apis.utils import make_request_httpx
from meutils.apis.oneapi.user import get_user_money
from meutils.llm.openai_utils.billing_utils import billing_for_tokens

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers
from meutils.serving.fastapi.dependencies.auth import parse_token

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi import File, UploadFile, Header, Query, Form, Body, Request

router = APIRouter()
TAGS = ["通用同步任务"]  # 兼容formdata


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

    upstream_base_url = headers.get('upstream_base_url') or "https://api.elevenlabs.io"
    upstream_api_key = headers.get('upstream_api_key')  # 上游号池管理
    upstream_api_key = await parse_token(upstream_api_key)

    upstream_path = headers.get('upstream_path') or path  # 路径不一致的时候要传 upstream_post_path

    # 获取请求体
    params = dict(request.query_params)

    # form_data
    prompt_tokens = 0  # todo 部分模型按量计费
    data = files = None
    payload = {}
    if data := (await request.form())._dict:
        file = data.get("file")

        if isinstance(file, UploadFile):
            file: UploadFile = data.pop("file", None)

            content = file.file.read()
            files = {"file": (file.filename, content)}
        else:
            content = await to_bytes(file)
            filename = Path(file).name if isinstance(file, str) else 'xx'
            files = {"file": (filename, content)}

    else:  # payload
        payload = await request.json()

    # 获取模型名称
    model = (
            payload.get("model")
            or payload.get("model_name")
            or payload.get("search_engine")
            or upstream_model
            or (upstream_model_key and payload.get(upstream_model_key))
            or "UNKNOWN"
    )

    # 执行
    async with atry_catch(
            f"{model}", callback=send_message, request=payload,
            upstream_base_url=upstream_base_url,
            upstream_api_key=upstream_api_key,
    ):
        # 检查余额
        if user_money := await get_user_money(api_key):
            if user_money < 1:
                raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="余额不足")

        # 执行逻辑
        response = await make_request_httpx(
            base_url=upstream_base_url,

            path=upstream_path,
            params=params,
            payload=payload,
            data=data,
            files=files,
            # headers=headers,

            debug=True
        )

        # 计费
        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": 0,
            "total_tokens": prompt_tokens
        }
        N = 1 if prompt_tokens == 0 else None
        await billing_for_tokens(model=f"{model}", api_key=api_key, usage=usage, n=N)

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
