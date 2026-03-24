# core/generator.py
import os
import shutil
import json
import time


def generate_draft_copies(template_draft_path, video_list, track_index, log_func=print):
    """
    根据模板草稿和素材列表，批量生成新的草稿副本

    Args:
        template_draft_path: 模板草稿的 draft_content.json 路径
        video_list: 新素材路径列表
        track_index: 要替换的轨道索引
        log_func: 日志输出函数

    Returns:
        success_count: 成功生成的数量
    """
    # 1. 获取模板文件夹路径
    template_folder = os.path.dirname(template_draft_path)
    parent_folder = os.path.dirname(template_folder)  # 草稿根目录

    success_count = 0

    for index, video_path in enumerate(video_list):
        try:
            # 2. 构建新草稿名称
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            timestamp = time.strftime("%H%M%S")
            # 新文件夹名：素材名_时间戳 (避免重名冲突)
            new_folder_name = f"{video_name}_{timestamp}"
            new_folder_path = os.path.join(parent_folder, new_folder_name)

            log_func(f"[{index + 1}/{len(video_list)}] 正在生成: {new_folder_name} ...")

            # 3. 复制整个模板文件夹
            shutil.copytree(template_folder, new_folder_path)

            # 4. 修改新草稿的内容
            new_draft_path = os.path.join(new_folder_path, "draft_content.json")

            # 使用现有的解析和替换逻辑
            # 为了避免循环依赖，这里直接导入
            from core.draft_parser import DraftParser
            from core.replacer import MaterialReplacer

            parser = DraftParser(new_draft_path)
            replacer = MaterialReplacer(parser)

            # 执行替换（只替换当前这一个视频）
            replacer.replace_material_in_track(track_index, [video_path])

            # 5. 修改 draft_meta_info.json (如果存在)
            # 剪映的项目显示名称通常存在这里
            meta_path = os.path.join(new_folder_path, "draft_meta_info.json")
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)

                # 修改项目名称
                meta_data['draft_name'] = new_folder_name
                # 重置修改时间等（可选）
                meta_data['draft_modified_at'] = int(time.time() * 1000000)

                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(meta_data, f, indent=4)

            success_count += 1

        except Exception as e:
            log_func(f"❌ 生成失败 {video_name}: {e}")

    return success_count