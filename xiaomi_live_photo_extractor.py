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

def load_config(config_path=None):
    """加载配置文件"""
    config = configparser.ConfigParser()
    
    # 查找配置文件的可能位置
    possible_paths = []
    if config_path:
        possible_paths.append(config_path)
    possible_paths.append("extractor_config.ini")
    possible_paths.append(os.path.expanduser("~/.extractor_config.ini"))
    possible_paths.append("/etc/extractor_config.ini")
    
    # 尝试加载配置文件
    config_loaded = False
    for path in possible_paths:
        if os.path.exists(path):
            config.read(path)
            config_loaded = True
            print(f"已加载配置文件: {path}")
            break
    
    if not config_loaded:
        print("未找到配置文件，将使用默认设置")
    
    return config

def get_config_value(config, section, key, default=None):
    """获取配置值，带默认值"""
    try:
        return config.get(section, key)
    except:
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
                    ftyp_pos = data.find(b'ftypmp4')
                    if ftyp_pos != -1:
                        return True
    except Exception as e:
        print(f"检查小米动态照片格式时出错: {str(e)}")
    return False

def find_mp4_in_file(file_path):
    """在文件中查找MP4视频数据并提取"""
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
            
            ftyp_pos = file_content.find(b'ftypmp4')
            if ftyp_pos == -1:
                ftyp_pos = file_content.find(b'ftypisom')
            
            if ftyp_pos == -1:
                print("未找到MP4视频标记")
                return None
                
            start_pos = max(0, ftyp_pos - 4)
            video_data = file_content[start_pos:]
            
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_file.write(video_data)
                return temp_file.name
                
    except Exception as e:
        print(f"提取MP4视频时出错: {str(e)}")
        return None

def extract_frames(video_path, output_dir, interval=1, max_frames=1000):
    """从视频中提取帧"""
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"无法打开视频文件: {video_path}")
        return False
    
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        if frame_count <= 0 or frame_count > max_frames * 10:
            print(f"检测到异常的帧计数: {frame_count}，将使用安全模式提取")
            frame_count = max_frames
            fps = fps if fps > 0 and fps < 100 else 30
            duration = "未知（使用安全模式）"
    except:
        print("无法获取视频信息，将使用安全模式提取")
        fps = 30
        frame_count = max_frames
        duration = "未知（使用安全模式）"
    
    print(f"视频信息: {os.path.basename(video_path)}")
    print(f"帧率: {fps:.2f} FPS")
    print(f"预计最大帧数: {frame_count}")
    print(f"时长: {duration}")
    
    frame_number = 0
    extracted_count = 0
    error_count = 0
    empty_frame_count = 0
    
    while frame_number < frame_count and error_count < 5 and empty_frame_count < 10:
        ret, frame = cap.read()
        
        if not ret:
            error_count += 1
            frame_number += 1
            continue
        
        if frame is None or frame.size == 0:
            empty_frame_count += 1
            frame_number += 1
            continue
        
        error_count = 0
        empty_frame_count = 0
        
        if frame_number % interval == 0:
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_filename = os.path.join(output_dir, f"frame_{extracted_count:04d}.png")
                Image.fromarray(frame_rgb).save(frame_filename)
                extracted_count += 1
            except Exception as e:
                print(f"保存帧时出错: {str(e)}")
        
        frame_number += 1
        
        if frame_number > max_frames * 2:
            print(f"已达到安全上限 {max_frames * 2} 帧，停止提取")
            break
    
    cap.release()
    print(f"提取完成，共提取 {extracted_count} 帧")
    return extracted_count > 0

def process_live_photo(file_path, base_output_dir=None, interval=1, max_frames=1000):
    """处理小米动态照片"""
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    file_dir = os.path.dirname(file_path)
    
    if base_output_dir is None:
        base_output_dir = os.path.join(file_dir, "live_photo_frames")
    
    output_dir = os.path.join(base_output_dir, file_name)
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return False
    
    print(f"\n处理文件: {file_path}")
    print(f"帧将保存到: {output_dir}")
    
    if is_xiaomi_live_photo(file_path):
        print("检测到小米动态照片格式")
        mp4_path = find_mp4_in_file(file_path)
        if mp4_path:
            print("成功提取内嵌的MP4视频")
            result = extract_frames(mp4_path, output_dir, interval, max_frames)
            os.unlink(mp4_path)
            if result:
                return True
    
    if extract_frames(file_path, output_dir, interval, max_frames):
        return True
    
    print("直接处理失败，尝试从文件中提取视频部分...")
    
    try:
        for ext in ['.mp4', '.mov', '.avi']:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                temp_path = temp_file.name
                
                with open(file_path, 'rb') as f:
                    f.seek(0)
                    shutil.copyfileobj(f, temp_file)
                
                if extract_frames(temp_path, output_dir, interval, max_frames):
                    os.unlink(temp_path)
                    return True
                
                with open(file_path, 'rb') as f:
                    f.seek(os.path.getsize(file_path) // 2)
                    shutil.copyfileobj(f, temp_file)
                
                if extract_frames(temp_path, output_dir, interval, max_frames):
                    os.unlink(temp_path)
                    return True
                
                with open(file_path, 'rb') as f:
                    f.seek(os.path.getsize(file_path) * 2 // 3)
                    shutil.copyfileobj(f, temp_file)
                
                if extract_frames(temp_path, output_dir, interval, max_frames):
                    os.unlink(temp_path)
                    return True
                
                os.unlink(temp_path)
        
        print("所有提取方法都已尝试，但未能成功提取视频帧")
        return False
        
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        return False

def batch_process(files, base_output_dir=None, interval=1, max_frames=1000):
    """批量处理多个文件"""
    total_files = len(files)
    success_count = 0
    
    print(f"开始批量处理，共 {total_files} 个文件")
    
    for i, file_path in enumerate(files, 1):
        print(f"\n===== 处理文件 {i}/{total_files} =====")
        if process_live_photo(file_path, base_output_dir, interval, max_frames):
            success_count += 1
    
    print(f"\n批量处理完成")
    print(f"总文件数: {total_files}")
    print(f"成功处理: {success_count}")
    print(f"处理失败: {total_files - success_count}")

def main():
    # 加载配置文件
    config = load_config()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='小米动态照片帧提取工具（支持配置文件）')
    parser.add_argument('input', nargs='?', help='输入文件路径或目录（可在配置文件中设置）')
    parser.add_argument('-c', '--config', help='指定配置文件路径')
    parser.add_argument('-o', '--output', help='基础输出目录路径（可在配置文件中设置）')
    parser.add_argument('-i', '--interval', type=int, help='帧提取间隔（可在配置文件中设置）')
    parser.add_argument('-m', '--max-frames', type=int, help='最大提取帧数限制（可在配置文件中设置）')
    parser.add_argument('-r', '--recursive', action='store_true', 
                      help='递归处理目录中的所有文件（可在配置文件中设置）')
    
    args = parser.parse_args()
    
    # 从配置文件获取默认值，命令行参数优先于配置文件
    input_path = args.input or get_config_value(config, 'Paths', 'input_dir')
    base_output_dir = args.output or get_config_value(config, 'Paths', 'output_dir')
    
    # 处理数字参数
    try:
        interval = args.interval or int(get_config_value(config, 'Extraction', 'interval', 1))
    except:
        interval = 1
    
    try:
        max_frames = args.max_frames or int(get_config_value(config, 'Extraction', 'max_frames', 500))
    except:
        max_frames = 500
    
    # 处理布尔参数
    recursive = args.recursive or get_config_value(config, 'Processing', 'recursive', 'false').lower() == 'true'
    
    # 检查输入是否有效
    if not input_path or not os.path.exists(input_path):
        print("错误: 请指定有效的输入文件或目录（通过命令行参数或配置文件）")
        return
    
    # 收集所有要处理的文件
    files_to_process = []
    
    if os.path.isdir(input_path):
        patterns = ['*.jpg', '*.jpeg', '*.heic', '*.mp4', '*.mov']
        for pattern in patterns:
            if recursive:
                files = glob(os.path.join(input_path, '**', pattern), recursive=True)
            else:
                files = glob(os.path.join(input_path, pattern))
            files_to_process.extend(files)
        
        files_to_process = list(set(files_to_process))
    else:
        files_to_process.append(input_path)
    
    if not files_to_process:
        print("未找到任何可处理的文件")
        return
    
    # 执行批量处理
    batch_process(files_to_process, base_output_dir, interval, max_frames)

if __name__ == "__main__":
    main()
