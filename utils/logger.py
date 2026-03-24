# utils/logger.py
import sys
from datetime import datetime

class TextHandler:
    """
    将日志输出重定向到 Tkinter Text 组件
    """
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        # 添加时间戳
        timestamp = datetime.now().strftime("[%H:%M:%S] ")
        self.text_widget.configure(state='normal')
        self.text_widget.insert('end', timestamp + str(message))
        self.text_widget.see('end')  # 自动滚动到底部
        self.text_widget.configure(state='disabled')

    def flush(self):
        pass