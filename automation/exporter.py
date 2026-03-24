# automation/exporter.py
import pyautogui
import time
import os
import subprocess
import psutil
import threading

try:
    import pygetwindow as gw
except ImportError:
    gw = None


class AutoExporter:
    def __init__(self, draft_path, jianying_exe=None, log_func=print):
        self.draft_path = draft_path
        self.jianying_exe = jianying_exe
        self.log = log_func
        self.process_name = "JianyingPro.exe"

        # 线程控制标志
        self._pause_event = threading.Event()
        self._stop_event = threading.Event()
        # 默认是运行状态
        self._pause_event.set()

    def open_jianying(self):
        self.log("正在启动剪映...")
        if self.jianying_exe and os.path.exists(self.jianying_exe):
            try:
                subprocess.Popen([self.jianying_exe, self.draft_path])
                self.log(f"已启动进程: {os.path.basename(self.jianying_exe)}")
                time.sleep(8)
                return True
            except Exception as e:
                self.log(f"启动失败: {e}")
                return False
        return False

    def activate_window(self):
        if not gw: return
        self.log("正在寻找剪映窗口...")
        keywords = ["JianyingPro", "剪映专业版", "CapCut"]

        for _ in range(5):
            try:
                windows = gw.getAllWindows()
                for win in windows:
                    if any(k in win.title for k in keywords):
                        if win.isMinimized: win.restore()
                        win.activate()
                        self.log("窗口已激活")
                        return True
            except:
                pass
            time.sleep(1)
        return False

    def pause_monitoring(self):
        self._pause_event.clear()
        self.log("⏸️ 监控已暂停")

    def resume_monitoring(self):
        self._pause_event.set()
        self.log("▶️ 监控已继续")

    def stop_monitoring(self):
        self._stop_event.set()
        self.log("⏹️ 监控已停止")

    def monitor_rendering(self, timeout=300):
        """
        智能监控渲染进度，支持暂停/继续
        """
        self.log("正在监控渲染进度 (检测CPU占用率)...")

        start_time = time.time()
        low_cpu_count = 0

        target_pid = None
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == self.process_name:
                target_pid = proc.info['pid']
                break

        if not target_pid:
            self.log("未找到剪映进程，无法监控")
            return

        try:
            process = psutil.Process(target_pid)
        except:
            return

        while not self._stop_event.is_set():
            # 检查暂停状态（阻塞直到恢复）
            self._pause_event.wait()

            # 检查停止状态
            if self._stop_event.is_set():
                break

            # 超时检测
            if time.time() - start_time > timeout:
                self.log(f"监控超时({timeout}秒)，请手动检查。")
                break

            try:
                cpu_percent = process.cpu_percent(interval=1.0)
                self.log(f"当前CPU占用: {cpu_percent}%")

                # 判定逻辑
                if cpu_percent < 5.0:
                    low_cpu_count += 1
                    if low_cpu_count >= 5:
                        self.log("✅ 检测到渲染完成。")
                        self.close_project()
                        break
                else:
                    low_cpu_count = 0
            except psutil.NoSuchProcess:
                self.log("进程已结束")
                break
            except Exception as e:
                print(f"监控异常: {e}")

    def close_project(self):
        self.log("尝试关闭项目窗口...")
        if gw:
            try:
                # 再次激活窗口确保按键生效
                wins = gw.getWindowsWithTitle("JianyingPro")
                if wins:
                    wins[0].activate()
                    time.sleep(0.5)
            except:
                pass

        pyautogui.hotkey('ctrl', 'w')
        time.sleep(1)
        pyautogui.press('enter')

    def export_video(self):
        self.log("=== 准备执行导出操作 ===")

        # 重置标志
        self._pause_event.set()
        self._stop_event.clear()

        self.activate_window()
        time.sleep(2)

        self.log("尝试发送导出快捷键...")
        pyautogui.press('esc')
        time.sleep(0.5)

        pyautogui.keyDown('ctrl')
        time.sleep(0.1)
        pyautogui.press('e')
        time.sleep(0.1)
        pyautogui.keyUp('ctrl')

        self.log("已发送指令。如未弹出窗口，请手动点击导出。")

        time.sleep(5)
        self.monitor_rendering()