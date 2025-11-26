#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : cherry
# @Time         : 2025/11/25 13:03
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from fastapi import FastAPI, Query, HTTPException

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers

from fastapi.responses import RedirectResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body

router = APIRouter()

app = FastAPI(title="Cherry Studio URL Generator")


@router.get("/")
async def root():
    return {"message": "Cherry Studio 链接生成器，访问 /redirect 接口"}


@router.get("/{biz:path}", response_class=RedirectResponse)
async def generate_and_redirect(
        biz: str,
        id: str = Query("🔥ChatfireAI", description="提供商ID"),
        name: str = Query("🔥ChatfireAI", description="显示名称"),
        api_key: str = Query("{api_key}", alias="api_key", description="API密钥"),
        base_url: str = Query("https://api.chatfire.cn/v1", alias="base_url", description="基础URL"),
        provider_type: str = Query("openai", alias="type", description="提供商类型")
):
    """
    生成 Cherry Studio 自定义协议链接并重定向

    示例：/redirect?id=MyAI&name=MyAI&apiKey=sk-xxx&baseUrl=https://api.example.com/v1&type=openai
    """
    logger.debug(api_key)

    try:
        if biz.startswith("cherry"):
            # 构建数据对象
            data = {
                "id": id,
                "baseUrl": base_url,
                "apiKey": api_key,
                "name": name,
                "type": provider_type
            }

            # 转换为JSON字符串并Base64编码
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            base64_data = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

            # 构建目标URL（使用自定义协议）
            target_url = f"cherrystudio://providers/api-keys?v=1&data={base64_data}"

            # 返回重定向响应
            # 注意：浏览器需要支持自定义协议才能正确打开
            return RedirectResponse(
                url=target_url,
                status_code=302  # 临时重定向
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成链接失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
