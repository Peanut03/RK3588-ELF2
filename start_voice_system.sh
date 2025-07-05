#!/bin/bash

if [ ! -f "./voice_service.py" ]; then
    echo "错误: voice_service.py 不存在"
    exit 1
fi

if [ ! -f "./ai_assistant_main.py" ]; then
    echo "错误: ai_assistant_main.py 不存在"
    exit 1
fi

rm -f ./voice_recognition_output.txt
rm -f ./voice_service_status.txt
rm -f ./voice_command.txt
rm -f ./*.log
rm -rf ./__pycache__

function check_vision_service() {
    status_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/v1/chat/completions)
    if [ "$status_code" -ne "000" ]; then
        return 0 
    else
        return 1 
    fi
}

if check_vision_service; then
    :
else
    if [ ! -f "./demo_stream" ]; then
        echo "可执行文件不存在于当前目录！"
        exit 1
    fi

    export LD_LIBRARY_PATH=./lib
    nohup ./demo_stream models/qwen2_vl_2b_vision_rk3588.rknn models/Qwen2-VL-2B-Instruct.rkllm 8080 > vision_service.log 2>&1 &
    VISION_PID=$!
    
    WAIT_SECONDS=30
    ELAPSED=0
    while ! check_vision_service; do
        if [ $ELAPSED -ge $WAIT_SECONDS ]; then
            echo "大模型服务在 $WAIT_SECONDS 秒内未能启动。"
            cat ./vision_service.log
            kill $VISION_PID 2>/dev/null
            exit 1
        fi
        sleep 2
        ELAPSED=$((ELAPSED + 2))
    done
fi

nohup python3 voice_service.py > voice_service.log 2>&1 &
VOICE_PID=$!

sleep 3

python3 ai_assistant_main.py

if [ -n "$VOICE_PID" ]; then
    kill $VOICE_PID 2>/dev/null
fi
if [ -n "$VISION_PID" ]; then
    kill $VISION_PID 2>/dev/null
fi
