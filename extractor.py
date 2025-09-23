# 文件名: extractor.py
import cv2
import os
import argparse
import json
import shutil # 用于移动/删除文件

# --- 配置文件加载 ---
CONFIG_FILE = 'config.json'
DEFAULT_CONFIG = {
    "input_folder": "input_photos",
    "output_folder": "extracted_frames",
    "min_blur_threshold": 100.0, # 模糊度阈值，低于此值的帧将被剔除
    "detect_faces": True,        # 是否启用无人脸剔除
    "keep_blur_info": False      # 是否保留模糊度信息文件
}

def load_config(config_path=CONFIG_FILE):
    """从 JSON 文件加载配置，如果文件不存在则返回默认配置。"""
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            # 确保必要的键存在并使用默认值填充缺失的键
            for key, default_val in DEFAULT_CONFIG.items():
                 if key not in config:
                     config[key] = default_val
            return config
        except Exception as e:
            print(f"警告: 读取配置文件 '{config_path}' 时出错: {e}。使用默认配置。")
    else:
        print(f"提示: 未找到配置文件 '{config_path}'。使用默认配置。")
    return DEFAULT_CONFIG
# --- 配置文件加载结束 ---


def calculate_blur_variance(image):
    """计算图像的拉普拉斯方差，用于衡量模糊度。"""
    # 转换为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # 计算拉普拉斯算子
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    # 计算方差
    variance = laplacian.var()
    return variance

def detect_faces(image):
    """使用 Haar 级联检测器检测图像中的人脸。"""
    # 加载 OpenCV 内置的人脸检测模型 (需要 opencv-contrib-python)
    # 注意：文件路径是相对于 OpenCV 安装目录的，cv2.data.haarcascades 提供了正确路径
    face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    
    if not os.path.exists(face_cascade_path):
        print(f"错误: 找不到人脸检测模型文件 '{face_cascade_path}'。请确保安装了 opencv-contrib-python。")
        return False

    face_cascade = cv2.CascadeClassifier(face_cascade_path)
    
    if face_cascade.empty():
        print(f"错误: 无法加载人脸检测模型 '{face_cascade_path}'。")
        return False

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    return len(faces) > 0 # 如果检测到至少一个人脸，则返回 True


def extract_video_from_jpeg(jpeg_path, output_video_path):
    """从小米动态照片的 .jpg 文件中提取内嵌的 .mp4 视频数据。"""
    try:
        with open(jpeg_path, 'rb') as f:
            data = f.read()

        marker = b'\xFF\xD9'
        marker_pos = data.find(marker)

        if marker_pos == -1:
            print(f"警告: 在文件 '{jpeg_path}' 中未找到 JPEG 结束标记。跳过此文件。")
            return False

        video_data = data[marker_pos + len(marker):]

        if not video_data:
            print(f"警告: 在文件 '{jpeg_path}' 的 JPEG 结束标记后未找到视频数据。跳过此文件。")
            return False

        with open(output_video_path, 'wb') as f:
            f.write(video_data)

        print(f"已提取视频: '{output_video_path}'")
        return True

    except Exception as e:
        print(f"提取视频 '{jpeg_path}' 时发生错误: {e}")
        return False


def extract_and_filter_frames(video_path, output_folder, min_blur_threshold, detect_faces_flag, keep_blur_info):
    """
    从视频文件中逐帧提取图片，并根据模糊度和人脸检测进行过滤。
    """
    # 创建输出文件夹和过滤文件夹
    filtered_folder = os.path.join(output_folder, "filtered_out")
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(filtered_folder, exist_ok=True)

    # 打开视频文件
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"错误: 无法打开视频文件 '{video_path}' 进行帧提取。")
        return False

    frame_count = 0
    kept_count = 0
    filtered_count = 0
    blur_info_lines = []

    print(f"开始提取和过滤帧 (模糊阈值: {min_blur_threshold}, 检测人脸: {detect_faces_flag})...")

    while True:
        success, image = cap.read()
        if not success:
            break

        filename = f"frame_{frame_count:04d}.jpg"
        full_output_path = os.path.join(output_folder, filename)
        
        # 保存原始帧（稍后可能移动）
        cv2.imwrite(full_output_path, image)
        
        # --- 分析帧 ---
        is_blurry = False
        has_face = True # 默认认为有人脸，除非启用检测且未检测到
        
        blur_variance = calculate_blur_variance(image)
        if keep_blur_info or blur_variance < min_blur_threshold:
             blur_info_lines.append(f"{filename}: Blur Variance = {blur_variance:.2f}\n")
        
        if blur_variance < min_blur_threshold:
            is_blurry = True

        if detect_faces_flag:
            has_face = detect_faces(image)
            
        # --- 决定是否保留 ---
        should_keep = not is_blurry and has_face

        if should_keep:
            print(f"  保留帧: {filename} (Blur: {blur_variance:.2f})") # 可选：打印保留的帧
            kept_count += 1
        else:
            # 移动到 filtered_out 文件夹
            filtered_output_path = os.path.join(filtered_folder, filename)
            shutil.move(full_output_path, filtered_output_path)
            reason = []
            if is_blurry: reason.append("模糊")
            if not has_face: reason.append("无人脸")
            print(f"  剔除帧: {filename} (原因: {', '.join(reason)}, Blur: {blur_variance:.2f})")
            filtered_count += 1
            
        frame_count += 1

    # 释放视频捕获对象
    cap.release()
    
    # 保存模糊度信息（如果需要）
    if keep_blur_info and blur_info_lines:
        blur_info_path = os.path.join(output_folder, "blur_info.txt")
        with open(blur_info_path, 'w') as f:
            f.writelines(blur_info_lines)
        print(f"模糊度信息已保存到: {blur_info_path}")

    if frame_count > 0:
        print(f"完成帧提取和过滤: '{output_folder}'")
        print(f"  总帧数: {frame_count}, 保留: {kept_count}, 剔除: {filtered_count}")
    else:
        print(f"警告: 从视频 '{video_path}' 未提取到任何帧。")
    return True


def process_motion_photo(jpeg_path, output_root_folder, config):
    """处理单个小米动态照片：提取视频并逐帧导出及过滤。"""
    if not os.path.exists(jpeg_path):
         print(f"警告: 文件 '{jpeg_path}' 不存在，已跳过。")
         return

    photo_name = os.path.splitext(os.path.basename(jpeg_path))[0]
    frames_output_folder = os.path.join(output_root_folder, f"{photo_name}_frames")
    temp_video_name = os.path.join(output_root_folder, f"{photo_name}_temp_extracted.mp4")

    print(f"正在处理: {jpeg_path}")

    if extract_video_from_jpeg(jpeg_path, temp_video_name):
        if extract_and_filter_frames(
            temp_video_name, 
            frames_output_folder, 
            config['min_blur_threshold'], 
            config['detect_faces'], 
            config['keep_blur_info']
        ):
            try:
                os.remove(temp_video_name)
            except OSError as e:
                print(f"警告: 删除临时文件 '{temp_video_name}' 时出错: {e}")


def main(input_folder, output_folder, config):
    """主函数：批量处理文件夹内的动态照片。"""
    if not os.path.isdir(input_folder):
        print(f"错误: 输入文件夹 '{input_folder}' 不存在。")
        return

    os.makedirs(output_folder, exist_ok=True)
    print(f"开始批量处理 '{input_folder}' 内的动态照片...")
    print(f"结果将保存到 '{output_folder}'")
    print(f"配置: 模糊阈值={config['min_blur_threshold']}, 检测人脸={config['detect_faces']}, 保留模糊信息={config['keep_blur_info']}")

    processed_count = 0
    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.jpg'):
            full_path = os.path.join(input_folder, filename)
            process_motion_photo(full_path, output_folder, config) # 传递配置
            processed_count += 1

    if processed_count > 0:
        print(f"\n批量处理完成！共处理了 {processed_count} 个动态照片。")
        print(f"请在 '{output_folder}' 目录下查看提取和过滤后的帧图片。")
        print(f"被剔除的帧位于每个照片文件夹下的 'filtered_out' 子目录中。")
    else:
        print(f"\n在 '{input_folder}' 中未找到任何 .jpg 文件。")


# 如果直接运行此脚本，则执行以下逻辑
if __name__ == "__main__":
    # 加载配置文件中的默认值
    config = load_config()

    parser = argparse.ArgumentParser(
        description="批量从小米动态照片 (.jpg) 中提取并过滤视频帧 (去模糊/无人脸)。",
        epilog="如果未提供命令行参数，将使用 config.json 中的配置。"
    )
    parser.add_argument(
        "-i", "--input",
        default=config["input_folder"],
        help=f"包含动态照片的输入文件夹路径 (默认: {config['input_folder']})"
    )
    parser.add_argument(
        "-o", "--output",
        default=config["output_folder"],
        help=f"存放提取结果的输出根文件夹路径 (默认: {config['output_folder']})"
    )
    # 可以通过命令行覆盖配置文件中的特定设置
    parser.add_argument(
        "--blur-threshold",
        type=float,
        default=config["min_blur_threshold"],
        help=f"模糊度阈值，方差低于此值的帧将被剔除 (默认: {config['min_blur_threshold']})"
    )
    parser.add_argument(
        "--no-face-detect",
        action='store_true',
        help="禁用无人脸帧的剔除功能"
    )
    parser.add_argument(
        "--keep-blur-info",
        action='store_true',
        help="保留包含每帧模糊度信息的 'blur_info.txt' 文件"
    )

    args = parser.parse_args()
    
    # 更新从命令行获取的配置
    config["input_folder"] = args.input
    config["output_folder"] = args.output
    config["min_blur_threshold"] = args.blur_threshold
    config["detect_faces"] = not args.no_face_detect # 注意逻辑取反
    config["keep_blur_info"] = args.keep_blur_info or config["keep_blur_info"] # 命令行优先

    main(args.input, args.output, config) # 传递完整的配置字典
