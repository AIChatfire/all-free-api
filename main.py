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
from free_api.routers import chat_yuanbao, chat_suno, chat_lyrics
from free_api.routers import polling_openai, chat_image, chat_to_audio

from free_api.routers import files, images
from free_api.routers import audio
from free_api.routers import tasks, reranker
from free_api.routers.tools import prompter, translator

app = App()

# Chat
app.include_router(polling_openai.router, '/polling/v1', tags=polling_openai.TAGS)
app.include_router(chat_image.router, '/chat_image/v1', tags=chat_image.TAGS)
app.include_router(chat_to_audio.router, '/chat_to_audio/v1', tags=chat_to_audio.TAGS)

app.include_router(chat_yuanbao.router, '/yuanbao/v1', tags=['腾讯混元'])

app.include_router(chat_suno.router, '/suno/v1', tags=chat_suno.TAGS)
app.include_router(chat_lyrics.router, '/chat_lyrics/v1', tags=chat_lyrics.TAGS)

# Audio
app.include_router(audio.router, '/audio/v1', tags=audio.TAGS)

# Image
app.include_router(images.router, '/images/v1', tags=images.TAGS)

# files
app.include_router(files.router, '/files/v1', tags=files.TAGS)

# 反代
app.include_router(tasks.router, tags=tasks.TAGS)  # 不兼容openai

app.include_router(reranker.router, '/reranker/v1', tags=reranker.TAGS)  # 不兼容openai

# 小工具
app.include_router(prompter.router, '/tools/v1', tags=prompter.TAGS)
app.include_router(translator.router, '/tools/v1', tags=translator.TAGS)

if __name__ == '__main__':
    app.run()

# python3 -m meutils.clis.server gunicorn-run smooth_app:app --pythonpath python3 --port 39006
