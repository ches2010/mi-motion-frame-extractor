import os
import sys
import argparse
import cv2
from PIL import Image
import tempfile
import shutil
import struct
from glob import glob
import configparser
import numpy as np

# 人脸检测模型路径（自动下载）
FACE_CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)

def load_config(config_path=None):
    """加载配置文件"""
    config = configparser.ConfigParser()
    # 配置文件查找顺序：指定路径 → 当前目录 → 用户主目录
    config_paths = []
    if config_path:
        config_paths.append(config_path)
    config_paths.extend([
        'extractor_config.ini',
        os.path.join(os.path.expanduser('~'), 'extractor_config.ini')
    ])
    
    # 读取第一个找到的配置文件
    for path in config_paths:
        if os.path.exists(path):
            config.read(path)
            print(f"加载配置文件: {path}")
            return config
    return None

def get_config_value(config, section, key, default=None, is_bool=False):
    """获取配置值，支持默认值和布尔类型转换"""
    if not config or section not in config:
        return default
    try:
        if is_bool:
            return config.getboolean(section, key)
        return config.get(section, key)
    except (configparser.NoOptionError, ValueError):
        return default

def is_xiaomi_live_photo(file_path):
    """判断是否为小米动态照片"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(1024)
            if b"MI LIVE PHOTO" in header:
                return True
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.heic']:
                f.seek(0)
                while True:
                    data = f.read(1024*1024)
                    if not data:
                        break
                    if data.find(b'ftypmp4') != -1:
                        return True
    except Exception as e:
        print(f"检查动态照片格式出错: {str(e)}")
    return False

def find_mp4_in_file(file_path):
    """提取文件中的MP4视频"""
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
            ftyp_pos = file_content.find(b'ftypmp4') or file_content.find(b'ftypisom')
            if ftyp_pos == -1:
                return None
            start_pos = max(0, ftyp_pos - 4)
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_file.write(file_content[start_pos:])
                return temp_file.name
    except Exception as e:
        print(f"提取MP4出错: {str(e)}")
        return None

def extract_frames(video_path, output_dir, interval=1, max_frames=500):
    """从视频提取帧"""
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"无法打开视频: {video_path}")
        return False

    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count <= 0 or frame_count > max_frames * 10:
            frame_count = max_frames
        duration = frame_count / fps
    except:
        fps = 30
        frame_count = max_frames
        duration = "未知"

    print(f"视频信息: 帧率{fps:.1f} | 预计帧数{frame_count} | 时长{duration}秒")
    frame_num, extracted_num, error_num = 0, 0, 0

    while frame_num < frame_count and error_num < 5:
        ret, frame = cap.read()
        if not ret:
            error_num += 1
            frame_num += 1
            continue

        if frame_num % interval == 0:
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                save_path = os.path.join(output_dir, f"frame_{extracted_num:04d}.png")
                Image.fromarray(frame_rgb).save(save_path)
                extracted_num += 1
            except Exception as e:
                print(f"保存帧出错: {str(e)}")
        
        frame_num += 1
        if frame_num > max_frames * 2:
            break

    cap.release()
    print(f"提取完成: {extracted_num} 帧保存到 {output_dir}")
    return extracted_num > 0

def calculate_blur_score(image_path):
    """计算图像模糊度（拉普拉斯方差）"""
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0
        return cv2.Laplacian(img, cv2.CV_64F).var()
    except Exception as e:
        print(f"计算模糊度出错: {str(e)}")
        return 0.0

def detect_and_remove_blurry_faces(input_dir, blur_threshold=100.0, dry_run=False):
    """独立功能：检测并删除包含模糊人脸的图片"""
    if not os.path.isdir(input_dir):
        print(f"输入目录不存在: {input_dir}")
        return False

    # 获取所有图片文件
    img_extensions = ['.png', '.jpg', '.jpeg', '.bmp']
    img_files = [f for f in os.listdir(input_dir) if os.path.splitext(f)[1].lower() in img_extensions]
    
    if not img_files:
        print(f"目录中无图片文件: {input_dir}")
        return False

    print(f"\n=== 开始模糊人脸检测（阈值: {blur_threshold}）===")
    print(f"待检测图片数量: {len(img_files)}")
    removed_count = 0

    for img_file in img_files:
        img_path = os.path.join(input_dir, img_file)
        img = cv2.imread(img_path)
        if img is None:
            print(f"跳过损坏文件: {img_file}")
            continue

        # 检测人脸
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            continue  # 无脸图片不处理

        # 计算整图模糊度
        blur_score = calculate_blur_score(img_path)
        
        # 判断是否模糊
        if blur_score < blur_threshold:
            print(f"删除模糊人脸图片: {img_file}（模糊度: {blur_score:.1f}）")
            if not dry_run:
                os.remove(img_path)
            removed_count += 1

    print(f"=== 检测完成 ===")
    print(f"总计检测: {len(img_files)} 张")
    print(f"删除模糊人脸: {removed_count} 张")
    print(f"剩余图片: {len(img_files) - removed_count} 张\n")
    return True

def process_live_photo(file_path, base_output_dir=None, interval=1, max_frames=500):
    """处理单张动态照片"""
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    file_dir = os.path.dirname(file_path)
    base_output_dir = base_output_dir or os.path.join(file_dir, "live_photo_frames")
    output_dir = os.path.join(base_output_dir, file_name)

    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return False

    print(f"\n处理文件: {file_path}")
    print(f"输出目录: {output_dir}")

    # 提取视频并处理
    if is_xiaomi_live_photo(file_path):
        print("检测到小米动态照片格式")
        mp4_path = find_mp4_in_file(file_path)
        if mp4_path:
            result = extract_frames(mp4_path, output_dir, interval, max_frames)
            os.unlink(mp4_path)
            return result

    # 直接作为视频处理
    if extract_frames(file_path, output_dir, interval, max_frames):
        return True

    # 尝试其他提取策略
    print("尝试其他提取策略...")
    for ext in ['.mp4', '.mov']:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
            temp_path = temp_file.name
            with open(file_path, 'rb') as f:
                f.seek(os.path.getsize(file_path) // 2)
                shutil.copyfileobj(f, temp_file)
            if extract_frames(temp_path, output_dir, interval, max_frames):
                os.unlink(temp_path)
                return True
            os.unlink(temp_path)

    print("处理失败")
    return False

def batch_process(files, base_output_dir=None, interval=1, max_frames=500):
    """批量处理动态照片"""
    total = len(files)
    success = 0
    print(f"开始批量处理: {total} 个文件")

    for i, file in enumerate(files, 1):
        print(f"\n===== 处理 {i}/{total} =====")
        if process_live_photo(file, base_output_dir, interval, max_frames):
            success += 1

    print(f"\n批量处理完成")
    print(f"成功: {success}/{total}")
    return success > 0

def main():
    """主函数：解析参数并执行对应功能"""
    parser = argparse.ArgumentParser(description='小米动态照片帧提取工具（含独立模糊人脸删除功能）')
    
    # 功能选择（默认：帧提取；--remove-blur：仅模糊人脸删除）
    parser.add_argument('--remove-blur', action='store_true', 
                      help='仅执行模糊人脸删除功能（独立模式）')
    
    # 帧提取相关参数
    parser.add_argument('input', nargs='?', help='帧提取：输入文件/目录（默认读取配置文件）')
    parser.add_argument('-o', '--output', help='帧提取：基础输出目录（覆盖配置文件）')
    parser.add_argument('-i', '--interval', type=int, help='帧提取：帧间隔（覆盖配置文件）')
    parser.add_argument('-m', '--max-frames', type=int, help='帧提取：最大帧数（覆盖配置文件）')
    parser.add_argument('-r', '--recursive', action='store_true', 
                      help='帧提取：递归处理子目录（覆盖配置文件）')
    
    # 模糊人脸删除相关参数（独立功能）
    parser.add_argument('--blur-dir', help='模糊删除：目标图片目录（--remove-blur模式必填）')
    parser.add_argument('--blur-threshold', type=float, 
                      help='模糊删除：模糊度阈值（默认100，值越低越严格）')
    parser.add_argument('--dry-run', action='store_true', 
                      help='模糊删除：模拟运行（不实际删除文件）')
    
    # 通用参数
    parser.add_argument('-c', '--config', help='指定配置文件路径')

    args = parser.parse_args()
    config = load_config(args.config)

    # 1. 独立模式：仅执行模糊人脸删除
    if args.remove_blur:
        # 检查必填参数
        blur_dir = args.blur_dir or get_config_value(config, 'Paths', 'blur_clean_dir')
        if not blur_dir or not os.path.isdir(blur_dir):
            print("错误：请通过 --blur-dir 指定图片目录，或在配置文件中设置 blur_clean_dir")
            sys.exit(1)
        
        # 获取参数（命令行 > 配置文件 > 默认值）
        blur_threshold = args.blur_threshold or \
                        get_config_value(config, 'Cleanup', 'blur_threshold', 100.0, is_bool=False)
        dry_run = args.dry_run or \
                  get_config_value(config, 'Cleanup', 'dry_run', False, is_bool=True)
        
        # 执行模糊人脸删除
        detect_and_remove_blurry_faces(blur_dir, blur_threshold, dry_run)
        sys.exit(0)

    # 2. 默认模式：执行帧提取（可选后续删除模糊人脸）
    # 处理输入参数
    input_path = args.input or get_config_value(config, 'Paths', 'input_dir')
    if not input_path or not (os.path.isfile(input_path) or os.path.isdir(input_path)):
        print("错误：请指定输入文件/目录，或在配置文件中设置 input_dir")
        sys.exit(1)
    
    # 读取参数（命令行 > 配置文件 > 默认值）
    base_output_dir = args.output or get_config_value(config, 'Paths', 'output_dir', './live_photo_frames')
    interval = args.interval or int(get_config_value(config, 'Extraction', 'interval', 1))
    max_frames = args.max_frames or int(get_config_value(config, 'Extraction', 'max_frames', 500))
    recursive = args.recursive or get_config_value(config, 'Processing', 'recursive', False, is_bool=True)
    post_clean_blur = get_config_value(config, 'Processing', 'post_extract_clean_blur', False, is_bool=True)
    blur_threshold = float(get_config_value(config, 'Cleanup', 'blur_threshold', 100.0))

    # 收集待处理文件
    if os.path.isdir(input_path):
        patterns = ['*.jpg', '*.jpeg', '*.heic', '*.mp4', '*.mov']
        files = []
        for p in patterns:
            search_path = os.path.join(input_path, '**', p) if recursive else os.path.join(input_path, p)
            files.extend(glob(search_path, recursive=recursive))
        files = list(set(files))
    else:
        files = [input_path]

    if not files:
        print("未找到可处理的文件")
        sys.exit(1)

    # 执行帧提取
    batch_process(files, base_output_dir, interval, max_frames)

    # 可选后续操作：提取完成后删除模糊人脸
    if post_clean_blur:
        print("\n=== 开始帧提取后的模糊人脸删除 ===")
        # 遍历所有提取结果目录
        for root, dirs, _ in os.walk(base_output_dir):
            for dir_name in dirs:
                frame_dir = os.path.join(root, dir_name)
                print(f"\n处理帧目录: {frame_dir}")
                detect_and_remove_blurry_faces(frame_dir, blur_threshold)

if __name__ == "__main__":
    main()
    
