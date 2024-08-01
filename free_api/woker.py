#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : woker
# @Time         : 2024/7/11 09:40
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import pandas as pd

from meutils.pipe import *


d = {
    "id": "aa6f8c69-a147-44ae-90a6-e01a08e83f52",
    "createdAt": "2024-07-25T04:16:07.261Z",
    "updatedAt": "2024-07-25T04:16:07.261Z",
    "userId": 16209160,
    "createdBy": 16209160,
    "taskId": "1d5ddbfd-2989-41db-a254-140cfde0b018",
    "parentAssetGroupId": "3ef8c7f1-d6e3-4f3a-a37a-6824fd612195",
    "filename": "Gen-3 Alpha 9188597594.mp4",
    "url": "https://dnznrvs05pmza.cloudfront.net/5c713f75-eceb-4ea4-87e6-93a0acb8dc4d.mp4?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiYTdlNzBmZGM1MTM2MjBhMCIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTcyMjAzODQwMH0.yUp4_Img9H-4MnNJ-RSRcpt78NhYVyizDnFcFQA-q50",
    "fileSize": "3356991",
    "isDirectory": False,
    "previewUrls": [
        "https://dnf8butk8bbsy.cloudfront.net/task_artifact_previews/3c8b796e-decb-422b-86b9-aa2619e95b75.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMTYyNTU2YWYyZGUzMGU5NyIsImJ1Y2tldCI6InJ1bndheS11cGxvYWRzLXByb2QiLCJzdGFnZSI6InByb2QiLCJleHAiOjE3MjIwMzg0MDB9.Me3tqZf85sVefH--WoqYAlJDhKL9rooS6mCt1L_iL0A",
        "https://dnf8butk8bbsy.cloudfront.net/task_artifact_previews/2e957007-11cc-4771-8762-569cc78e8e7b.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiYjcxZWY2NGU4YTMzNGI3YiIsImJ1Y2tldCI6InJ1bndheS11cGxvYWRzLXByb2QiLCJzdGFnZSI6InByb2QiLCJleHAiOjE3MjIwMzg0MDB9.mDrQFRleuQvwtkBBpfWkftZmQek3zFy8isYOfgVCB00",
        "https://dnf8butk8bbsy.cloudfront.net/task_artifact_previews/e2f0c554-1a7c-4357-b379-9cc1e2e0dac1.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMzk3ZjNhZjkzOGI1MzUyYSIsImJ1Y2tldCI6InJ1bndheS11cGxvYWRzLXByb2QiLCJzdGFnZSI6InByb2QiLCJleHAiOjE3MjIwMzg0MDB9.e6JQSXs4_VghB5aHHAZSjOOg4i-HW9_sYQYDmz1OL7M",
        "https://dnf8butk8bbsy.cloudfront.net/task_artifact_previews/94dbd7fe-3e00-4550-8395-f5f7d8081616.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiZmYwN2U1OTIzODg2MDZmNSIsImJ1Y2tldCI6InJ1bndheS11cGxvYWRzLXByb2QiLCJzdGFnZSI6InByb2QiLCJleHAiOjE3MjIwMzg0MDB9.hm1B-31m_EfS7oHkXh7j2nmyI8or0heaIO5ToyY6_xY",
        "https://dnf8butk8bbsy.cloudfront.net/task_artifact_previews/9bbc6772-1899-4f56-b9cb-5c5a5cf585ee.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNjhiZTlmZTU2OTcxN2Y0YiIsImJ1Y2tldCI6InJ1bndheS11cGxvYWRzLXByb2QiLCJzdGFnZSI6InByb2QiLCJleHAiOjE3MjIwMzg0MDB9.1-nCrAHbDpVtePoR6lR0BphuHoSsSu3vr0WwzBupkN0"
    ],
    "private": True,
    "privateInTeam": True,
    "deleted": False,
    "reported": False,
    "metadata": {
        "frameRate": 24,
        "duration": 5.334,
        "dimensions": [
            1280,
            768
        ],
        "size": {
            "width": 1280,
            "height": 768
        }
    },
    "favorite": False
}

f""""""
data = [
    {

    }
]
d = {
    "视频": f"![视频]({urls[0]})",
    "预览图": list(map(lambda url: f"![]({url})", urls[1]))

}

d = pd.DataFrame([d])
d.to_markdown()
