#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : images
# @Time         : 2024/7/8 14:27
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
from aiostream import stream

from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from meutils.schemas.wechat_types import Message, HookResponse

from meutils.apis.kling import images as kling_image

from meutils.apis.vidu import vidu_video
from meutils.schemas.vidu_types import ViduRequest

from meutils.apis.siliconflow.text_to_image import create
from meutils.schemas.image_types import ImageRequest
from meutils.io.image import image2nowatermark_image
from meutils.str_utils.regular_expression import parse_url

from meutils.apis.hf import got_ocr
from meutils.schemas.ocr_types import OCRRequest

from meutils.apis.textcard import hanyuxinjie

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["HOOK"]


@router.post("/wechat")  # todo: sd3 兜底，增加 key
async def create_reply(
        request: Message,
        auth: Optional[str] = Depends(get_bearer_token),
):
    api_key = auth

    logger.debug(request.model_dump_json(indent=4))

    responses = []
    content = request.Content.split(maxsplit=1)[-1]  # request.Content = "@firebot /flux-pro 一条狗"
    if content.startswith(('/v', '/video')):
        prompt = content.strip('/video').split('/v')[-1]

        video_request = ViduRequest(prompt=prompt)
        task = await vidu_video.create_task(video_request)

        for i in range(1, 16):
            await asyncio.sleep(10 / i)
            try:
                data = await vidu_video.get_task(task.id, task.system_fingerprint)
                if data.get("state") == "success":
                    video_url = data.get("creations")[0].get("uri")
                    responses += [HookResponse(content=f"任务已完成🎉🎉🎉\nTaskId: {task.id}")]
                    responses += [HookResponse(type='video', content=video_url)]
                    logger.debug(responses)
                    break
            except Exception as e:
                logger.debug(e)
                continue

    elif content.startswith('/flux-pro'):
        prompt = content.split(maxsplit=1)[-1]

        image_reponse = await create(ImageRequest(prompt=prompt, model="black-forest-labs/FLUX.1-dev"))
        responses += [HookResponse(type='image', content=img.url) for img in image_reponse.data]
        logger.debug(responses)

    elif content.startswith('/kling'):
        prompt = content.split(maxsplit=1)[-1]
        # 图生图
        urls = parse_url(prompt, for_image=True)
        url = None
        if urls:
            url = urls[0]
            prompt = prompt.replace(url, '')

        request = kling_image.ImageRequest(prompt=prompt, image=url, n=2)
        task = await kling_image.create_task(request, vip=True)

        for i in range(1, 16):
            await asyncio.sleep(15 / i)
            try:
                data = await kling_image.get_task(task.data.task_id, task.system_fingerprint, oss="glm")
                logger.debug(data)

                for image in data.data.task_result.get('images', []):
                    if url := image.get("url"):
                        responses += [HookResponse(type='image', content=url)]
                logger.debug(responses)
                break
            except Exception as e:
                logger.debug(e)
                continue

    elif content.startswith('/ocr'):
        prompt = content.split(maxsplit=1)[-1]
        urls = parse_url(prompt, for_image=True)
        url = None
        if urls:
            url = urls[0]
            prompt = prompt.replace(url, '').strip().replace('ocr', "OCR")

        modes = {
            'plain texts OCR', 'plain multi-crop OCR', 'plain fine-grained OCR',
            'format texts OCR', 'format multi-crop OCR', 'format fine-grained OCR'
        }

        mode = prompt if prompt in modes else "plain texts OCR"

        request = OCRRequest(
            image=urls[0],
            mode=mode,
        )
        try:

            ocr_text, rendered_html = await got_ocr.create(request)
            responses += [HookResponse(content=ocr_text)]

            logger.debug(responses)
        except Exception as e:
            pass

    elif content.startswith('/去水印'):
        urls = parse_url(content, for_image=True)
        for url in urls:
            url = await image2nowatermark_image(url)
            responses += [HookResponse(type="image", content=url)]

        logger.debug(responses)

    elif content.startswith('/汉语新解'):
        prompt = content.split(maxsplit=1)[-1]
        chunks = await stream.list(hanyuxinjie.create(prompt))
        html_content = "".join(chunks)
        htmls = hanyuxinjie.HTML_PARSER.findall(html_content)
        html_content = htmls and htmls[-1] or html_content
        html_content = html_content.replace("```", "")
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.html', delete=False) as file:
            # logger.debug(file.name)
            file.write(html_content)
            file.seek(0)
            url = f"https://api.chatfire.cn/render/{file.name}"
            responses += [HookResponse(content=url)]

    elif content.startswith('/换衣'):
        from meutils.apis.hf import kolors_virtual_try_on
        urls = parse_url(content, for_image=True)

        if len(urls):
            request = kolors_virtual_try_on.KolorsTryOnRequest(
                human_image=urls[0],
                cloth_image=urls[-1]
            )

            data = await kolors_virtual_try_on.create(request)
            url = data["data"][0]["url"]
            responses += [
                HookResponse(type="image", content=url),
                HookResponse(type="image", content=request.human_image),
            ]

    return responses


if __name__ == '__main__':
    # from meutils.serving.fastapi import App
    #
    # app = App()
    #
    # app.include_router(router, '/v1')
    #
    # app.run()

    async def main():

        prompt = "画条狗"

        request = kling_image.ImageRequest(prompt=prompt, n=2)
        task = await kling_image.create_task(request, vip=True)

        responses = []
        with timer():
            for i in range(1, 16):
                await asyncio.sleep(15 / i)
                try:
                    data = await kling_image.get_task(task.data.task_id, task.system_fingerprint, oss='glm')
                    logger.debug(data)

                    for image in data.data.task_result.get('images', []):
                        url = image.get("url")
                        responses += [HookResponse(type='image', content=url)]
                    logger.debug(responses)
                    break
                except Exception as e:
                    logger.debug(e)


    arun(main())
