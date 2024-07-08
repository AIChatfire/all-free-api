from flask import Flask, request, jsonify, Response
import json
import requests
import time
import random
import string

app = Flask(__name__)

AUTHORIZATION_KEY = "Bearer sk-123"

def generate_id():
    return "chatcmpl-" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=24))

@app.route('/v1/chat/completions', methods=['POST'])
def handle_request():
    # scraper = cloudscraper.create_scraper()
    if request.method != 'POST':
        return Response("请求方法必须为POST", status=405)

    authorization_header = request.headers.get("Authorization")
    # print(authorization_header)
    if authorization_header != AUTHORIZATION_KEY:
        return Response("未授权的请求", status=401)

    request_body = request.get_json()
    print(type(request_body))
    messages = request_body.get('messages')
    is_stream = request_body.get('stream')
    # print(is_stream)
    model = request_body.get('model')
    print(request_body)
    content = messages[-1]['content']
    if is_stream:
        new_request_body = json.dumps({
        "inputs": {},
        "query": content,
        "response_mode": "streaming",
        "conversation_id": "",
        "user": "abc-1234",
        })
    else :
        new_request_body = json.dumps({
        "inputs": {},
        "query": content,
        "conversation_id": "",
        "user": "abc-1234"
        }) 
    print(new_request_body)
    target_api_url = "https://api.dify.ai/v1/chat-messages"
    headers = {
    "Content-Type": "application/json" ,
    "Authorization":"Bearer a"
    }
    response = requests.post(target_api_url, headers=headers, data=new_request_body)
    # print(response.text)
    if is_stream:
        def stream_response():
            content_buffer = ""
            for chunk in response.iter_lines():
                
                if chunk:
                    chunk = chunk.decode('utf-8')
                    if chunk.startswith("data:"):
                        try:
                            data = json.loads(chunk[5:])
                            print(data)
                            # 在此处根据目标API的响应格式解析数据
                            if response.status_code == 200:
                                formatted_data = {
                                    "id": generate_id(),
                                    "object": "chat.completion.chunk",
                                    "created": int(time.time()),
                                    "model": "dify",
                                    "choices": [{
                                        "index": 0,
                                        "delta": {
                                            # 在此处提取响应的内容
                                            "content": data.get("answer")
                                        },
                                        "finish_reason": None
                                    }]
                                }
                                if data.get("event")== "message_end":
                                    formatted_data = {
                                        "id": generate_id(),
                                        "object": "chat.completion.chunk",
                                        "created": int(time.time()),
                                        "model": model,
                                        "choices": [{
                                            "index": 0,
                                            "delta": {},
                                            "finish_reason": "stop"
                                        }]
                                    }
                                yield f"data: {json.dumps(formatted_data)}\n\n"
                        except json.JSONDecodeError as error:
                            print(f"解析JSON时出错: {error} 原始数据: {chunk}")
                    
            # yield "data: [DONE]\n\n"

        return Response(stream_response(), content_type='text/event-stream')

    else:
        response_data = response.json()
        print(f"response_data{response_data}")
        # print(f"typr:{type(response_data)}")
        print(response_data.get("status"))
        content_buffer = ""
        if response.status_code == 200:
            content_buffer = response_data.get('answer')

        formatted_data = {
            "id": generate_id(),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "dify",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content_buffer
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(json.dumps(new_request_body)),
                "completion_tokens": len(content_buffer),
                "total_tokens": len(json.dumps(new_request_body)) + len(content_buffer)
            }
        }
        return jsonify(formatted_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, use_reloader=True, use_debugger=True)
