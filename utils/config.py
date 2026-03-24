# utils/config.py
import json
import os

CONFIG_FILE = "config.json"

def load_config():
    """读取配置文件"""
    if not os.path.exists(CONFIG_FILE):
        # 默认配置
        return {
            "custom_path": None,
            "jianying_exe": None
        }
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            "custom_path": None,
            "jianying_exe": None
        }

def save_config(data):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"配置保存失败: {e}")