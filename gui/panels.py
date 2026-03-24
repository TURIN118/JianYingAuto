# gui/panels.py
import tkinter as tk
from tkinter import ttk


def setup_left_panel(parent, app):
    """
    构建左侧面板：路径设置、项目列表、管理工具栏
    """
    # --- 路径设置区 ---
    path_frame = ttk.LabelFrame(parent, text="草稿根目录")
    path_frame.pack(fill=tk.X, padx=5, pady=5)

    ttk.Entry(path_frame, textvariable=app.current_scan_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
    ttk.Button(path_frame, text="📁", width=3, command=app.select_custom_folder).pack(side=tk.LEFT, padx=2, pady=5)
    ttk.Button(path_frame, text="⟲", width=3, command=app.reset_default_path).pack(side=tk.LEFT, padx=2, pady=5)

    # --- 项目列表区 ---
    list_frame = ttk.LabelFrame(parent, text="本地项目库")
    list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # 工具栏
    toolbar = ttk.Frame(list_frame)
    toolbar.pack(fill=tk.X, padx=5, pady=2)

    ttk.Button(toolbar, text="🔄 刷新", command=app.refresh_projects, width=6).pack(side=tk.LEFT)
    ttk.Button(toolbar, text="↩️ 撤销", command=app.restore_backup, width=6).pack(side=tk.LEFT, padx=2)

    ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

    ttk.Button(toolbar, text="✏️ 重命名", command=app.rename_draft, width=8).pack(side=tk.LEFT)
    ttk.Button(toolbar, text="🗑️ 删除", command=app.delete_draft, width=6).pack(side=tk.LEFT, padx=2)

    # 项目列表
    app.listbox_projects = tk.Listbox(list_frame, font=("Microsoft YaHei UI", 10))
    app.listbox_projects.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    app.listbox_projects.bind('<<ListboxSelect>>', app.on_project_select)


def setup_right_panel(parent, app):
    """
    构建右侧面板：使用 NoteBook 实现多标签页
    """
    # 创建 NoteBook 控件
    notebook = ttk.Notebook(parent)
    notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # --- 标签页 1: 草稿替换 (原有功能) ---
    tab_draft = ttk.Frame(notebook)
    notebook.add(tab_draft, text="📝 草稿替换")
    _build_draft_tab(tab_draft, app)

    # --- 标签页 2: 视频处理 (新功能) ---
    tab_process = ttk.Frame(notebook)
    notebook.add(tab_process, text="🎬 视频混剪")
    _build_process_tab(tab_process, app)

    # --- 底部日志控制台 (共享) ---
    log_frame = ttk.LabelFrame(parent, text="运行日志")
    log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    app.log_console = tk.Text(log_frame, height=8, state='disabled', bg="#f0f0f0", font=("Consolas", 9))
    app.log_console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)


def _build_draft_tab(parent, app):
    """构建草稿替换页面的详细布局"""
    # 1. 素材设置区
    top_frame = ttk.LabelFrame(parent, text="素材替换设置")
    top_frame.pack(fill=tk.X, padx=5, pady=5)

    mat_container = ttk.Frame(top_frame)
    mat_container.pack(fill=tk.X, padx=5, pady=5, expand=True)

    # 列表区域
    list_area = ttk.Frame(mat_container)
    list_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    app.video_listbox = tk.Listbox(list_area, height=4)
    app.video_listbox.pack(fill=tk.BOTH, expand=True)
    app.video_listbox.bind('<<ListboxSelect>>', app.update_preview)

    btn_col = ttk.Frame(list_area)
    btn_col.pack(fill=tk.X)
    ttk.Button(btn_col, text="➕ 添加素材", command=app.add_videos).pack(side=tk.LEFT, pady=2)
    ttk.Button(btn_col, text="➖ 清空列表", command=lambda: app.video_listbox.delete(0, tk.END)).pack(side=tk.LEFT,
                                                                                                     padx=5)

    # 预览区域
    preview_area = ttk.LabelFrame(mat_container, text="素材预览")
    preview_area.pack(side=tk.RIGHT, padx=5)

    app.preview_label = ttk.Label(preview_area, text="无预览", width=25, anchor="center")
    app.preview_label.pack(padx=5, pady=5)

    # 轨道选择
    track_frame = ttk.Frame(top_frame)
    track_frame.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(track_frame, text="目标轨道:").pack(side=tk.LEFT)
    app.track_combo = ttk.Combobox(track_frame, state="readonly", width=30)
    app.track_combo.pack(side=tk.LEFT, padx=5)

    # 2. 操作区
    action_frame = ttk.LabelFrame(parent, text="执行操作")
    action_frame.pack(fill=tk.X, padx=5, pady=5)

    gen_frame = ttk.Frame(action_frame)
    gen_frame.pack(fill=tk.X, pady=5)
    app.btn_batch_gen = ttk.Button(gen_frame, text="🚀 批量生成副本", command=app.run_batch_generate)
    app.btn_batch_gen.pack(side=tk.LEFT, padx=10, expand=True)
    ttk.Label(gen_frame, text="← 根据素材数量生成", foreground="gray").pack(side=tk.LEFT)

    edit_frame = ttk.Frame(action_frame)
    edit_frame.pack(fill=tk.X, pady=5)
    app.btn_replace = ttk.Button(edit_frame, text="✏️ 直接修改当前草稿", command=app.run_replace)
    app.btn_replace.pack(side=tk.LEFT, padx=10, expand=True)
    app.btn_export = ttk.Button(edit_frame, text="💾 打开并导出", command=app.run_export)
    app.btn_export.pack(side=tk.LEFT, padx=10, expand=True)

    ctrl_frame = ttk.Frame(action_frame)
    ctrl_frame.pack(fill=tk.X, pady=5)
    app.btn_pause = ttk.Button(ctrl_frame, text="⏸️ 暂停监控", command=app.toggle_pause_monitoring, state="disabled")
    app.btn_pause.pack(side=tk.LEFT, padx=10, expand=True)
    app.btn_stop = ttk.Button(ctrl_frame, text="⏹️ 停止监控", command=app.stop_monitoring, state="disabled")
    app.btn_stop.pack(side=tk.LEFT, padx=10, expand=True)


def _build_process_tab(parent, app):
    """构建视频处理页面的详细布局"""
    # 输入设置
    input_frame = ttk.LabelFrame(parent, text="1. 输入设置")
    input_frame.pack(fill=tk.X, padx=10, pady=5)

    row1 = ttk.Frame(input_frame)
    row1.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(row1, text="素材文件夹:").pack(side=tk.LEFT)
    ttk.Entry(row1, textvariable=app.process_input_path, width=40).pack(side=tk.LEFT, padx=5)
    ttk.Button(row1, text="选择文件夹", command=app.select_process_folder).pack(side=tk.LEFT)

    # 输出设置
    output_frame = ttk.LabelFrame(parent, text="2. 输出设置")
    output_frame.pack(fill=tk.X, padx=10, pady=5)

    row2 = ttk.Frame(output_frame)
    row2.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(row2, text="输出目录:").pack(side=tk.LEFT)
    ttk.Entry(row2, textvariable=app.process_output_path, width=40).pack(side=tk.LEFT, padx=5)
    ttk.Button(row2, text="选择目录", command=app.select_process_output).pack(side=tk.LEFT)

    # 处理参数 - 核心功能
    param_frame = ttk.LabelFrame(parent, text="3. 处理参数")
    param_frame.pack(fill=tk.X, padx=10, pady=5)

    # 行1: 裁剪与抽帧
    row3 = ttk.Frame(param_frame)
    row3.pack(fill=tk.X, padx=5, pady=5)

    ttk.Label(row3, text="头尾裁剪(秒):").pack(side=tk.LEFT)
    ttk.Entry(row3, textvariable=app.trim_seconds, width=5).pack(side=tk.LEFT, padx=5)

    ttk.Label(row3, text="  抽帧间隔:").pack(side=tk.LEFT)
    ttk.Entry(row3, textvariable=app.frame_interval, width=5).pack(side=tk.LEFT, padx=5)
    ttk.Label(row3, text="(1=不抽)", foreground="gray").pack(side=tk.LEFT)

    # 行2: 变速
    row4 = ttk.Frame(param_frame)
    row4.pack(fill=tk.X, padx=5, pady=5)

    ttk.Label(row4, text="视频变速:").pack(side=tk.LEFT)
    ttk.Entry(row4, textvariable=app.speed_var, width=5).pack(side=tk.LEFT, padx=5)
    ttk.Label(row4, text="(1.0=原速, 1.2=1.2倍速)", foreground="gray").pack(side=tk.LEFT)

    # 行3: 分辨率统一
    row5 = ttk.Frame(param_frame)
    row5.pack(fill=tk.X, padx=5, pady=5)

    ttk.Label(row5, text="输出分辨率:").pack(side=tk.LEFT)
    res_options = [("保持原画", "origin"), ("统一竖屏 (9:16)", "vertical"), ("统一横屏 (16:9)", "horizontal")]
    for text, val in res_options:
        ttk.Radiobutton(row5, text=text, variable=app.resolution_var, value=val).pack(side=tk.LEFT, padx=5)

    # BGM设置
    bgm_frame = ttk.LabelFrame(parent, text="4. 背景音乐 (可选)")
    bgm_frame.pack(fill=tk.X, padx=10, pady=5)

    row_bgm = ttk.Frame(bgm_frame)
    row_bgm.pack(fill=tk.X, padx=5, pady=5)

    ttk.Label(row_bgm, text="BGM文件:").pack(side=tk.LEFT)
    ttk.Entry(row_bgm, textvariable=app.bgm_path, width=35).pack(side=tk.LEFT, padx=5)
    ttk.Button(row_bgm, text="选择音乐", command=app.select_bgm).pack(side=tk.LEFT)
    ttk.Button(row_bgm, text="清除", command=lambda: app.bgm_path.set("")).pack(side=tk.LEFT, padx=2)

    # 操作按钮与进度条
    action_frame = ttk.Frame(parent)
    action_frame.pack(fill=tk.X, padx=10, pady=20)

    app.btn_start_process = ttk.Button(action_frame, text="🚀 开始批量处理并拼接", command=app.run_video_process)
    app.btn_start_process.pack(pady=5)

    # 进度条
    app.progress_bar = ttk.Progressbar(action_frame, length=400, mode='determinate')
    app.progress_bar.pack(pady=5)
    app.progress_label = ttk.Label(action_frame, text="等待开始...")
    app.progress_label.pack()

    # 说明
    desc = "流程: 排序 -> 裁剪/抽帧/变速/统一尺寸 -> 拼接 -> 添加BGM -> 修改MD5"
    ttk.Label(parent, text=desc, foreground="#666").pack(pady=10)