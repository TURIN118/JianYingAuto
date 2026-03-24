# gui/handlers.py
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import threading
import os
import shutil
import json
from datetime import datetime

# 导入核心模块
from core.scanner import ProjectScanner
from core.draft_parser import DraftParser
from core.replacer import MaterialReplacer
from core.generator import generate_draft_copies
from automation.exporter import AutoExporter
from utils.preview import get_video_thumbnail

# 导入新的视频处理器
from core.video_processor import VideoBatchProcessor

# 尝试导入回收站库
try:
    from send2trash import send2trash

    HAS_TRASH_LIB = True
except ImportError:
    HAS_TRASH_LIB = False


class ProjectHandlers:
    """
    项目管理相关的逻辑：扫描、重命名、删除、选择
    """

    def refresh_projects(self):
        self.projects_data = ProjectScanner.scan_projects(self.current_scan_path.get())
        self.listbox_projects.delete(0, tk.END)
        if not self.projects_data:
            self.listbox_projects.insert(tk.END, "未找到项目")
            return
        for p in self.projects_data:
            self.listbox_projects.insert(tk.END, f"📁 {p['name']}")
        print(f"扫描完成: {len(self.projects_data)} 个项目")

    def on_project_select(self, event):
        sel = self.listbox_projects.curselection()
        if not sel: return
        proj = self.projects_data[sel[0]]
        self.current_draft_path = proj['path']
        print(f"选中模板: {proj['name']}")
        try:
            parser = DraftParser(self.current_draft_path)
            tracks = parser.get_video_tracks()
            self.track_combo['values'] = [f"轨道 {t['index']} ({len(t['track_data']['segments'])} 片段)" for t in
                                          tracks]
            if tracks: self.track_combo.current(0)
        except Exception as e:
            print(f"读取失败: {e}")

    def rename_draft(self):
        selection = self.listbox_projects.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个项目")
            return

        index = selection[0]
        project = self.projects_data[index]
        old_name = project['name']
        old_folder_path = project['folder']

        new_name = simpledialog.askstring("重命名项目", f"请输入新名称:", initialvalue=old_name)

        if new_name and new_name != old_name:
            try:
                parent_dir = os.path.dirname(old_folder_path)
                new_folder_path = os.path.join(parent_dir, new_name)

                if os.path.exists(new_folder_path):
                    messagebox.showerror("错误", "目标名称已存在，请更换名称。")
                    return

                os.rename(old_folder_path, new_folder_path)

                meta_path = os.path.join(new_folder_path, "draft_meta_info.json")
                if os.path.exists(meta_path):
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta_data = json.load(f)
                    meta_data['draft_name'] = new_name
                    with open(meta_path, 'w', encoding='utf-8') as f:
                        json.dump(meta_data, f, indent=4)

                print(f"✅ 项目已重命名为: {new_name}")
                self.refresh_projects()

            except Exception as e:
                print(f"❌ 重命名失败: {e}")
                messagebox.showerror("错误", str(e))

    def delete_draft(self):
        selection = self.listbox_projects.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个项目")
            return

        index = selection[0]
        project = self.projects_data[index]
        name = project['name']
        folder_path = project['folder']

        if not messagebox.askyesno("确认删除", f"确定要删除项目【{name}】吗？\n\n该操作将移入系统回收站，可恢复。"):
            return

        try:
            if HAS_TRASH_LIB:
                send2trash(folder_path)
                print(f"🗑️ 项目 [{name}] 已移入回收站")
                self.refresh_projects()
            else:
                messagebox.showinfo("提示", "请安装 send2trash 库以启用删除功能。\npip install send2trash")
        except Exception as e:
            print(f"❌ 删除失败: {e}")
            messagebox.showerror("错误", str(e))

    def restore_backup(self):
        if not self.current_draft_path:
            messagebox.showwarning("提示", "请先选择一个项目")
            return
        backup_dir = os.path.join(os.path.dirname(self.current_draft_path), "backups")
        if not os.path.exists(backup_dir):
            messagebox.showinfo("提示", "没有找到备份文件")
            return
        files = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.json')]
        if not files:
            messagebox.showinfo("提示", "备份文件夹为空")
            return
        latest_backup = max(files, key=os.path.getmtime)
        if messagebox.askyesno("确认还原", f"确定要还原以下备份吗？\n{os.path.basename(latest_backup)}"):
            try:
                shutil.copy2(latest_backup, self.current_draft_path)
                print("✅ 备份还原成功！")
                messagebox.showinfo("成功", "备份已还原，请重新打开项目查看。")
                self.on_project_select(None)
            except Exception as e:
                print(f"❌ 还原失败: {e}")


class MaterialHandlers:
    """
    素材管理相关的逻辑：添加、预览
    """

    def add_videos(self):
        files = filedialog.askopenfilenames(filetypes=[("Video", "*.mp4 *.mov *.avi")])
        for f in files:
            if f not in self.new_videos:
                self.new_videos.append(f)
                self.video_listbox.insert(tk.END, os.path.basename(f))
        print(f"添加 {len(files)} 个素材")

    def update_preview(self, event):
        selection = self.video_listbox.curselection()
        if not selection: return
        index = selection[0]
        if index >= len(self.new_videos): return
        video_path = self.new_videos[index]
        print(f"加载预览: {os.path.basename(video_path)}")
        threading.Thread(target=self._load_preview_image, args=(video_path,), daemon=True).start()

    def _load_preview_image(self, video_path):
        try:
            img = get_video_thumbnail(video_path, width=200)
            if img:
                self.root.after(0, lambda: self.preview_label.configure(image=img))
                self.root.after(0, lambda: setattr(self, 'current_img', img))
            else:
                self.root.after(0, lambda: self.preview_label.configure(text="无法读取", image=''))
        except Exception as e:
            print(f"预览错误: {e}")


class TaskHandlers:
    """
    核心任务逻辑：替换、生成、导出
    """

    def backup_draft(self):
        if not self.current_draft_path: return
        backup_dir = os.path.join(os.path.dirname(self.current_draft_path), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(self.current_draft_path, os.path.join(backup_dir, f"draft_content_{timestamp}.json"))

    def run_batch_generate(self):
        if not self.current_draft_path:
            messagebox.showwarning("提示", "请先选择【模板草稿】")
            return
        if not self.video_listbox.get(0):
            messagebox.showwarning("提示", "请先添加素材")
            return
        if not messagebox.askyesno("确认", f"将生成 {len(self.new_videos)} 个新草稿，是否继续？"):
            return
        threading.Thread(target=self._task_batch_generate, daemon=True).start()

    def _task_batch_generate(self):
        try:
            self.btn_batch_gen.config(state="disabled")
            print("========== 开始批量生成 ==========")
            track_index = self.track_combo.current()
            success_count = generate_draft_copies(self.current_draft_path, self.new_videos, track_index, log_func=print)
            print(f"========== 生成完成 ==========")
            messagebox.showinfo("完成", f"成功生成 {success_count} 个新草稿")
            self.refresh_projects()
        except Exception as e:
            messagebox.showerror("错误", str(e))
        finally:
            self.btn_batch_gen.config(state="normal")

    def run_replace(self):
        if not self.current_draft_path or not self.video_listbox.get(0):
            messagebox.showwarning("提示", "请选择项目和素材")
            return
        threading.Thread(target=self._task_replace, daemon=True).start()

    def _task_replace(self):
        try:
            self.btn_replace.config(state="disabled")
            print("========== 开始替换 ==========")
            self.backup_draft()
            parser = DraftParser(self.current_draft_path)
            replacer = MaterialReplacer(parser)
            idx = self.track_combo.current()
            tracks = parser.get_video_tracks()
            if tracks:
                replacer.replace_material_in_track(tracks[idx]['index'], self.new_videos)
                messagebox.showinfo("成功", "替换完成！")
        except Exception as e:
            messagebox.showerror("错误", str(e))
        finally:
            self.btn_replace.config(state="normal")

    def run_export(self):
        if not self.current_draft_path or not self.jianying_exe_path.get():
            messagebox.showwarning("提示", "请选择项目和主程序路径")
            return
        threading.Thread(target=self._task_export, daemon=True).start()

    def _task_export(self):
        try:
            self.btn_export.config(state="disabled")
            self.btn_pause.config(state="normal", text="⏸️ 暂停监控")
            self.btn_stop.config(state="normal")
            print("========== 开始导出 ==========")
            self.exporter_instance = AutoExporter(self.current_draft_path, self.jianying_exe_path.get(), log_func=print)
            self.exporter_instance.open_jianying()
            self.exporter_instance.export_video()
        except Exception as e:
            print(f"❌ 异常: {e}")
        finally:
            self.btn_export.config(state="normal")
            self.btn_pause.config(state="disabled")
            self.btn_stop.config(state="disabled")
            self.exporter_instance = None

    def toggle_pause_monitoring(self):
        if not self.exporter_instance: return
        if self.btn_pause.cget("text") == "⏸️ 暂停监控":
            self.exporter_instance.pause_monitoring()
            self.btn_pause.config(text="▶️ 继续监控")
        else:
            self.exporter_instance.resume_monitoring()
            self.btn_pause.config(text="⏸️ 暂停监控")

    def stop_monitoring(self):
        if self.exporter_instance:
            self.exporter_instance.stop_monitoring()
            self.btn_stop.config(state="disabled")
            self.btn_pause.config(state="disabled")


class VideoProcessHandlers:
    """
    视频批量处理逻辑
    """

    def select_process_folder(self):
        folder = filedialog.askdirectory(title="选择素材文件夹")
        if folder:
            self.process_input_path.set(folder)
            self.process_output_path.set(os.path.dirname(folder))

    def select_process_output(self):
        folder = filedialog.askdirectory(title="选择输出目录")
        if folder:
            self.process_output_path.set(folder)

    def select_bgm(self):
        file = filedialog.askopenfilename(title="选择BGM文件", filetypes=[("Audio", "*.mp3 *.wav *.aac")])
        if file:
            self.bgm_path.set(file)

    def update_progress(self, current, total):
        """更新进度条的回调函数"""
        self.progress_bar['value'] = (current / total) * 100
        self.progress_label.config(text=f"处理进度: {current}/{total}")
        # self.root.update_idletasks() # after(0) 已经可以保证UI更新

    def run_video_process(self):
        input_path = self.process_input_path.get()
        output_path = self.process_output_path.get()

        if not input_path or not output_path:
            messagebox.showwarning("提示", "请先选择输入和输出路径")
            return

        try:
            # 收集配置参数
            config = {
                'trim': int(self.trim_seconds.get()),
                'frame_interval': int(self.frame_interval.get()),
                'speed': float(self.speed_var.get()),
                'resolution': self.resolution_var.get(),
                'bgm_path': self.bgm_path.get()
            }

            if config['trim'] < 0 or config['frame_interval'] < 1:
                raise ValueError("参数错误")

        except Exception as e:
            messagebox.showerror("错误", f"参数格式错误: {e}")
            return

        threading.Thread(target=self._task_video_process, args=(input_path, output_path, config), daemon=True).start()

    def _task_video_process(self, input_path, output_path, config):
        try:
            self.btn_start_process.config(state="disabled")
            print("========== 开始视频处理任务 ==========")

            # 实例化处理器，传入进度回调
            processor = VideoBatchProcessor(log_func=print, progress_callback=self.update_progress)

            # 绑定 root 用于进度回调的 UI 更新
            processor.root = self.root

            success = processor.run(input_path, output_path, config)

            if success:
                print("========== 任务完成 ==========")
                self.root.after(0, lambda: self.progress_label.config(text="✅ 处理完成！"))
                messagebox.showinfo("完成", "视频处理与拼接已完成！")
            else:
                self.root.after(0, lambda: self.progress_label.config(text="❌ 处理失败"))

        except Exception as e:
            print(f"❌ 处理异常: {e}")
            messagebox.showerror("错误", str(e))
        finally:
            self.btn_start_process.config(state="normal")