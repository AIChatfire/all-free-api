#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : demo
# @Time         : 2024/6/19 12:12
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
import requests
import json

url = "https://yuewen.cn/api/proto.chat.v1.ChatMessageService/SendMessageStream"

token = "...eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOjEwMjAwLCJkZXZpY2VfaWQiOiJkOGMzZmQyMDNiMDVkZDYyNWRhMjE0NzExZmZmYTc1YjM2YWUzMDIzIiwiZXhwIjoxNzIwOTE5NDAxLCJvYXNpc19pZCI6ODM1NDcxMjc1MDIwMTI0MTYsInBsYXRmb3JtIjoid2ViIiwidmVyc2lvbiI6Mn0.DOucHDLLquvRvynk1MczqUEHvQE6tfuAINXAnY2qBgQ"
token = f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY3RpdmF0ZWQiOnRydWUsImFnZSI6MSwiYmFuZWQiOmZhbHNlLCJjcmVhdGVfYXQiOjE3MTg3ODU5NzQsImV4cCI6MTcxODc4Nzc3NCwibW9kZSI6Miwib2FzaXNfaWQiOjgzNTQ3MTI3NTAyMDEyNDE2LCJ2ZXJzaW9uIjoyfQ.q_BebNbGp0DsYz_mdQy2XpwAMisQZ6hRjeKjObqFKVQ" + token

payload = "\u0000\u0000\u0000\u0000r{\"chatId\":\"114574443810230272\",\"messageInfo\":{\"text\":\"1+1\",\"author\":{\"role\":\"user\"}},\"messageMode\":\"SEND_MESSAGE\"}"
data = {"chatId": "114574443810230272", "messageInfo": {"text": "1+1", "author": {"role": "user"}},
           "messageMode": "SEND_MESSAGE"}
# payload = """\u0000\u0000\u0000\u0000r{"chatId":"114574443810230272","messageInfo":{"text":"1+1","author":{"role":"user"}},"messageMode":"SEND_MESSAGE"}"""
payload = f"""\u0000\u0000\u0000\u0000r{json.dumps(data)}""".replace(' ', '')
logger.debug(payload)

headers = {
    'connect-protocol-version': '1',
    'oasis-appid': '10200',
    'oasis-platform': 'web',
    'oasis-webid': 'd8c3fd203b05dd625da214711fffa75b36ae3023',
    'priority': 'u=1, i',
    'x-waf-client-type': 'fetch_sdk',
    # 'Cookie': f'Oasis-Token={token}',
    'content-type': 'application/connect+json',
    'oasis-token': token
}

response = requests.request("POST", url, headers=headers, data=payload)
response.encoding = 'utf8'
print(response.text)
