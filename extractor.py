import os
import cv2
import subprocess
import argparse
from pathlib import Path

def extract_video_from_jpeg(jpeg_path, output_video_path):
    """从小米动态照片的 .jpg 文件中提取内嵌视频数据，并使用 ffmpeg 修复 fragmented MP4 结构。"""
    try:
        with open(jpeg_path, 'rb') as f:
            data = f.read()

        marker = b'\xFF\xD9'
        marker_pos = data.find(marker)

        if marker_pos == -1:
            print(f"⚠️ 警告: 在文件 '{jpeg_path}' 中未找到 JPEG 结束标记。跳过此文件。")
            return False

        video_data = data[marker_pos + len(marker):]

        if not video_data:
            print(f"⚠️ 警告: 在文件 '{jpeg_path}' 的 JPEG 结束标记后未找到视频数据。跳过此文件。")
            return False

        # 保存原始提取的视频
        with open(output_video_path, 'wb') as f:
            f.write(video_data)

        print(f"💾 已提取原始视频: '{output_video_path}'")

        # --- Step 1: 尝试用 -f mp4 + -ignore_editlist 修复 fragment ---
        fixed_step1 = output_video_path.replace(".mp4", "_step1.mp4")
        cmd1 = [
            'ffmpeg',
            '-f', 'mp4',
            '-ignore_editlist', '1',  # 忽略编辑列表，常用于修复 fMP4
            '-i', output_video_path,
            '-c', 'copy',             # 先不转码，只修复结构
            '-movflags', 'faststart',
            '-y',
            fixed_step1
        ]

        result1 = subprocess.run(cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result1.returncode == 0:
            print(f"🔧 步骤1修复成功: '{fixed_step1}'")
            # --- Step 2: 重新编码确保兼容性 ---
            fixed_final = output_video_path.replace(".mp4", "_fixed.mp4")
            cmd2 = [
                'ffmpeg',
                '-i', fixed_step1,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', 'faststart',
                '-y',
                fixed_final
            ]
            result2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result2.returncode == 0:
                print(f"✅ 最终编码成功: '{fixed_final}'")
                # 替换原文件
                os.remove(output_video_path)
                os.remove(fixed_step1)  # 清理中间文件
                os.rename(fixed_final, output_video_path)
                return True
            else:
                print(f"❌ 步骤2编码失败: {result2.stderr.decode('utf-8', errors='ignore')}")
        else:
            print(f"❌ 步骤1修复失败，尝试直接强制转码...")

        # --- 备用方案：强制指定格式 + 忽略 moov + 使用 copyts ---
        fixed_fallback = output_video_path.replace(".mp4", "_fallback.mp4")
        cmd_fallback = [
            'ffmpeg',
            '-f', 'mp4',
            '-ignore_editlist', '1',
            '-fflags', '+genpts',     # 生成缺失的时间戳
            '-i', output_video_path,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', 'faststart',
            '-y',
            fixed_fallback
        ]
        result_fb = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result_fb.returncode == 0:
            print(f"✅ 备用方案成功: '{fixed_fallback}'")
            os.remove(output_video_path)
            os.rename(fixed_fallback, output_video_path)
            return True
        else:
            print(f"❌ 备用方案失败: {result_fb.stderr.decode('utf-8', errors='ignore')}")

        return False

    except Exception as e:
        print(f"💥 提取或编码视频 '{jpeg_path}' 时发生错误: {e}")
        return False

        # --- 终极兜底：当作原始 H.264 裸流处理 ---
        print("🔄 终极兜底：尝试作为 h264 裸流处理...")
        fixed_last_resort = output_video_path.replace(".mp4", "_last_resort.mp4")
        cmd_last = [
            'ffmpeg',
            '-f', 'h264',          # 强制当作裸流
            '-i', output_video_path,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-movflags', 'faststart',
            '-y',
            fixed_last_resort
        ]
        result_last = subprocess.run(cmd_last, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result_last.returncode == 0:
            print(f"✅ 终极兜底成功: '{fixed_last_resort}'")
            os.remove(output_video_path)
            os.rename(fixed_last_resort, output_video_path)
            return True
        else:
            print(f"❌ 终极兜底失败: {result_last.stderr.decode('utf-8', errors='ignore')}")


def extract_and_filter_frames(video_path, output_folder, min_blur_threshold, detect_faces_flag, keep_blur_info):
    """
    从视频文件中逐帧提取图片，并根据模糊度和人脸检测进行过滤。
    """
    # 健壮性检查
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        print(f"❌ 错误: 视频文件 '{video_path}' 不存在或为空。")
        return False

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ 错误: 无法打开视频文件 '{video_path}' 进行帧提取。")
        return False

    # 创建输出目录和 filtered_out 子目录
    os.makedirs(output_folder, exist_ok=True)
    filtered_out_dir = os.path.join(output_folder, "filtered_out")
    if not keep_blur_info:
        os.makedirs(filtered_out_dir, exist_ok=True)

    frame_count = 0
    saved_count = 0
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml') if detect_faces_flag else None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        has_face = True
        if detect_faces_flag:
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            has_face = len(faces) > 0

        frame_filename = f"frame_{frame_count:04d}.jpg"
        save_path = os.path.join(output_folder, frame_filename)

        reason = []
        if laplacian_var < min_blur_threshold:
            reason.append(f"模糊 (Blur: {laplacian_var:.2f})")
        if detect_faces_flag and not has_face:
            reason.append("无人脸")

        if reason:
            if keep_blur_info:
                cv2.imwrite(save_path, frame)
                print(f"⚠️  保留但标注: {frame_filename} (原因: {'; '.join(reason)})")
            else:
                cv2.imwrite(os.path.join(filtered_out_dir, frame_filename), frame)
                print(f"🗑️  剔除帧: {frame_filename} (原因: {'; '.join(reason)})")
        else:
            cv2.imwrite(save_path, frame)
            print(f"✅ 保留帧: {frame_filename} (Blur: {laplacian_var:.2f})")
            saved_count += 1

    cap.release()
    print(f"📊 本视频共提取 {frame_count} 帧，保留 {saved_count} 帧。")
    return True


def process_motion_photo(jpeg_path, base_output_folder, config):
    """处理单个小米动态照片文件"""
    filename = Path(jpeg_path).stem
    output_folder = os.path.join(base_output_folder, filename)
    temp_video_path = os.path.join(base_output_folder, f"{filename}_temp_extracted.mp4")

    print(f"\n📦 正在处理: {jpeg_path}")

    if not extract_video_from_jpeg(jpeg_path, temp_video_path):
        print(f"❌ 视频提取失败，跳过此文件。")
        return False

    if not extract_and_filter_frames(
        temp_video_path,
        output_folder,
        config['blur_threshold'],
        config['detect_faces'],
        config['keep_blur_info']
    ):
        print(f"❌ 帧提取失败。")
        return False

    # 清理临时视频文件
    try:
        os.remove(temp_video_path)
        print(f"🧹 已清理临时文件: {temp_video_path}")
    except Exception as e:
        print(f"⚠️  无法删除临时文件 {temp_video_path}: {e}")

    return True


def main(input_dir, output_dir, config):
    """批量处理目录中的所有小米动态照片"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    jpeg_files = list(input_path.glob("*.jpg")) + list(input_path.glob("*.jpeg"))
    total_files = len(jpeg_files)

    if total_files == 0:
        print(f"⚠️  在 '{input_dir}' 中未找到任何 .jpg 或 .jpeg 文件。")
        return

    print(f"📁 开始批量处理 '{input_dir}' 内的动态照片...")
    print(f"📤 结果将保存到 '{output_dir}'")
    print(f"⚙️  配置: 模糊阈值={config['blur_threshold']}, 检测人脸={config['detect_faces']}, 保留模糊信息={config['keep_blur_info']}")

    processed_count = 0
    for jpeg_file in jpeg_files:
        if process_motion_photo(str(jpeg_file), str(output_path), config):
            processed_count += 1

    print(f"\n🎉 批量处理完成！共处理了 {processed_count} / {total_files} 个动态照片。")
    print(f"📂 请在 '{output_dir}' 目录下查看提取和过滤后的帧图片。")
    print(f"🗑️  被剔除的帧位于每个照片文件夹下的 'filtered_out' 子目录中。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从小米动态照片中提取视频帧并过滤模糊/无人脸帧")
    parser.add_argument("input", help="输入目录路径，包含 .jpg 动态照片")
    parser.add_argument("output", help="输出目录路径，保存提取的帧")
    parser.add_argument("--blur-threshold", type=float, default=100.0, help="模糊阈值 (默认: 100.0)")
    parser.add_argument("--no-face-detect", action="store_true", help="禁用人脸检测")
    parser.add_argument("--keep-blur-info", action="store_true", help="保留模糊帧（添加标注），不移入 filtered_out")

    args = parser.parse_args()

    config = {
        'blur_threshold': args.blur_threshold,
        'detect_faces': not args.no_face_detect,
        'keep_blur_info': args.keep_blur_info
    }

    main(args.input, args.output, config)
