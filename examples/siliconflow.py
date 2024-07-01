#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : siliconflow
# @Time         : 2024/6/26 17:30
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
import requests
import json
# from fake_useragent import UserAgent
# ua = UserAgent()
import requests
import json

url = "https://cloud.siliconflow.cn/api/model/text2img?modelName=stabilityai/stable-diffusion-3-medium&modelSubType=text-to-image"

payload = {
    "image_size": "1024x1024",
    "batch_size": 1,
    "num_inference_steps": 25,
    "guidance_scale": 4.5,
    "prompt": "Man snowboarding on the mars, ultra high resolution 12k"
}
headers = {

    'Cookie': '__Host-authjs.csrf-token=e0ef45d98025e394212b732a5fff6a0fb85d413a1b4cc9fb6518f63f7cdd4feb%7C692f34c1ea27fc3d5d97f0c104ee5ee0bcf3d85c1f72a771acbbd6a8df0d39fa; __Secure-authjs.callback-url=https%3A%2F%2Fcloud.siliconflow.cn; Hm_lvt_85d0fa672fe1e9cf21f0253958808923=1719368752; Hm_lpvt_85d0fa672fe1e9cf21f0253958808923=1719393853; _ga_FS03N2E4YL=GS1.1.1719393547.4.1.1719393856.0.0.0; __Secure-authjs.session-token=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwia2lkIjoiZ3dNNWRzR3hqS1RxVnF4cTBrRmVyNElJYy1RMkhRZ01wVUFRSjRsTTkwQzVhZVhmN2RLNlZuOGFHTjlULTBsWVFoYkxiUE9LaEI5a2h3ZmJ6N0Y0NXcifQ..68vCEbXryIWYOGZu-hVnHQ.WCLg9u-CfGJHpeuYkPmG8v0daHmlOWkyc6BytcYDbTzRoRy0c640X68n37UpV6IaqpxF3xn18HqSZ1bUeqGxkLusR3LamnFJfTaNK6Y2S9TrI-NevjyR1_wFfawX-FEXEyzeHgwhzZgmrvCs78Kxhq3qW-nhNQ9BUuSQG56V4p7ymhikrHcbGZ4hvOG4C1cLOzXB1oWHuWMC976JaxxMBy0uS3q6nACbrHt-kK_d2LApZeahBmpQzhK0yjuSUggT.OJm_S_HyXYzFLNbd95ahx-eEkFVLKNVPyWGtmf0adI4',
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'content-type': 'application/json'
}

response = httpx.post(url, headers=headers, json=payload, timeout=100)

print(response.text)
