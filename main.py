#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : app.py
# @Time         : 2023/12/15 15:13
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.serving.fastapi import App
from free_api.routers import chat_yuanbao
from free_api.routers import chat_suno
from free_api.routers import files, images
from free_api.routers import polling_openai
from free_api.routers import audio
from free_api.routers import reranker

app = App()

app.include_router(polling_openai.router, '/polling/v1', tags=['OpenAI轮询'])

app.include_router(chat_yuanbao.router, '/yuanbao/v1', tags=['腾讯混元'])
app.include_router(chat_suno.router, '/suno/v1', tags=['SunoAI'])
app.include_router(audio.router, '/audio/v1', tags=audio.TAGS)
app.include_router(images.router, '/images/v1', tags=images.TAGS)  # 转发：todo 反代

# 反代
app.include_router(files.router, '/files-extraction/v1', tags=files.TAGS)
app.include_router(reranker.router, '/reranker/v1', tags=reranker.TAGS)  # 不兼容openai

if __name__ == '__main__':
    app.run()

# python3 -m meutils.clis.server gunicorn-run smooth_app:app --pythonpath python3 --port 39006
