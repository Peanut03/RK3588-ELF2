#!/usr/bin/env python3

import time
import os

def write_voice_command(text):
    """写入语音命令到文件"""
    command_file = '/tmp/voice_command.txt'
    
    with open(command_file, 'w') as f:
        f.write(f"{text}\n")
        f.flush()
    
    print(f"已写入语音命令: {text}")
    print(f"文件位置: {command_file}")

def main():
    default_command = "测试"
    write_voice_command(default_command)

if __name__ == "__main__":
    main() 