# core/scanner.py
import os
import json
import platform
from pathlib import Path


class ProjectScanner:
    @staticmethod
    def get_default_jianying_path():
        """获取剪映默认的项目路径"""
        system = platform.system()
        if system == "Windows":
            local_app_data = os.getenv('LOCALAPPDATA')
            if local_app_data:
                return os.path.join(local_app_data, "JianyingPro", "User Data", "Projects", "com.lveditor.draft")
        elif system == "Darwin":
            home = str(Path.home())
            return os.path.join(home, "Movies", "JianyingPro", "User Data", "Projects", "com.liveditor.draft")
        return None

    @staticmethod
    def scan_projects(custom_path=None):
        """
        扫描所有本地项目，返回列表
        custom_path: 用户自定义的根路径
        """
        # 1. 决定扫描路径：优先使用自定义路径，否则使用默认路径
        if custom_path and os.path.exists(custom_path):
            root_path = custom_path
        else:
            root_path = ProjectScanner.get_default_jianying_path()

        if not root_path or not os.path.exists(root_path):
            return []

        projects = []
        # 2. 遍历文件夹
        for folder in os.listdir(root_path):
            folder_path = os.path.join(root_path, folder)
            draft_file = os.path.join(folder_path, "draft_content.json")

            if os.path.isdir(folder_path) and os.path.exists(draft_file):
                try:
                    # 简单处理：使用文件夹名称
                    projects.append({
                        "name": folder,
                        "path": draft_file,
                        "folder": folder_path
                    })
                except:
                    continue
        return projects