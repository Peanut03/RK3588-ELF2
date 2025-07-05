#!/bin/bash

# AI助手系统诊断脚本

DEMO_DIR="/userdata/rkllm_qwen2-vl_http_demo-main/deploy/install/demo_Linux_aarch64"
SHERPA_DIR="/userdata/sherpa/sherpa-onnx-v1.11.5-linux-aarch64-shared-cpu"
SHERPA_ONNX_DIR="/userdata/sherpa-onnx"

cd "$DEMO_DIR"

files_to_check=(
    "$DEMO_DIR/demo_stream:大模型可执行文件"
    "$DEMO_DIR/models/qwen2_vl_2b_vision_rk3588.rknn:视觉模型文件"
    "$DEMO_DIR/models/Qwen2-VL-2B-Instruct.rkllm:语言模型文件"
    "$DEMO_DIR/2.jpg:测试图片文件"
    "$SHERPA_DIR/bin/sense-voice-simulate-streaming-alsa-cxx-api:语音识别程序"
    "$SHERPA_ONNX_DIR/build/bin/sherpa-onnx-offline-tts:TTS程序"
    "$SHERPA_ONNX_DIR/matcha-icefall-zh-baker/model-steps-3.onnx:TTS声学模型"
    "$SHERPA_ONNX_DIR/vocos-22khz-univ.onnx:TTS声码器"
)

for item in "${files_to_check[@]}"; do
    file_path="${item%%:*}"
    description="${item##*:}"
    if [ -f "$file_path" ]; then
        size=$(du -h "$file_path" | cut -f1)
    else
        :
    fi
done

if pgrep -f "demo_stream" > /dev/null; then
    pid=$(pgrep -f "demo_stream")
    ps aux | grep demo_stream | grep -v grep > /dev/null
else
    :
fi

if pgrep -f "integrated_ai_assistant.py" > /dev/null; then
    pid=$(pgrep -f "integrated_ai_assistant.py")
else
    :
fi

if nc -z localhost 8080 2>/dev/null; then
    :
else
    :
fi

port_info=$(netstat -tlnp 2>/dev/null | grep :8080 || ss -tlnp 2>/dev/null | grep :8080)
if [ -n "$port_info" ]; then
    :
fi

if nc -z localhost 8080 2>/dev/null; then
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d '{"model":"RK3588-Qwen2-VL-2B","messages":[{"role":"user","content":"hello"}],"stream":true,"max_tokens":5}' \
        http://localhost:8080/v1/chat/completions 2>/dev/null)
    
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        :
    else
        :
    fi
else
    :
fi

if command -v arecord >/dev/null 2>&1; then
    arecord -l 2>/dev/null || echo "未找到音频录制设备" > /dev/null
else
    :
fi

if command -v aplay >/dev/null 2>&1; then
    aplay -l 2>/dev/null || echo "未找到音频播放设备" > /dev/null
else
    :
fi

free -h > /dev/null
top -b -n1 | head -5 > /dev/null
df -h /userdata 2>/dev/null || df -h / > /dev/null

log_files=(
    "$DEMO_DIR/model_service.log:大模型服务日志"
    "$DEMO_DIR/ai_assistant.log:AI助手日志"
)

for item in "${log_files[@]}"; do
    log_path="${item%%:*}"
    description="${item##*:}"
    if [ -f "$log_path" ]; then
        size=$(du -h "$log_path" | cut -f1)
        lines=$(wc -l < "$log_path")
        tail -5 "$log_path" | sed 's/^/  /' > /dev/null
    else
        :
    fi
done

:
:
:
ls -la "$DEMO_DIR" | head -5 > /dev/null

echo "=========================================="
echo "        诊断完成"
echo "=========================================="

# 提供建议
echo
echo "常见问题解决方案:"
echo "1. 如果大模型服务无法启动，检查模型文件是否完整"
echo "2. 如果API无响应，等待更长时间或检查model_service.log"
echo "3. 如果语音功能不工作，检查音频设备配置"
echo "4. 如果内存不足，尝试重启系统或调整参数"
echo "5. 如果权限问题，确保文件具有执行权限" 