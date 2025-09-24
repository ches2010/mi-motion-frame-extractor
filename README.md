# 小米动态照片帧提取工具

一个功能完整的工具，用于提取小米动态照片中的所有帧，并可独立删除包含模糊人脸的图片。

## 功能特点

- 提取小米动态照片中的所有视频帧
- 支持批量处理多个文件或目录
- 通过配置文件设置参数，也支持命令行直接操作
- 独立的模糊人脸检测与删除功能
- 可在帧提取后自动执行模糊人脸清理，也可单独使用

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

3. 创建配置文件（可选）
   ```bash
   cp extractor_config.ini.default extractor_config.ini
   ```

## 使用方法

### 1. 帧提取功能

基本用法（使用配置文件设置）：

```
python3 xiaomi_live_photo_extractor.py
```

命令行指定参数：# 处理单个文件
```
python3 xiaomi_live_photo_extractor.py ./path/to/photo.jpg
```

# 处理目录并递归子目录
```
python3 xiaomi_live_photo_extractor.py ./photos_dir -r
```

# 指定输出目录
```
python3 xiaomi_live_photo_extractor.py -o ./my_output_dir
```

# 提取间隔为2（每2帧提取1帧）
```
python3 xiaomi_live_photo_extractor.py -i 2
```

### 2. 模糊人脸删除（独立功能）
# 清理指定目录中的模糊人脸图片
```
python3 xiaomi_live_photo_extractor.py --remove-blur --blur-dir ./frames_dir
```

# 自定义模糊阈值（值越低标准越严格）
```
python3 xiaomi_live_photo_extractor.py --remove-blur --blur-dir ./frames_dir --blur-threshold 80
```

# 模拟运行（不实际删除，仅显示结果）
```
python3 xiaomi_live_photo_extractor.py --remove-blur --blur-dir ./frames_dir --dry-run
```

### 3. 组合使用

帧提取后自动清理模糊人脸：# 方法1：通过命令行参数（需要配置文件支持）
```
python3 xiaomi_live_photo_extractor.py ./photos_dir
```

# 方法2：直接指定（需要先设置配置文件post_extract_clean_blur=true）
```
python3 xiaomi_live_photo_extractor.py ./photos_dir
```

## 配置文件说明

配置文件`extractor_config.ini`包含以下主要部分：

- `[Paths]`：设置输入输出路径
- `[Extraction]`：帧提取相关参数
- `[Processing]`：处理模式设置
- `[Cleanup]`：模糊人脸删除相关参数

可通过修改配置文件来设置默认行为，命令行参数会覆盖配置文件设置。

## 注意事项

- 小米动态照片通常以.jpg或.heic为扩展名，但包含视频数据
- 模糊检测使用拉普拉斯方差算法，阈值可根据需求调整
- 首次运行时会自动下载人脸检测模型（约1MB）
- 处理大量文件时建议使用`--dry-run`先测试效果
    
