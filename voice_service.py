#!/usr/bin/env python3

import os
import subprocess
import sys
import threading
from datetime import datetime

SHERPA_DIR = '/userdata/sherpa/sherpa-onnx-v1.11.5-linux-aarch64-shared-cpu'
ASR_EXECUTABLE = os.path.join(SHERPA_DIR, 'bin/sense-voice-simulate-streaming-alsa-cxx-api')
AUDIO_DEVICE = 'plughw:1,0'
OUTPUT_FILE = '/tmp/voice_recognition_output.txt'

def parse_and_write_output(line, output_file):
    line = line.strip()

    if ". " in line and line.startswith('['):
        try:
            recognized_text = line.split('. ', 1)[1].strip()
            if recognized_text:
                try:
                    with open(output_file, 'a') as f:
                        f.write(f"{recognized_text}\n")
                        f.flush()
                except IOError as e:
                    pass
        except IndexError:
            pass

def main():
    try:
        os.chdir(SHERPA_DIR)
    except OSError as e:
        sys.exit(1)
        
    env = os.environ.copy()
    lib_path = os.path.join(SHERPA_DIR, 'lib')
    env['LD_LIBRARY_PATH'] = f"{lib_path}:{env.get('LD_LIBRARY_PATH', '')}" if env.get('LD_LIBRARY_PATH') else lib_path
    
    command = ['/usr/bin/stdbuf', '-oL', '/usr/bin/taskset', '0xc0', ASR_EXECUTABLE, AUDIO_DEVICE]

    try:
        with open(OUTPUT_FILE, 'w') as f:
            f.write("")
    except IOError as e:
        sys.exit(1)

    try:
        process = subprocess.Popen(
                command,
            env=env,
                stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, 
                text=True,
            bufsize=1 
            )

        for line in iter(process.stdout.readline, ''):
            parse_and_write_output(line, OUTPUT_FILE)

        process.wait()

    except FileNotFoundError:
        sys.exit(1)
    except Exception as e:
        sys.exit(1)

if __name__ == "__main__":
    main() 