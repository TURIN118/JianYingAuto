# core/draft_parser.py
import json
import os


class DraftParser:
    def __init__(self, draft_path):
        self.draft_path = draft_path
        self.data = None
        self.load()

    def load(self):
        if not os.path.exists(self.draft_path):
            raise FileNotFoundError(f"草稿文件不存在: {self.draft_path}")

        # 剪映草稿通常是UTF-8编码，有时带BOM
        with open(self.draft_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def save(self):
        with open(self.draft_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def get_tracks(self):
        """获取所有轨道"""
        return self.data.get('tracks', [])

    def get_video_tracks(self):
        """筛选出视频轨道"""
        tracks = self.get_tracks()
        video_tracks = []
        for index, track in enumerate(tracks):
            # 剪映轨道类型：video, audio, text等
            if track.get('type') == 'video':
                video_tracks.append({
                    "index": index,
                    "track_data": track
                })
        return video_tracks