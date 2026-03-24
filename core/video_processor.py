# core/video_processor.py
import os
import subprocess
import random
import string
import shutil
import re


def get_video_duration(video_path):
    """获取视频时长 (依赖 ffprobe)"""
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
               '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
        # 使用 CREATE_NO_WINDOW 防止弹出黑框
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                creationflags=subprocess.CREATE_NO_WINDOW)

        output = result.stdout.strip()
        if not output:
            return 0

        return float(output)

    except FileNotFoundError:
        print("❌ 错误: 系统中未找到 'ffprobe' 命令。")
        print("❌ 请确保已安装 FFmpeg 并将其添加到了系统环境变量 Path 中。")
        return 0
    except Exception as e:
        print(f"❌ 获取时长异常: {e}")
        return 0


def process_single_video(input_path, output_path, config):
    """
    处理单个视频：裁剪、抽帧、分辨率统一、变速
    """
    duration = get_video_duration(input_path)
    trim_seconds = config.get('trim', 0)

    if duration <= 0:
        print(f"跳过 {os.path.basename(input_path)}: 无法获取视频时长")
        return False

    start_time = trim_seconds
    end_time = duration - trim_seconds

    if end_time <= start_time:
        print(f"跳过 {os.path.basename(input_path)}: 视频时长不足")
        return False

    # 构建滤镜
    v_filters = []
    interval = config.get('frame_interval', 1)
    if interval > 1:
        v_filters.append(f"select='not(mod(n\,{interval}))'")
        v_filters.append("setpts=N/FRAME_RATE/TB")

    res_mode = config.get('resolution', 'origin')
    if res_mode != 'origin':
        target_w, target_h = (1080, 1920) if res_mode == 'vertical' else (1920, 1080)
        v_filters.append(f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease")
        v_filters.append(f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black")

    speed = config.get('speed', 1.0)
    if speed != 1.0:
        v_filters.append(f"setpts=PTS/{speed}")

    a_filters = []
    if speed != 1.0:
        s = max(0.5, min(2.0, speed))
        a_filters.append(f"atempo={s}")

    cmd = [
        'ffmpeg', '-y',
        '-ss', str(start_time),
        '-i', input_path,
        '-t', str(end_time - start_time),
    ]

    if v_filters: cmd.extend(['-vf', ','.join(v_filters)])
    if a_filters: cmd.extend(['-af', ','.join(a_filters)])

    cmd.extend(['-c:v', 'libx264', '-preset', 'fast', '-c:a', 'aac', output_path])

    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except subprocess.CalledProcessError:
        # 尝试无音频重试
        try:
            if '-af' in cmd:
                idx = cmd.index('-af')
                cmd.pop(idx);
                cmd.pop(idx)
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except:
            pass
    except:
        pass
    return False


def merge_with_bgm(video_list, output_path, bgm_path=None):
    """
    拼接视频并添加BGM，一次性完成
    """
    list_file = os.path.join(os.path.dirname(output_path), 'concat_list.txt')
    try:
        # 1. 生成拼接列表 (关键：统一转换为正斜杠绝对路径)
        with open(list_file, 'w', encoding='utf-8') as f:
            for v in video_list:
                # FFmpeg 对正斜杠兼容性最好
                safe_path = os.path.abspath(v).replace('\\', '/')
                f.write(f"file '{safe_path}'\n")

        # 生成随机元数据用于去重
        random_hash = "hash_" + "".join(random.choices(string.ascii_letters, k=8))

        # 2. 定义中间临时文件
        temp_merge = output_path + ".temp.mp4"

        # 3. 第一步：拼接视频片段
        # 如果没有BGM，直接输出最终文件并写入元数据
        # 如果有BGM，输出临时文件
        step1_output = temp_merge if (bgm_path and os.path.exists(bgm_path)) else output_path

        cmd_concat = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            '-metadata', f'comment={random_hash}',  # 写入元数据
            step1_output
        ]

        # 执行拼接
        subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)

        # 4. 第二步：添加BGM (如果需要)
        if bgm_path and os.path.exists(bgm_path):
            cmd_bgm = [
                'ffmpeg', '-y',
                '-i', temp_merge,
                '-stream_loop', '-1', '-i', bgm_path,
                '-filter_complex', "[0:a]volume=0.5[a0];[1:a]volume=0.8[a1];[a0][a1]amix=inputs=2:duration=first[aout]",
                '-map', '0:v', '-map', '[aout]',
                '-c:v', 'copy', '-c:a', 'aac',
                '-shortest',
                '-metadata', f'comment={random_hash}',  # 再次保留元数据
                output_path
            ]
            subprocess.run(cmd_bgm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)

            # 清理临时文件
            if os.path.exists(temp_merge):
                os.remove(temp_merge)

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg处理失败 (Exit Code: {e.returncode})")
        return False
    except Exception as e:
        print(f"❌ 拼接异常: {e}")
        return False
    finally:
        if os.path.exists(list_file):
            try:
                os.remove(list_file)
            except:
                pass


class VideoBatchProcessor:
    def __init__(self, log_func=print, progress_callback=None):
        self.log = log_func
        self.progress_callback = progress_callback
        self.root = None

    def run(self, folder_path, output_dir, config):
        if not folder_path or not os.path.isdir(folder_path):
            self.log("❌ 文件夹路径无效")
            return False

        files = [f for f in os.listdir(folder_path) if f.endswith(('.mp4', '.mov', '.avi'))]
        files.sort(key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])

        if not files:
            self.log("❌ 文件夹中没有视频文件")
            return False

        self.log(f"📂 扫描到 {len(files)} 个视频")

        temp_dir = os.path.join(output_dir, "temp_process")
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        os.makedirs(temp_dir)

        processed_files = []

        for idx, filename in enumerate(files):
            src_path = os.path.join(folder_path, filename)
            temp_path = os.path.join(temp_dir, f"temp_{idx:04d}.mp4")

            if self.progress_callback and self.root:
                self.root.after(0, lambda i=idx, t=len(files): self.progress_callback(i, t))

            self.log(f"🛠️ [{idx + 1}/{len(files)}] 处理: {filename}")

            if process_single_video(src_path, temp_path, config):
                processed_files.append(temp_path)
            else:
                self.log(f"⚠️ 跳过: {filename}")

        if not processed_files:
            self.log("❌ 没有有效的视频可供拼接")
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
            return False

        folder_name = os.path.basename(folder_path.rstrip('\\/'))
        final_name = f"{folder_name}.mp4"
        final_path = os.path.join(output_dir, final_name)

        self.log(f"🔗 正在拼接并添加BGM...")

        if merge_with_bgm(processed_files, final_path, config.get('bgm_path')):
            self.log(f"✅ 成功导出: {final_path}")
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            return True
        else:
            self.log("❌ 拼接过程出错")
            return False