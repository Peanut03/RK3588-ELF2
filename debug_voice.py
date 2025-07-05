#!/usr/bin/env python3

import subprocess
import os
import time
import threading

os.environ['LD_LIBRARY_PATH'] = '/userdata/sherpa/sherpa-onnx-v1.11.5-linux-aarch64-shared-cpu/lib/:' + os.environ.get('LD_LIBRARY_PATH', '')

original_cwd = os.getcwd()
os.chdir('/userdata/sherpa/sherpa-onnx-v1.11.5-linux-aarch64-shared-cpu')

cmd = [
    'taskset', '0xc0',
    '/userdata/sherpa/sherpa-onnx-v1.11.5-linux-aarch64-shared-cpu/bin/sense-voice-simulate-streaming-alsa-cxx-api',
    'plughw:1,0'
]

try:
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    def monitor_stderr():
        while True:
            try:
                error_line = process.stderr.readline()
                if not error_line:
                    break
            except:
                break
    
    stderr_thread = threading.Thread(target=monitor_stderr, daemon=True)
    stderr_thread.start()
    
    while True:
        if process.poll() is not None:
            break
        
        try:
            output = process.stdout.readline()
            if not output:
                break
        except Exception as e:
            break
        
        time.sleep(0.1)

except Exception as e:
    pass
finally:
    try:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
    except:
        try:
            if process.poll() is None:
                process.kill()
        except:
            pass
    
    os.chdir(original_cwd) 