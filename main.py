# main.py
import tkinter as tk
from tkinter import ttk
import sys
import os

from gui.panels import setup_left_panel, setup_right_panel
from gui.handlers import ProjectHandlers, MaterialHandlers, TaskHandlers, VideoProcessHandlers
from utils.config import load_config, save_config
from utils.logger import TextHandler


class App(ProjectHandlers, MaterialHandlers, TaskHandlers, VideoProcessHandlers, object):
    def __init__(self, root):
        self.root = root
        self.root.title("剪映批量助手 Pro v6.0 (深度去重版)")
        self.root.geometry("1050x780")

        style = ttk.Style()
        style.theme_use('clam')

        # 初始化变量
        self.projects_data = []
        self.current_draft_path = None
        self.new_videos = []
        self.current_scan_path = tk.StringVar()
        self.jianying_exe_path = tk.StringVar()
        self.exporter_instance = None

        self.process_input_path = tk.StringVar()
        self.process_output_path = tk.StringVar()
        self.trim_seconds = tk.StringVar(value="2")
        self.frame_interval = tk.StringVar(value="1")
        self.speed_var = tk.StringVar(value="1.0")
        self.resolution_var = tk.StringVar(value="origin")
        self.bgm_path = tk.StringVar()

        # 新增：去重布尔变量
        self.dedup_adjust = tk.BooleanVar(value=True)
        self.dedup_noise = tk.BooleanVar(value=False)
        self.dedup_crop = tk.BooleanVar(value=True)

        self._setup_menus()

        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, width=350)
        setup_left_panel(left_frame, self)

        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame)
        setup_right_panel(right_frame, self)

        self._init_path_config()
        self.redirect_logs()

    def _setup_menus(self):
        menubar = tk.Menu(self.root)
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="设置剪映主程序路径...", command=self._set_jianying_exe)
        self.root.config(menu=menubar)

    def _init_path_config(self):
        config = load_config()
        saved_path = config.get("custom_path")
        if saved_path and os.path.exists(saved_path):
            self.current_scan_path.set(saved_path)
        else:
            default_path = r"D:\DATA\JianYing\draft\JianyingPro Drafts"
            if not os.path.exists(default_path):
                from core.scanner import ProjectScanner
                system_default = ProjectScanner.get_default_jianying_path()
                if system_default: default_path = system_default
            self.current_scan_path.set(default_path)

        saved_exe = config.get("jianying_exe")
        if saved_exe:
            self.jianying_exe_path.set(saved_exe)

        self.refresh_projects()

    def _set_jianying_exe(self):
        from tkinter import filedialog
        exe_path = filedialog.askopenfilename(title="选择剪映主程序", filetypes=[("EXE", "*.exe")])
        if exe_path:
            self.jianying_exe_path.set(exe_path)
            config = load_config()
            config['jianying_exe'] = exe_path
            save_config(config)
            print(f"已设置主程序: {exe_path}")

    def select_custom_folder(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="选择草稿根目录")
        if folder:
            self.current_scan_path.set(folder)
            save_config({"custom_path": folder})
            self.refresh_projects()

    def reset_default_path(self):
        from core.scanner import ProjectScanner
        path = ProjectScanner.get_default_jianying_path()
        if path:
            self.current_scan_path.set(path)
            save_config({"custom_path": None})
            self.refresh_projects()

    def redirect_logs(self):
        sys.stdout = TextHandler(self.log_console)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()