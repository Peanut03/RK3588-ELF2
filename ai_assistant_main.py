#!/usr/bin/env python3

import os
import sys
import time
import json
import base64
import logging
import signal
import subprocess
import threading
import re
from datetime import datetime
from queue import Queue
import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPixmap, QFont, QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
                             QDesktopWidget, QSpacerItem, QSizePolicy)
import requests
# 安全地导入配置,如果失败则打印明确错误并退出
try:
    from config import *
except ImportError as e:
    print("=" * 60)
    print("!!! 致命错误: 无法导入配置文件 'config.py' !!!")
    print(f"错误详情: {e}")
    print("请确保 'config.py' 文件存在于同一目录下,并且没有语法错误。")
    print("=" * 60)
    sys.exit(1)
# 新增:定时分析的配置
# 建议将此变量移至 config.py 文件中进行统一管理
TIMED_ANALYSIS_INTERVAL = 120  # 定时分析的间隔时间(秒)
class AIFitnessApp(QMainWindow):
    """
    主应用窗口类,整合了 GUI 和 AI 后端逻辑。
    """
    # 定义一个信号,用于在非 GUI 线程完成分析后安全地更新 GUI
    analysis_complete_signal = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        # ------------------- AI 后端初始化 (功能未修改) -------------------
        self.image_path = IMAGE_PATH
        self.vision_api_url = VISION_API_URL
        self.analysis_prompt = ANALYSIS_PROMPT
        self.camera_index = CAMERA_INDEX
        self.llm_output_file = LLM_OUTPUT_FILE
        self.summary_output_file = SUMMARY_OUTPUT_FILE
        self.tts_bin = TTS_BIN
        self.audio_output_dir = AUDIO_OUTPUT_DIR
        self.output_audio_file = os.path.join(self.audio_output_dir, "audio.wav")
        self.voice_output_file = '/tmp/voice_recognition_output.txt'
        self.quick_commands = QUICK_COMMANDS
        self.running = True
        self.exit_requested = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.setup_logging()
        os.makedirs(self.audio_output_dir, exist_ok=True)
        self.analysis_complete_signal.connect(self.handle_analysis_result)
        # ------------------- GUI 初始化 (界面美化) -------------------
        self.setWindowTitle("◇ 智能健身助手")
        screen = QDesktopWidget().screenGeometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        self.setGeometry(0, 0, self.screen_width, self.screen_height) # 使用setGeometry以适应全屏
        # 设置全局字体
        font = QFont("Microsoft YaHei UI", 10)
        QApplication.setFont(font)
        self.camera = cv2.VideoCapture(self.camera_index)
        if not self.camera.isOpened():
            self.logger.critical(f"无法打开摄像头,索引: {self.camera_index}")
            sys.exit(1)
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        # 主布局: 水平布局
        main_layout = QHBoxLayout(self.main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        # --- 左侧布局 (摄像头和按钮) ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.camera_label, 1)
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0,0,0,0)
        button_layout.setSpacing(15)
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.analyze_now_button = QPushButton("◇ 语音分析")
        self.analyze_now_button.setObjectName("AnalyzeButton")
        self.analyze_now_button.clicked.connect(self.trigger_manual_analysis)
        button_layout.addWidget(self.analyze_now_button)
        self.stop_button = QPushButton("◇ 停止分析")
        self.stop_button.setObjectName("StopButton")
        self.stop_button.clicked.connect(self.stop_ai_services)
        button_layout.addWidget(self.stop_button)
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        left_layout.addWidget(button_container)
        # --- 右侧布局 (信息面板) ---
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)
        self.analysis_container = QWidget()
        self.analysis_container.setObjectName("InfoPanel")
        analysis_layout = QVBoxLayout(self.analysis_container)
        analysis_title = QLabel("◇ 实时 AI 分析")
        analysis_title.setObjectName("PanelTitle")
        analysis_layout.addWidget(analysis_title)

        # MODIFICATION: 将 QLabel 更换为 QTextEdit 以支持滚动条
        self.analysis_text = QTextEdit("正在启动首次自动分析...")
        self.analysis_text.setReadOnly(True)
        analysis_layout.addWidget(self.analysis_text, 1)

        self.summary_container = QWidget()
        self.summary_container.setObjectName("InfoPanel")
        summary_layout = QVBoxLayout(self.summary_container)
        summary_title = QLabel("◇ 训练历史及练后总结")
        summary_title.setObjectName("PanelTitle")
        summary_layout.addWidget(summary_title)
        self.summary_text = QTextEdit("训练结束后，最终生成的总结报告将显示在此处。")
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text, 1)
        right_layout.addWidget(self.analysis_container, 1)
        right_layout.addWidget(self.summary_container, 1)
        main_layout.addWidget(left_container, 3)
        main_layout.addWidget(right_container, 2)
        self.set_stylesheet()
        self.stopped = False
        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self.trigger_timed_analysis)
        # ------------------- 启动后台服务 (功能未修改) -------------------
        self.clear_log_files()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_tick)
        self.timer.start(33)
        self.logger.info("AI 健身助手 GUI 已启动")
        self.logger.info(f"首次定时分析将在启动后立即开始,后续间隔 {TIMED_ANALYSIS_INTERVAL} 秒。")
        QTimer.singleShot(1000, self.trigger_timed_analysis)
    def set_stylesheet(self):
        """设置应用的QSS样式表"""
        style = """
        QMainWindow, #main_widget {
            background-color: #1e2a40;
        }
        QLabel {
            color: #d0d0d0;
            font-size: 14px;
        }
        QWidget#InfoPanel {
            background-color: rgba(38, 50, 70, 0.7);
            border-radius: 12px;
            border: 1px solid rgba(0, 255, 255, 0.2);
        }
        QLabel#PanelTitle {
            color: #ffffff;
            font-size: 15px;
            font-weight: bold;
            padding: 5px 12px;
            border-bottom: 1px solid rgba(0, 255, 255, 0.2);
        }
        #analysis_container, #summary_container {
            padding: 8px;
        }
        QTextEdit {
            background-color: transparent;
            border: none;
            color: #d0d0d0;
            font-size: 13px;
            padding: 0px 8px;
        }
        #camera_label {
            background-color: #000000;
            border: 2px solid #00ffff;
            border-radius: 12px;
            box-shadow: 0 0 15px #00ffff;
        }
        QPushButton {
            color: white;
            font-size: 14px;
            font-weight: bold;
            border-radius: 12px;
            padding: 8px 18px;
            border: 1px solid transparent;
            min-height: 36px;
        }
        QPushButton#AnalyzeButton {
            background-color: #00aaff;
        }
        QPushButton#AnalyzeButton:hover {
            background-color: #00cfff;
            border: 1px solid #ffffff;
        }
        QPushButton#StopButton {
            background-color: #ff4757;
        }
        QPushButton#StopButton:hover {
            background-color: #ff6b81;
            border: 1px solid #ffffff;
        }
        QPushButton:disabled {
            background-color: #505050;
            color: #a0a0a0;
        }
        """
        self.setStyleSheet(style)
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[logging.FileHandler('ai_assistant_gui.log'), logging.StreamHandler()])
        self.logger = logging.getLogger(__name__)
    def clear_log_files(self):
        try:
            with open(self.llm_output_file, 'w', encoding='utf-8') as f:
                f.write(f"--- AI Assistant Log Initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n\n")
            self.logger.info(f"已清空并初始化日志文件: {self.llm_output_file}")
        except Exception as e:
            self.logger.error(f"清空日志文件失败: {e}")
        try:
            with open(self.summary_output_file, 'w', encoding='utf-8') as f:
                f.write(f"--- Final Summary will be generated upon exit ---\n")
            self.logger.info(f"已清空并初始化总结文件: {self.summary_output_file}")
        except Exception as e:
            self.logger.error(f"清空总结文件失败: {e}")
    def update_tick(self):
        if self.stopped:
            return
        ret, frame = self.camera.read()
        if ret:
            with self.frame_lock:
                self.current_frame = frame
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            self.camera_label.setPixmap(pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
    def trigger_manual_analysis(self):
        if self.stopped:
            self.logger.info("应用已停止,忽略手动分析请求。")
            self.analysis_text.setPlainText("应用已停止,无法分析。")
            return
        if self.analysis_timer.isActive():
            self.analysis_timer.stop()
            self.logger.info("定时分析已暂停,处理手动指令。")
        self.logger.info("--> '开始分析'按钮被点击, 读取最新语音指令... <--")
        self.analysis_text.setPlainText("正在读取语音指令...")
        voice_text = self.get_last_voice_command()
        if voice_text:
            self.logger.info(f"🎤 读取到最新语音命令: '{voice_text}'")
            processed_text = self.process_voice_command(voice_text)
            final_prompt = f"{processed_text}\n\n请务必用中文回答。"
            self.logger.info(f"构造送给模型的最终提示词: '{final_prompt}'")
            self.start_analysis_in_thread(final_prompt)
        else:
            self.logger.warning("语音输入文件为空或未找到,将使用默认提示词进行分析。")
            self.analysis_text.setPlainText("未检测到语音,使用默认分析。")
            self.start_analysis_in_thread(self.analysis_prompt)
    def trigger_timed_analysis(self):
        if self.stopped:
            self.analysis_timer.stop()
            return
        self.logger.info(f"定时器触发,使用默认提示进行分析: '{self.analysis_prompt}'")
        self.analysis_text.setPlainText("正在进行定时自动分析...")
        self.start_analysis_in_thread(self.analysis_prompt)
    def start_analysis_in_thread(self, prompt):
        with self.frame_lock:
            if self.current_frame is None:
                self.logger.warning("请求分析,但当前没有可用的摄像头帧。")
                return
            frame_to_analyze = self.current_frame.copy()
        self.analysis_text.setPlainText("分析中，请稍候...")
        thread = threading.Thread(target=self.analysis_worker, args=(frame_to_analyze, prompt))
        thread.daemon = True
        thread.start()
    def analysis_worker(self, frame, prompt):
        response = self.query_vision_model(frame, prompt)
        if response:
            self.analysis_complete_signal.emit(response)
        else:
            self.logger.error("AI 分析失败。")
            self.analysis_complete_signal.emit("AI 分析失败。")
    def handle_analysis_result(self, result_text):
        if result_text.startswith("FINAL_SUMMARY:"):
            summary = result_text.replace("FINAL_SUMMARY:", "", 1)
            self.logger.info("在 GUI 中显示最终总结。")
            self.analysis_text.setPlainText("训练总结已生成完毕！")
            self.summary_text.setPlainText(summary)
            return
        self.logger.info(f"AI 分析结果: {result_text}")
        self.analysis_text.setPlainText(f"{result_text}")
        self.save_llm_output(result_text)
        tts_thread = threading.Thread(target=self.text_to_speech, args=(result_text,))
        tts_thread.daemon = True
        tts_thread.start()
        if not self.stopped:
            self.logger.info(f"分析完成,将在 {TIMED_ANALYSIS_INTERVAL} 秒后进行下一次自动分析。")
            self.analysis_timer.start(TIMED_ANALYSIS_INTERVAL * 1000)
    def query_vision_model(self, frame, question):
        self.logger.info(f"正在查询视觉模型, 问题: {question}")
        cv2.imwrite(self.image_path, frame)
        try:
            with open(self.image_path, 'rb') as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            data = { "model": "RK3588-Qwen2-VL-2B", "messages": [ { "role": "user", "content": [ { "type": "image_url", "image_url": { "url": f"data:image/jpeg;base64,{base64_image}" } }, { "type": "text", "text": question } ] } ], "stream": True, "max_tokens": 1000 }
            response = requests.post(self.vision_api_url, headers={'Content-Type': 'application/json'}, json=data, stream=True, timeout=30)
            if response.status_code == 200:
                full_response = ""
                for chunk in response.iter_lines():
                    if chunk:
                        line = chunk.decode('utf-8')
                        if line.startswith('data: ') and not line.startswith('data: [DONE]'):
                            try:
                                json_data = json.loads(line[6:])
                                if json_data.get('choices') and len(json_data['choices']) > 0:
                                    delta = json_data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        full_response += content
                            except json.JSONDecodeError:
                                continue
                return re.sub(r'[a-zA-Z0-9 .\-#*]', '', full_response.strip()) if full_response else None
            else:
                self.logger.error(f"视觉模型请求失败: {response.status_code} - {response.text}")
                return f"视觉模型请求失败: {response.status_code}"
        except Exception as e:
            self.logger.error(f"查询视觉模型失败: {e}")
            return f"查询视觉模型时出错: {e}"
    def query_text_model(self, question):
        self.logger.info(f"正在查询文本模型, 问题: {question[:100]}...")
        try:
            data = { "model": "RK3588-Qwen2-VL-2B", "messages": [{"role": "user", "content": [{"type": "text", "text": question}]}], "stream": True, "max_tokens": 1500 }
            response = requests.post(self.vision_api_url, headers={'Content-Type': 'application/json'}, json=data, stream=True, timeout=120)
            if response.status_code == 200:
                full_response = ""
                for chunk in response.iter_lines():
                    if chunk:
                        line = chunk.decode('utf-8')
                        if line.startswith('data: ') and not line.startswith('data: [DONE]'):
                            try:
                                json_data = json.loads(line[6:])
                                if json_data.get('choices') and len(json_data['choices']) > 0:
                                    delta = json_data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        full_response += content
                            except json.JSONDecodeError:
                                continue
                return re.sub(r'[a-zA-Z0-9 .\-#*]', '', full_response.strip()) if full_response else None
            else:
                self.logger.error(f"文本模型请求失败: {response.status_code} - {response.text}")
                return f"文本模型请求失败: {response.status_code}"
        except Exception as e:
            self.logger.error(f"查询文本模型时出错: {e}")
            return f"查询文本模型时出错: {e}"
    def get_last_voice_command(self):
        try:
            if not os.path.exists(self.voice_output_file):
                self.logger.warning(f"语音输入文件 {self.voice_output_file} 不存在。")
                return None
            with open(self.voice_output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for line in reversed(lines):
                stripped_line = line.strip()
                if stripped_line:
                    return stripped_line
            self.logger.warning(f"语音输入文件 {self.voice_output_file} 为空。")
            return None
        except Exception as e:
            self.logger.error(f"读取语音文件时出错: {e}")
            return None
    def process_voice_command(self, voice_text):
        for command, prompt in self.quick_commands.items():
            if command in voice_text:
                self.logger.info(f"🔄 匹配到快捷命令: {command}")
                return prompt
        return voice_text
    def text_to_speech(self, text):
        self.logger.info("开始进行文字转语音...")
        try:
            cmd = [ TTS_BIN, f"--matcha-acoustic-model={TTS_ACOUSTIC_MODEL}", f"--matcha-vocoder={TTS_VOCODER}", f"--matcha-lexicon={TTS_LEXICON}", f"--matcha-tokens={TTS_TOKENS}", f"--matcha-dict-dir={TTS_DICT_DIR}", "--num-threads=2", f"--output-filename={self.output_audio_file}", text ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if result.returncode == 0 and os.path.exists(self.output_audio_file):
                self.logger.info(f"TTS成功,音频文件已保存到: {self.output_audio_file}")
                self.play_audio(self.output_audio_file)
            else:
                self.logger.error(f"TTS失败: {result.stderr}")
        except Exception as e:
            self.logger.error(f"TTS处理失败: {e}")
    def play_audio(self, audio_file):
        self.logger.info(f"正在使用 aplay 播放音频: {audio_file}")
        try:
            subprocess.run(['aplay', audio_file], check=True, capture_output=True, text=True, timeout=60)
            self.logger.info(f"音频播放完毕: {audio_file}")
        except Exception as e:
            self.logger.error(f"播放音频时发生错误: {e}")
    def save_llm_output(self, text):
        self.logger.info("正在保存大模型输出...")
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.llm_output_file, 'a', encoding='utf-8') as f:
                f.write(f"--- Response at {timestamp} ---\n{text}\n\n")
            self.logger.info(f"大模型输出已成功追加到: {self.llm_output_file}")
        except Exception as e:
            self.logger.error(f"保存大模型输出失败: {e}", exc_info=True)
    def stop_ai_services(self):
        self.logger.info("用户请求停止服务并生成总结。")
        self.running = False
        self.stopped = True
        if self.analysis_timer.isActive():
            self.analysis_timer.stop()
            self.logger.info("定时分析已停止。")
        if self.camera.isOpened():
            self.camera.release()
            self.logger.info("摄像头资源已释放。")
        self.camera_label.setText("训练已结束")
        self.camera_label.setStyleSheet(self.camera_label.styleSheet() + "color: white; font-size: 24px;")
        self.analysis_text.setPlainText("正在生成最终总结...")
        self.analyze_now_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        summary_thread = threading.Thread(target=self.perform_final_summary)
        summary_thread.daemon = True
        summary_thread.start()
    def perform_final_summary(self):
        self.logger.info("正在准备生成最终总结...")
        try:
            with open(self.llm_output_file, 'r', encoding='utf-8') as f:
                history = f.read()
            if len(history.splitlines()) < 3:
                self.logger.warning("训练记录太少,无法生成总结。")
                final_summary = "没有足够的训练数据来生成总结。"
            else:
                summary_prompt = f"这是本次健身的全部AI分析记录,请根据这些记录,生成一份完整的最终总结报告。报告应包括:1. 本次训练整体表现的总结。2. 动作的亮点和主要优点。3. 最需要改进的几个问题点。4. 针对问题点的具体、可执行的改进建议。请以易于阅读的格式呈现,回答请使用中文。记录如下:\n\n{history}"
                final_summary = self.query_text_model(summary_prompt)
            if final_summary:
                self.logger.info("成功生成最终总结。")
                self.save_final_summary(final_summary)
                self.analysis_complete_signal.emit(f"FINAL_SUMMARY:{final_summary}")
            else:
                self.logger.error("未能生成最终总结。")
                self.analysis_complete_signal.emit("FINAL_SUMMARY:生成总结失败,请检查网络或模型服务。")
        except FileNotFoundError:
            self.logger.error(f"无法找到日志文件 {self.llm_output_file} 来生成总结。")
            self.analysis_complete_signal.emit("FINAL_SUMMARY:找不到训练记录文件,无法生成总结。")
        except Exception as e:
            self.logger.error(f"生成总结过程中出现意外错误: {e}", exc_info=True)
            self.analysis_complete_signal.emit(f"FINAL_SUMMARY:生成总结时出错: {e}")
    def save_final_summary(self, text):
        self.logger.info("正在保存最终总结...")
        try:
            with open(self.summary_output_file, 'w', encoding='utf-8') as f:
                f.write("--- AI Fitness Coach Final Summary ---\n")
                f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(text)
            self.logger.info(f"最终总结已成功保存到: {self.summary_output_file}")
        except Exception as e:
            self.logger.error(f"保存最终总结失败: {e}", exc_info=True)
    def closeEvent(self, event):
        self.logger.info("收到关闭窗口请求,开始清理资源...")
        self.running = False
        self.exit_requested = True
        if self.camera.isOpened():
            self.camera.release()
            self.logger.info("摄像头资源已释放。")
        self.logger.info("应用已关闭。")
        event.accept()
def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    window = AIFitnessApp()
    window.showMaximized()
    sys.exit(app.exec_())
if __name__ == "__main__":
    main()