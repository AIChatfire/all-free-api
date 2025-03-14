#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : suno
# @Time         : 2024/6/25 09:41
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :


from meutils.pipe import *
from meutils.schemas.openai_types import ChatCompletionRequest
from meutils.schemas.suno_types import SunoAIRequest
from meutils.apis.sunoai import suno, suno_api

template = """


- 自动歌词懒人模式
```
gpt_description_prompt: 写首中国风的歌曲
```

- 自定义歌词模式(每行逗号分割)
```
mv: chirp-v3-5,
title: "这里是歌词标题",
prompt: "这里是你的自定义歌词：吧啦吧啦"
```

- 官网的标准模式(json结构)
```json
{
    "prompt": "",
    "gpt_description_prompt": "写首中国风的歌曲",
    "title": "",
    "tags": "",
    "continue_at": null,
    "continue_clip_id": null,
    "infill_start_s": null,
    "infill_end_s": null,
    "make_instrumental": false,
    "mv": "chirp-v3-5"
}
```
"""


class Completions(object):

    def __init__(self, api_key):
        self.api_key = api_key

    async def create(self, request: ChatCompletionRequest):
        if isinstance(request.last_content, str) and request.last_content.startswith(  # 跳过nextchat
                ("hi",
                 "使用四到五个字直接返回这句话的简要主题",
                 "简要总结一下对话内容，用作后续的上下文提示 prompt，控制在 200 字以内")):
            return "请关闭nextchat上下文总结，避免不必要的浪费"

        if all(i not in request.last_content for i in {"prompt", "make_instrumental"}):  # 无字段标识，默认 gpt创作
            request = SunoAIRequest(gpt_description_prompt=request.last_content)

        else:
            data = json_repair.repair_json(f"{{{request.last_content}}}", return_objects=True)
            if isinstance(data, dict) and data:
                request = SunoAIRequest(**data)
            else:
                return f"请按照规定格式提交任务（未知错误联系管理员）\n\n {template}"

        task_id = await suno_api.create_task(request)
        logger.debug(task_id)

        # task_id = "5dc4c01c-7e7b-2d94-9868-f5f9742248cc"
        return create_chunks(task_id)


def music_info(df):
    """
    #   'audio_url': 'https://cdn1.suno.ai/63c85335-d8ec-4e17-882a-e51c2f358b2d.mp3',
    #   'video_url': 'https://cdn1.suno.ai/25c7e34b-6986-4f7c-a5f2-537dd80e370c.mp4',
    # https://cdn1.suno.ai/image_bea09d9e-be4a-4c27-a0bf-67c4a92d6e16.png
    :param df:
    :return:
    """
    logger.debug(df)

    df['🎵音乐链接'] = df['id'].map(
        lambda x: f"**请两分钟后试听**[🎧音频](https://cdn1.suno.ai/{x}.mp3)[▶️视频](https://cdn1.suno.ai/{x}.mp4)"
    )
    # todo: 图片链接发生变化
    df['专辑图'] = df['id'].map(lambda x: f"![🖼](https://cdn1.suno.ai/image_{x}.jpeg)")  # _large

    df_ = df[["id", "mv", "🎵音乐链接", "专辑图"]]

    return f"""
🎵 **「{df['title'][0]}」**

`风格: {df['tags'][0]}`

```toml
{df['prompt'][0]}
```


{df_.to_markdown(index=False).replace('|:-', '|-').replace('-:|', '-|')}
    """


async def create_chunks(task_id):
    yield "✅开始生成音乐\n\n"
    await asyncio.sleep(1)

    yield f"任务ID：{task_id}\n\n"

    # yield f"音乐ID：\n"
    # for clip_id in clip_ids:
    #     yield f"- [{clip_id}](https://cdn1.suno.ai/{clip_id}.mp3)\n\n"
    #     await asyncio.sleep(1)

    yield f"""[🔥音乐进度]("""
    await asyncio.sleep(1)

    for i in range(100):
        await asyncio.sleep(1) if i < 10 else await asyncio.sleep(3)

        # 监听歌曲
        data = await suno_api.get_task(task_id)
        logger.debug(bjson(data))

        clips = data.get("data").get("data")

        STATUS = {"streaming", "complete", "error", "running"}  # submitted queued streaming complete/error
        if clips and all(clip.get('status') in STATUS for clip in clips):  # 可提前返回
            yield f""") ✅\n\n"""
            df = pd.DataFrame(clips)
            df['tags'] = [clip.get('tags') for clip in clips]
            df['prompt'] = [clip.get('prompt') for clip in clips]
            md_string = music_info(df)
            yield md_string  # yield from
            break
        else:
            yield f"""{'🎵' if i % 2 else '🔥'}"""


    else:
        yield "长时间未获取或者中断，可从超链接获取音乐"


if __name__ == '__main__':
    task_id = "5d10ae83-a0ee-205d-dc3f-f67ceb791496"

    # arun(create_chunks(task_id))

    # arun(Completions('x').create(ChatCompletionRequest(messages=[{'role': 'user', 'content': '写一首中国风的歌曲'}])))
