#!/bin/bash

SHERPA_DIR="/userdata/sherpa/sherpa-onnx-v1.11.5-linux-aarch64-shared-cpu"
cd "$SHERPA_DIR" || { echo "错误: 无法进入目录 $SHERPA_DIR"; exit 1; }

if [ ! -f "./silero_vad.onnx" ]; then
    echo "错误: VAD模型 'silero_vad.onnx' 不存在" >&2
    exit 1
fi
if [ ! -d "./sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17" ]; then
    echo "错误: ASR模型目录不存在" >&2
    exit 1
fi

export LD_LIBRARY_PATH="$SHERPA_DIR/lib:$LD_LIBRARY_PATH"

ASR_BIN="./bin/sense-voice-simulate-streaming-alsa-cxx-api"
AUDIO_DEVICE="plughw:1,0"

taskset 0xc0 stdbuf -o0 "$ASR_BIN" "$AUDIO_DEVICE" 