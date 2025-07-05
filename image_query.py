import base64
import json
import requests
from pathlib import Path

IMAGE_PATH = '/userdata/rkllm_qwen2-vl_http_demo-main/deploy/install/demo_Linux_aarch64/2.jpg'
API_URL = 'http://localhost:8080/v1/chat/completions'
QUESTION = "详细地描述一下图片里的内容"

def main():
    with open(IMAGE_PATH, 'rb') as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    request_data = {
        "model": "RK3588-Qwen2-VL-2B",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": QUESTION
                    }
                ]
            }
        ],
        "stream": True,
        "max_tokens": 1000
    }
    
    response = requests.post(
        API_URL,
        headers={'Content-Type': 'application/json'},
        json=request_data,
        stream=True
    )
    
    if response.status_code != 200:
        return
    
    full_response = ""
    for chunk in response.iter_lines():
        if chunk:
            line = chunk.decode('utf-8')
            if line.startswith('data: ') and not line.startswith('data: [DONE]'):
                try:
                    data = json.loads(line[6:])
                    if data.get('choices') and len(data['choices']) > 0:
                        delta = data['choices'][0].get('delta', {})
                        if 'content' in delta:
                            content = delta['content']
                            full_response += content
                except json.JSONDecodeError:
                    pass

if __name__ == "__main__":
    main() 
