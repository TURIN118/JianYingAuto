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
        if not output: return 0
        return float(output)
    except FileNotFoundError:
        print("❌ 错误: 系统中未找到 'ffprobe' 命令。请检查环境变量。")
        return 0
    except Exception as e:
        print(f"❌ 获取时长异常: {e}")
        return 0


def process_single_video(input_path, output_path, config):
    """
    处理单个视频：裁剪、抽帧、分辨率统一、变速、深度去重
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

    # 构建视频滤镜链
    v_filters = []

    # 1. 基础处理：抽帧
    interval = config.get('frame_interval', 1)
    if interval > 1:
        v_filters.append(f"select='not(mod(n\,{interval}))'")
        v_filters.append("setpts=N/FRAME_RATE/TB")

        # 2. 深度去重：边缘裁剪 (改变分辨率指纹)
    if config.get('dedup_crop', False):
        crop_val = random.randint(1, 3)
        v_filters.append(f"crop=iw-{crop_val * 2}:ih-{crop_val * 2}")

    # 3. 分辨率统一
    res_mode = config.get('resolution', 'origin')
    if res_mode != 'origin':
        target_w, target_h = (1080, 1920) if res_mode == 'vertical' else (1920, 1080)
        v_filters.append(f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease")
        v_filters.append(f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black")

    # 4. 深度去重：画面微调 (打破像素一致性)
    if config.get('dedup_adjust', False):
        # 随机微调亮度、对比度、饱和度
        bright = round(random.uniform(0.98, 1.02), 3)
        contrast = round(random.uniform(0.98, 1.02), 3)
        sat = round(random.uniform(0.95, 1.05), 3)
        v_filters.append(f"eq=brightness={bright - 1}:contrast={contrast}:saturation={sat}")

    # 5. 深度去重：添加噪点 (改变数据特征)
    if config.get('dedup_noise', False):
        v_filters.append(f"noise=alls=1:allf=t")

    # 6. 变速
    speed = config.get('speed', 1.0)
    if speed != 1.0:
        v_filters.append(f"setpts=PTS/{speed}")

    # 音频滤镜
    a_filters = []
    if speed != 1.0:
        s = max(0.5, min(2.0, speed))
        a_filters.append(f"atempo={s}")

    # 组装命令
    cmd = ['ffmpeg', '-y', '-ss', str(start_time), '-i', input_path, '-t', str(end_time - start_time)]

    if v_filters: cmd.extend(['-vf', ','.join(v_filters)])
    if a_filters: cmd.extend(['-af', ','.join(a_filters)])

    cmd.extend(['-c:v', 'libx264', '-preset', 'fast', '-c:a', 'aac', output_path])

    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except subprocess.CalledProcessError:
        try:
            if '-af' in cmd:
                idx = cmd.index('-af');
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
    """拼接视频并添加BGM"""
    list_file = os.path.join(os.path.dirname(output_path), 'concat_list.txt')
    try:
        with open(list_file, 'w', encoding='utf-8') as f:
            for v in video_list:
                safe_path = os.path.abspath(v).replace('\\', '/')
                f.write(f"file '{safe_path}'\n")

        random_hash = "hash_" + "".join(random.choices(string.ascii_letters, k=8))
        temp_merge = output_path + ".temp.mp4"

        step1_output = temp_merge if (bgm_path and os.path.exists(bgm_path)) else output_path

        cmd_concat = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            '-metadata', f'comment={random_hash}',
            step1_output
        ]
        subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)

        if bgm_path and os.path.exists(bgm_path):
            cmd_bgm = [
                'ffmpeg', '-y',
                '-i', temp_merge,
                '-stream_loop', '-1', '-i', bgm_path,
                '-filter_complex', "[0:a]volume=0.5[a0];[1:a]volume=0.8[a1];[a0][a1]amix=inputs=2:duration=first[aout]",
                '-map', '0:v', '-map', '[aout]',
                '-c:v', 'copy', '-c:a', 'aac',
                '-shortest',
                '-metadata', f'comment={random_hash}',
                output_path
            ]
            subprocess.run(cmd_bgm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
            if os.path.exists(temp_merge): os.remove(temp_merge)

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg处理失败 (Exit Code: {e.returncode})")
        return False
    except Exception as e:
        print(f"❌ 拼接失败: {e}")
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