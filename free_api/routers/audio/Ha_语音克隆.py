import requests
import json

def clone_voice_to_file(voice_file_path, texts, title, token, jsonl_file_path):
    url = "https://api.chatfire.cn/fish/model"
    
    # 设置请求头
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 打开语音文件
    with open(voice_file_path, 'rb') as voice_file:
        files = [
            ('voices', ('', voice_file, 'application/octet-stream'))
        ]
        
        # 发送 POST 请求
        response = requests.post(url, headers=headers, files=files, data={'texts': texts, 'title': title})
        
        # 检查响应是否成功
        if response.status_code == 200:
            result = response.json()
            
            
            # 追加写入到指定的 JSONL 文件
            with open(jsonl_file_path, 'a') as jsonl_file:
                jsonl_file.write(json.dumps(result) + '\n')
            
            print("数据已成功追加到文件中")
            return result
        else:
            print(f"请求失败，状态码：{response.status_code}")
            return None

# 示例调用
token = "sk-gpoH1z3G6nHovD8MY40i6xx5tsC1vbh7B3Aao2jmejYNoKhv"  # Bearer token
voice_file_path = r"E:\Pet_AI_Empower\voive\mp3\cjy15.mp3"     # 语音文件路径
texts = "分组1、2、3、4"                
title = "chatfire-tts-model"                    # 模型标题
jsonl_file_path = "fish_克隆.jsonl"                # 输出文件路径

# 调用函数
clone_voice_to_file(voice_file_path, texts, title, token, jsonl_file_path)
