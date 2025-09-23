# 小米动态照片帧提取工具

一个用于提取小米动态照片中所有帧的Python工具，支持批量处理和配置文件设置。

## 功能特点

- 提取小米动态照片中的所有视频帧
- 支持批量处理多个文件或目录
- 通过配置文件设置输入输出目录等参数
- 自动识别小米动态照片格式
- 支持递归处理子目录中的文件

## 安装方法

### 在Ubuntu系统上

1. 克隆本仓库
   ```bash
   git clone https://github.com/ches2010/xiaomi-live-photo-extractor.git
   cd xiaomi-live-photo-extractor
   ```

2. 运行安装脚本
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

## 配置文件

可通过修改`extractor_config.ini`文件来设置默认参数：
[Paths]
input_dir = ./photos      ; 输入目录或文件路径
output_dir = ./extracted_frames  ; 输出目录路径

[Extraction]
interval = 1              ; 帧提取间隔，1表示提取所有帧
max_frames = 500          ; 最大提取帧数限制

[Processing]
recursive = false         ; 是否递归处理子目录 (true/false)
## 使用方法

### 基本用法

如果已在配置文件中设置好输入目录，直接运行：python3 xiaomi_live_photo_extractor.py
### 命令行参数

命令行参数会覆盖配置文件中的设置：
# 指定输入目录
python3 xiaomi_live_photo_extractor.py ./my_photos

# 指定输出目录
python3 xiaomi_live_photo_extractor.py -o ./my_output

# 递归处理子目录
python3 xiaomi_live_photo_extractor.py -r

# 指定配置文件
python3 xiaomi_live_photo_extractor.py -c ./my_config.ini

# 设置帧提取间隔和最大帧数
python3 xiaomi_live_photo_extractor.py -i 2 -m 300
## 注意事项

- 小米动态照片通常以.jpg或.heic为扩展名，但包含视频数据
- 如果提取失败，建议先用小米手机将动态照片导出为单独的视频文件
- 提取的帧会保存在输出目录中以原文件名命名的子文件夹内
