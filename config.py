#!/usr/bin/env python3
# -*- coding: utf-8 -*-

VISION_API_URL = "http://localhost:8080/v1/chat/completions"
IMAGE_PATH = '/userdata/rkllm_qwen2-vl_http_demo-main/deploy/install/demo_Linux_aarch64/demo.jpg'
AUDIO_OUTPUT_DIR = "/userdata/rkllm_qwen2-vl_http_demo-main/deploy/install/demo_Linux_aarch64/audio_outputs"
TTS_BIN = "/userdata/sherpa/sherpa-onnx-v1.11.5-linux-aarch64-shared-cpu/bin/sherpa-onnx-offline-tts"
TTS_MODEL_DIR = "/userdata/sherpa-onnx/matcha-icefall-zh-baker"
TTS_ACOUSTIC_MODEL = "/userdata/sherpa-onnx/matcha-icefall-zh-baker/model-steps-3.onnx"
TTS_VOCODER = "/userdata/sherpa-onnx/vocos-22khz-univ.onnx"
TTS_LEXICON = "/userdata/sherpa-onnx/matcha-icefall-zh-baker/lexicon.txt"
TTS_TOKENS = "/userdata/sherpa-onnx/matcha-icefall-zh-baker/tokens.txt"
TTS_DICT_DIR = "/userdata/sherpa-onnx/matcha-icefall-zh-baker/dict"

CAMERA_INDEX = 21

DEFAULT_PROMPT = """
你是一位顶级的AI健身教练，看看图片里的人在做什么动作，详细评估我的姿势。如果姿势标准，请夸奖我。如果姿势不标准，请具体指出2个最关键的错误点，并解释为什么这是错的。
针对不标准的点，清晰地告诉我应该如何改进。最后，请用一句话鼓励我。

重要要求：请使用纯文本格式进行回答，不要包含任何Markdown标记（例如 `*` 或 `#`），确保整个回答是一个完整的、未分段的段落。
"""
ANALYSIS_PROMPT = DEFAULT_PROMPT

ANALYSIS_INTERVAL = 120

AUDIO_FORMAT = "wav"

MAX_AUDIO_FILES = 20

QUICK_COMMANDS = {
    "这是什么": "用一句话描述图片里的主要物体",
    "有什么人": "详细描述图片里的人物，包括他们的穿着和动作",
    "有几个": "数一数图片里有多少个物体或人",
    "详细描述": "请用尽可能多的细节来描述这张图片",
}

LLM_OUTPUT_FILE = "llm_output.txt"
SUMMARY_OUTPUT_FILE = "final_summary.txt"
VOICE_SERVICE_BIN = './demo_stream' 