# utils/video_info.py
from moviepy.editor import VideoFileClip
import os


def get_video_metadata(video_path):
    """
    获取视频的元数据：时长、宽度、高度
    """
    if not os.path.exists(video_path):
        return None

    try:
        clip = VideoFileClip(video_path)
        metadata = {
            "duration": clip.duration,  # 秒
            "width": clip.w,
            "height": clip.h,
            "fps": clip.fps
        }
        clip.close()
        return metadata
    except Exception as e:
        print(f"读取视频信息失败: {e}")
        return None