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

from free_api.routers import search
from free_api.routers import chat_yuanbao, chat_suno, chat_lyrics
from free_api.routers import openai_agent, openai_adapter, openai_polling, openai_redirect, chatfire_all, vision_llm
from free_api.routers import chat_image, chat_to_audio, chat_video

from free_api.routers import test
from free_api.routers import files, tasks, reranker

from free_api.routers.goamz import suno
from free_api.routers.hooks import wechat
from free_api.routers.oneapi import extra_api as oneapi
from free_api.routers.cv import ocr
from free_api.routers.async_tasks import replicateai, kling, kling_pro, cogvideox, hailuo, hailuo_pro, tripo3d, hunyuan
from free_api.routers.async_tasks import seededit

from free_api.routers.audio import v1 as audio_v1, fish
from free_api.routers.images import v1 as images_v1, virtual_try_on

from free_api.routers.aitools import document_intelligence, images as aitools_images
from free_api.routers.tools import prompter, translator, imager, news, textcard, templates, watermark

app = App()

# 空服务
app.include_router(test.router, '/v0', tags=test.TAGS)

# search
app.include_router(search.router, '/v1', tags=search.TAGS)

# Chat
app.include_router(openai_agent.router, '/agent', tags=openai_agent.TAGS)
app.include_router(openai_redirect.router, '/redirect', tags=openai_redirect.TAGS)
app.include_router(openai_adapter.router, '/adapter/v1', tags=openai_adapter.TAGS)
app.include_router(openai_polling.router, '/polling/v1', tags=openai_polling.TAGS)
app.include_router(vision_llm.router, '/vision/v1', tags=vision_llm.TAGS)

app.include_router(chat_image.router, '/chat_image/v1', tags=chat_image.TAGS)
app.include_router(chat_to_audio.router, '/chat_to_audio/v1', tags=chat_to_audio.TAGS)

app.include_router(chat_yuanbao.router, '/yuanbao/v1', tags=['腾讯混元'])

app.include_router(chat_suno.router, '/suno/v1', tags=chat_suno.TAGS)
app.include_router(chat_lyrics.router, '/chat_lyrics/v1', tags=chat_lyrics.TAGS)

app.include_router(chat_video.router, '/chat_video/v1', tags=chat_video.TAGS)

app.include_router(chatfire_all.router, '/all/v1', tags=chatfire_all.TAGS)

# Audio
app.include_router(audio_v1.router, '/v1', tags=audio_v1.TAGS)  # 反代
app.include_router(fish.router, '/fish', tags=fish.TAGS)

# Images
app.include_router(images_v1.router, '/v1', tags=images_v1.TAGS)  # 反代
app.include_router(virtual_try_on.router, '/v1', tags=virtual_try_on.TAGS)

# files
app.include_router(files.router, '/v1', tags=files.TAGS)

# CV
app.include_router(ocr.router, '/ocr/v1', tags=ocr.TAGS)

# 异步任务 async_tasks
app.include_router(seededit.router, '/seededit/v1', tags=seededit.TAGS)

app.include_router(replicateai.router, '/replicate/v1', tags=replicateai.TAGS)

app.include_router(cogvideox.router, '/cogvideox/v1', tags=cogvideox.TAGS)
app.include_router(kling.router, '/kling/v1', tags=kling.TAGS)
app.include_router(kling_pro.router, '/kling_pro/v1', tags=kling_pro.TAGS)

app.include_router(hailuo.router, '/hailuo/v1', tags=hailuo.TAGS)
app.include_router(hailuo_pro.router, '/hailuo-pro/v1', tags=hailuo.TAGS)

app.include_router(hunyuan.router, '/hunyuan/v1', tags=hunyuan.TAGS)

app.include_router(tripo3d.router, '/tripo3d/v1', tags=tripo3d.TAGS)

# 反代
app.include_router(tasks.router, tags=tasks.TAGS)  # 不兼容openai

app.include_router(reranker.router, '/reranker/v1', tags=reranker.TAGS)  # 不兼容openai

# 小工具
app.include_router(aitools_images.router, '/aitools', tags=aitools_images.TAGS)
app.include_router(document_intelligence.router, '/aitools', tags=document_intelligence.TAGS)  # 文档智能： todo: 标准化

app.include_router(templates.router, tags=templates.TAGS)
app.include_router(prompter.router, '/tools/v1', tags=prompter.TAGS)
app.include_router(translator.router, '/tools/v1', tags=translator.TAGS)
app.include_router(imager.router, '/tools/v1', tags=imager.TAGS)
app.include_router(news.router, '/tools/v1', tags=news.TAGS)
# app.include_router(processor.router, '/tools/processor/v1', tags=processor.TAGS)
app.include_router(textcard.router, '/tools/textcard/v1', tags=textcard.TAGS)
app.include_router(watermark.router, '/tools/v1', tags=watermark.TAGS)

# GOAMZ
app.include_router(suno.router, '/goamz/v1', tags=suno.TAGS)
app.include_router(suno.router, '/suno/v1', tags=suno.TAGS)

# Hook
app.include_router(wechat.router, '/hooks/v1', tags=wechat.TAGS)

# ONEAPI: extra-api
app.include_router(oneapi.router, '/oneapi', tags=oneapi.TAGS)

if __name__ == '__main__':
    app.run()

# python3 -m meutils.clis.server gunicorn-run smooth_app:app --pythonpath python3 --port 39006
