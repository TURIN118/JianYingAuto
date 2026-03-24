# utils/preview.py
import cv2
import os  # 修复：导入 os 模块
import numpy as np
from PIL import Image, ImageTk


def get_video_thumbnail(video_path, width=200):
    """
    提取视频第一帧作为缩略图
    """
    if not video_path or not os.path.exists(video_path):
        return None

    try:
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)

        w, h = img.size
        ratio = width / w
        height = int(h * ratio)

        img = img.resize((width, height), Image.Resampling.LANCZOS)

        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"预览生成失败: {e}")
        return None