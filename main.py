#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : app.py
# @Time         : 2023/12/15 15:13
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 域名区分下？

from meutils.serving.fastapi import App

from free_api.routers.oai import polling as oai_polling

from free_api.routers import openai_spark, openai_plus, openai_deep2x, openai_assistants
from free_api.routers import openai_agent, openai_adapter, openai_redirect
from free_api.routers import chat_image, chat_to_audio, chat_video, chat_suno

from free_api.routers import test
from free_api.routers import files, tasks

from free_api.routers.oneapi import oneapi, usage
from free_api.routers.async_tasks import kling, kling_pro, cogvideox, hailuo, hailuo_pro, siliconflow_videos
from free_api.routers.async_tasks import seededit, jimeng, volcengine_apis, veo
from free_api.routers.async_tasks import fal, fal_kling  # , kling_apis
from free_api.routers.async_tasks import fal, fal_kling, fal_ai

from free_api.routers.audio import v1 as audio_v1, fish, tts

from free_api.routers.images import biz as images_biz
from free_api.routers.images import v1 as images_v1
from free_api.routers.images import dynamic_routers as images

from free_api.routers.crawler import reader
from free_api.routers.search import web_search

from free_api.routers.aitools import document_intelligence, images as aitools_images
from free_api.routers.tools import prompter, translator, imager, news, textcard, templates, text_to_url

# 采购
from free_api.routers.textin import v1 as textin_v1

app = App()

# 空服务
app.include_router(test.router, '/v0', tags=test.TAGS)

# 信息类
app.include_router(openai_assistants.router, '/assistants/v1', tags=openai_assistants.TAGS)

app.include_router(openai_plus.router, '/plus', tags=openai_plus.TAGS)
app.include_router(openai_agent.router, '/agent', tags=openai_agent.TAGS)
app.include_router(openai_spark.router, '/spark', tags=openai_spark.TAGS)
app.include_router(openai_deep2x.router, '/deep2x', tags=openai_deep2x.TAGS)

app.include_router(openai_redirect.router, '/redirect', tags=openai_redirect.TAGS)  # todo: 更通用
app.include_router(openai_adapter.router, '/adapter', tags=openai_adapter.TAGS)  # todo: 更通用

# polling/chat
# polling/images
app.include_router(oai_polling.router, '/polling/v1', tags=oai_polling.TAGS)

app.include_router(chat_image.router, '/chat_image/v1', tags=chat_image.TAGS)
app.include_router(chat_to_audio.router, '/chat_to_audio/v1', tags=chat_to_audio.TAGS)

app.include_router(chat_suno.router, '/suno/v1', tags=chat_suno.TAGS)

app.include_router(chat_video.router, '/chat_video/v1', tags=chat_video.TAGS)

# Audio
app.include_router(audio_v1.router, '/v1', tags=audio_v1.TAGS)
app.include_router(fish.router, '/fish', tags=fish.TAGS)
app.include_router(tts.router, '/audio/v1', tags=tts.TAGS)  #######

# Images
app.include_router(images.router, '/images/v1', tags=images.TAGS)  # todo：未来以这个为准

app.include_router(images_biz.router, '', tags=images_biz.TAGS)  # 适配其他渠道
app.include_router(images_v1.router, '/v1', tags=images_v1.TAGS)

# files
app.include_router(files.router, '/v1', tags=files.TAGS)  ########## 废弃

# 异步任务 async_tasks
# 通用异步接口
# app.include_router(seededit.router, '/async/v1', tags=seededit.TAGS)

app.include_router(seededit.router, '/seededit/v1', tags=seededit.TAGS)

app.include_router(fal_ai.router, '/fal-ai/v1', tags=fal_ai.TAGS)

app.include_router(fal.router, '/lipsync/v1', tags=fal.TAGS)
app.include_router(fal_kling.router, '/kling-video/v1', tags=fal_kling.TAGS)
app.include_router(jimeng.router, '/jimeng-video/v1', tags=jimeng.TAGS)

app.include_router(veo.router, '/veo/v1', tags=veo.TAGS)

# 火山
app.include_router(volcengine_apis.router, '/volc', tags=volcengine_apis.TAGS)

app.include_router(cogvideox.router, '/cogvideox/v1', tags=cogvideox.TAGS)
# app.include_router(kling.router, '/kling/v1', tags=kling.TAGS)
# app.include_router(kling_apis.router, '/kling_apis', tags=kling_apis.TAGS)

app.include_router(hailuo.router, '/hailuo/v1', tags=hailuo.TAGS)
# app.include_router(hailuo_pro.router, '/hailuo-pro/v1', tags=hailuo.TAGS)

app.include_router(siliconflow_videos.router, '/v1/videos', tags=siliconflow_videos.TAGS)

# app.include_router(tripo3d.router, '/tripo3d/v1', tags=tripo3d.TAGS)

# 反代
app.include_router(tasks.router, tags=tasks.TAGS)  # 不兼容openai
app.include_router(tasks.router, tags=tasks.TAGS)  # 不兼容openai

# 小工具
app.include_router(aitools_images.router, '/aitools/v1', tags=aitools_images.TAGS)
app.include_router(document_intelligence.router, '/aitools', tags=document_intelligence.TAGS)  # 文档智能： todo: 标准化

app.include_router(templates.router, tags=templates.TAGS)
app.include_router(prompter.router, '/tools/v1', tags=prompter.TAGS)
app.include_router(translator.router, '/tools/v1', tags=translator.TAGS)
app.include_router(imager.router, '/tools/v1', tags=imager.TAGS)
app.include_router(news.router, '/tools/v1', tags=news.TAGS)
# app.include_router(processor.router, '/tools/processor/v1', tags=processor.TAGS)
app.include_router(textcard.router, '/tools/textcard/v1', tags=textcard.TAGS)
app.include_router(text_to_url.router, '/tools/v1', tags=text_to_url.TAGS)

# 搜索与爬虫
app.include_router(reader.router, '/crawler/reader', tags=reader.TAGS)
app.include_router(web_search.router, '/search/v1', tags=web_search.TAGS)

# Hook

# ONEAPI: extra-api
app.include_router(oneapi.router, '/oneapi', tags=oneapi.TAGS)
app.include_router(usage.router, '/usage', tags=usage.TAGS)  # 计费系统

# 采购项
app.include_router(textin_v1.router, '/textin/v1', tags=textin_v1.TAGS)

if __name__ == '__main__':
    app.run()

# python3 -m meutils.clis.server gunicorn-run smooth_app:app --pythonpath python3 --port 39006
