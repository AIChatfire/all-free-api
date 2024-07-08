#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : ark
# @Time         : 2024/5/15 15:26
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://www.volcengine.com/product/doubao?utm_source=5&utm_medium=sembaidu&utm_term=sem_baidu_damoxing_doubao_1&utm_campaign=vgbdpcztn797661721486&utm_content=damoxing_doubao
import os

from meutils.pipe import *
import volcenginesdkcore
import volcenginesdkark
from pprint import pprint
from volcenginesdkcore.rest import ApiException

endpoint_map ={
            "doubao-lite-128k": "ep-20240520010805-566f7",
            "doubao-lite-32k": "ep-20240515062431-rkhfp",
            "doubao-lite-4k": "ep-20240515062545-nnq8b",

            "doubao-pro-128k": "ep-20240515073409-dlpqp",
            "doubao-pro-32k": "ep-20240515073434-s4skk",
            "doubao-pro-4k": "ep-20240515073524-xj4m2",  # fc

            "moonshot-v1-8k": "ep-20240516010405-mwthf",
            "moonshot-v1-32k": "ep-20240516010345-f88rs",
            "moonshot-v1-128k": "ep-20240516010323-zfzwj",

            "doubao-embedding": "ep-20240516005609-9c9pq",
        }

if __name__ == '__main__':
    configuration = volcenginesdkcore.Configuration()
    configuration.ak = os.getenv("ARK_ACCESS_KEY")
    configuration.sk = os.getenv("ARK_SECRET_ACCESS_KEY")
    configuration.region = "cn-beijing"
    # set default configuration
    volcenginesdkcore.Configuration.set_default(configuration)

    # use global default configuration
    api_instance = volcenginesdkark.ARKApi()

    # for endpoint in endpoint_map.values():
    get_api_key_request = volcenginesdkark.GetApiKeyRequest(
        duration_seconds=30 * 24 * 3600,
        resource_type="endpoint",
        resource_ids=list(endpoint_map.values()),
        # resource_ids=["ep-20240515062545-nnq8b"]
    )




    try:
        resp = api_instance.get_api_key(get_api_key_request)
        pprint(resp)
    except ApiException as e:
        print("Exception when calling api: %s\n" % e)



    '''
    Usage:

    1. python3 -m pip install --user volcengine
    2. python main.py
    '''
    import os
    from volcengine.maas.v2 import MaasService
    from volcengine.maas import MaasException, ChatRole


    def test_chat(maas, endpoint_id, req):
        try:
            resp = maas.chat(endpoint_id, req)
            print(resp)
        except MaasException as e:
            print(e)


    def test_stream_chat(maas, endpoint_id, req):
        try:
            resps = maas.stream_chat(endpoint_id, req)
            for resp in resps:
                print(resp)
        except MaasException as e:
            print(e)


        maas = MaasService('maas-api.ml-platform-cn-beijing.volces.com', 'cn-beijing')

        # set ak&sk
        maas.set_ak("VOLC_ACCESSKEY")
        maas.set_sk("VOLC_SECRETKEY")
        # r := client.NewInstance("maas-api.ml-platform-cn-beijing.volces.com", "cn-beijing")

        # chat
        req = {
            "parameters": {
                "max_new_tokens": 1024,  # 输出文本的最大tokens限制，max_new_tokens + input_length <= max_input_size
                "temperature": 0.3,  # 用于控制生成文本的随机性和创造性，Temperature值越大随机性越大，取值范围0~1
                "top_p": 0.9,  # 用于控制输出tokens的多样性，TopP值越大输出的tokens类型越丰富，取值范围0~1
            },
            "messages": [
                {
                    "role": ChatRole.USER,
                    "content": "天为什么这么蓝？"
                }, {
                    "role": ChatRole.ASSISTANT,
                    "content": "因为有你"
                }, {
                    "role": ChatRole.USER,
                    "content": "花儿为什么这么香？"
                },
            ]
        }

        endpoint_id = 'ep-20240516010405-mwthf'
        test_chat(maas, endpoint_id, req)
        test_stream_chat(maas, endpoint_id, req)
