# core/replacer.py
import uuid
import copy
import os
from utils.video_info import get_video_metadata


class MaterialReplacer:
    def __init__(self, draft_parser):
        self.parser = draft_parser

    def _find_material_by_id(self, material_id):
        """
        在 materials 字典中查找对应的素材对象
        兼容新版剪映结构: materials = {'videos': [...], 'audios': [...]}
        """
        materials_root = self.parser.data.get('materials', {})

        # 情况1：materials 是字典 (新版常见)
        if isinstance(materials_root, dict):
            # 遍历所有分类（videos, audios, images 等）
            for category in materials_root.values():
                if isinstance(category, list):
                    for item in category:
                        if item.get('id') == material_id:
                            return item
        # 情况2：materials 是列表 (旧版或特殊情况)
        elif isinstance(materials_root, list):
            for item in materials_root:
                if item.get('id') == material_id:
                    return item

        return None

    def _get_target_material_list(self):
        """
        获取应该存放视频素材的列表对象
        返回列表对象本身，以便直接 append
        """
        materials_root = self.parser.data.get('materials')

        # 如果 materials 不存在，创建它
        if materials_root is None:
            self.parser.data['materials'] = {}
            materials_root = self.parser.data['materials']

        # 如果是字典结构，返回 'videos' 列表
        if isinstance(materials_root, dict):
            if 'videos' not in materials_root:
                materials_root['videos'] = []
            return materials_root['videos']

        # 如果是列表结构，直接返回
        if isinstance(materials_root, list):
            return materials_root

        return []

    def replace_material_in_track(self, track_index, new_video_paths, mode='loop'):
        """
        替换指定轨道的素材
        """
        tracks = self.parser.data['tracks']
        target_track = tracks[track_index]

        segments = target_track.get('segments', [])
        if not segments:
            print("该轨道没有片段")
            return

        print(f"正在处理轨道 {track_index}，共 {len(segments)} 个片段")

        for i, segment in enumerate(segments):
            # 选择新视频
            video_index = i % len(new_video_paths)
            new_video_path = new_video_paths[video_index]

            # 获取新视频信息
            meta = get_video_metadata(new_video_path)
            if not meta:
                print(f"跳过无效视频: {new_video_path}")
                continue

            # 生成新的素材ID
            new_material_id = str(uuid.uuid4()).replace('-', '')

            # 1. 获取旧素材的信息 (关键修改：用于复制配置)
            old_material_id = segment.get('material_id')
            old_material = self._find_material_by_id(old_material_id)

            # 2. 创建新素材数据
            if old_material:
                # 深拷贝旧素材配置，保留特效、音量等设置
                new_material = copy.deepcopy(old_material)
            else:
                # 如果找不到旧素材，创建一个基础模板
                new_material = {
                    "type": "video",
                    "roughcut_time_range": None  # 简单处理
                }

            # 更新核心字段
            new_material['id'] = new_material_id
            new_material['path'] = new_video_path
            new_material['duration'] = meta['duration'] * 1000000  # 秒转微秒

            # 处理宽高
            if 'width' not in new_material: new_material['width'] = meta['width']
            if 'height' not in new_material: new_material['height'] = meta['height']

            # 3. 更新片段的 material_id 和时间范围
            segment['material_id'] = new_material_id

            # 更新 source_timerange (素材源时间)
            # 逻辑：让新视频适应原片段的长度，或者使用新视频长度
            # 这里演示：保持原片段在时间轴上的位置不变
            target_duration = segment['target_timerange']['duration']

            segment['source_timerange'] = {
                "start": 0,
                "duration": min(meta['duration'] * 1000000, target_duration)
            }

            # 4. 将新素材添加到 materials 列表 (修复报错的关键位置)
            target_list = self._get_target_material_list()
            target_list.append(new_material)

            print(f"片段 {i} 已替换为: {os.path.basename(new_video_path)}")

        self.parser.save()
        print("保存草稿成功！")