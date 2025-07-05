#!/bin/bash

DEMO_DIR="/userdata/rkllm_qwen2-vl_http_demo-main/deploy/install/demo_Linux_aarch64"
SHERPA_DIR="/userdata/sherpa/sherpa-onnx-v1.11.5-linux-aarch64-shared-cpu"
SHERPA_ONNX_DIR="/userdata/sherpa-onnx"

if [ ! -f "$DEMO_DIR/demo_stream" ]; then
    echo "大模型可执行文件不存在: $DEMO_DIR/demo_stream"
    exit 1
fi

if [ ! -f "$DEMO_DIR/models/qwen2_vl_2b_vision_rk3588.rknn" ]; then
    echo "视觉模型文件不存在"
    exit 1
fi

if [ ! -f "$DEMO_DIR/models/Qwen2-VL-2B-Instruct.rkllm" ]; then
    echo "语言模型文件不存在"
    exit 1
fi

if [ ! -f "$DEMO_DIR/2.jpg" ]; then
    echo "测试图片文件不存在: $DEMO_DIR/2.jpg"
    exit 1
fi

if [ ! -f "$SHERPA_DIR/bin/sense-voice-simulate-streaming-alsa-cxx-api" ]; then
    echo "语音识别程序不存在"
    exit 1
fi

if [ ! -f "$SHERPA_ONNX_DIR/build/bin/sherpa-onnx-offline-tts" ]; then
    echo "错误: TTS程序不存在，需要先编译sherpa-onnx"
    echo "请在sherpa-onnx目录下运行: mkdir build && cd build && cmake .. && make -j4"
    exit 1
fi

export LD_LIBRARY_PATH="$DEMO_DIR/lib:$SHERPA_DIR/lib:$LD_LIBRARY_PATH"

check_model_service() {
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if ! pgrep -f "demo_stream" > /dev/null; then
            return 1
        fi
        
        if ! nc -z localhost 8080 2>/dev/null; then
            sleep 2
            ((attempt++))
            continue
        fi
        
        response=$(curl -s -w "%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d '{"model":"RK3588-Qwen2-VL-2B","messages":[{"role":"user","content":"test"}],"stream":true,"max_tokens":10}' \
            http://localhost:8080/v1/chat/completions \
            -o /tmp/api_test_response.json 2>/dev/null)
        
        http_code="${response: -3}"
        
        if [ "$http_code" = "200" ]; then
            return 0
        fi
        
        sleep 2
        ((attempt++))
    done
    
    return 1
}

if pgrep -f "demo_stream" > /dev/null; then
    if ! check_model_service; then
        pkill -f "demo_stream"
        sleep 3
    fi
fi

if ! pgrep -f "demo_stream" > /dev/null; then
    cd "$DEMO_DIR"
    
    rm -f model_service.log
    
    nohup ./demo_stream models/qwen2_vl_2b_vision_rk3588.rknn models/Qwen2-VL-2B-Instruct.rkllm 8080 > model_service.log 2>&1 &
    DEMO_PID=$!
    
    if ! check_model_service; then
        exit 1
    fi
fi

cd "$DEMO_DIR"
python3 integrated_ai_assistant.py

cleanup() {
    if [ ! -z "$DEMO_PID" ]; then
        kill $DEMO_PID 2>/dev/null
    fi
    pkill -f "demo_stream" 2>/dev/null
    pkill -f "integrated_ai_assistant.py" 2>/dev/null
}

trap cleanup EXIT INT TERM

wait 