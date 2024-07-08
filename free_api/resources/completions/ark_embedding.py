#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : ark_embedding
# @Time         : 2024/5/16 09:25
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *


'''
Usage:
DEPRECATED: this is v2 sdk that will be discarded and using v3 instead
1. python3 -m pip install --user volcengine
2. python main.py
'''
import os
from volcengine.maas.v2 import MaasService
from volcengine.maas import MaasException


def test_embeddings(maas, endpoint_id, req):
    try:
        resp = maas.embeddings(endpoint_id, req)
        print(resp)
    except MaasException as e:
        print(e)


if __name__ == '__main__':
    maas = MaasService('maas-api.ml-platform-cn-beijing.volces.com', 'cn-beijing')

    # set ak&sk
    maas.set_ak(os.getenv("ARK_ACCESS_KEY"))
    maas.set_sk(os.getenv("ARK_SECRET_ACCESS_KEY"))

    # embeddings
    embeddingsReq = {
        "input": [
            "天很蓝",
            "海很深"
        ]
    }

    endpoint_id = 'ep-20240516005609-9c9pq'
    test_embeddings(maas, endpoint_id, embeddingsReq)
