# 小米动态照片帧提取器 (Mi Motion Photo Frame Extractor)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) (如果添加了LICENSE文件)

一个用于批量从小米手机拍摄的动态照片 (`.jpg` 文件) 中提取视频帧为独立图片，并自动剔除模糊帧和无人脸帧的 Python 工具。

## 功能

*   直接处理小米手机导出的 `.jpg` 动态照片文件。
*   自动识别并提取内嵌的视频数据。
*   将提取出的视频逐帧保存为 `.jpg` 图片。
*   **智能过滤**：
    *   **剔除模糊帧**：基于拉普拉斯方差算法。
    *   **剔除无人脸帧**：使用 OpenCV Haar 级联分类器 (可配置开关)。
*   支持批量处理指定文件夹内的所有动态照片。
*   通过 `config.json` 配置文件轻松管理输入输出路径及过滤参数。
*   提供 `run_extractor.py` 一键运行脚本。
*   提供 `setup.sh` 脚本简化环境设置 (Linux/macOS)。
*   适用于 Ubuntu (及其他 Linux 发行版)、macOS 和 Windows。

## 依赖

*   Python 3.6+
*   **`opencv-contrib-python`** (注意：替换掉了 `opencv-python`，以包含人脸检测模型)

## 安装与设置

### 方法一：使用 Setup 脚本 (推荐 - Linux/macOS)

1.  **克隆仓库**:
    ```bash
    git clone https://github.com/ches2010/mi-motion-frame-extractor.git
    cd mi-motion-frame-extractor
    ```
2.  **运行 Setup 脚本**:
    ```bash
    chmod +x setup.sh # 赋予执行权限
    ./setup.sh
    ```
    这个脚本会检查 Python/pip，创建虚拟环境 (`.venv`)，并安装依赖。

### 方法二：手动设置

1.  **克隆仓库**:
    ```bash
    git clone https://github.com/<你的用户名>/mi-motion-frame-extractor.git
    cd mi-motion-frame-extractor
    ```
2.  **(推荐) 创建虚拟环境**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate # Linux/macOS
    # .venv\Scripts\activate.bat # Windows
    ```
3.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

## 配置

编辑 `config.json` 文件来设置默认的输入输出路径和过滤参数:

```json
{
    "input_folder": "input_photos",
    "output_folder": "extracted_frames",
    "min_blur_threshold": 100.0,
    "detect_faces": true,
    "keep_blur_info": false
}
```

*   `input_folder`: 包含待处理动态照片 (`.jpg`) 的文件夹。可以是相对路径或绝对路径。
*   `output_folder`: 存放提取结果的根文件夹。每个照片的结果会放在该根目录下的独立子文件夹中。可以是相对路径或绝对路径。
*   `min_blur_threshold` (数值): 模糊度阈值。计算出的拉普拉斯方差低于此值的帧将被视为模糊并被剔除。值越高，保留的图片越清晰，但也可能误删。可以根据你的照片调整，100 是一个常见的起始值。
*   `detect_faces` (布尔值 `true`/`false`): 是否启用无人脸帧的剔除功能。设置为 `true` 会剔除检测不到人脸的帧。
*   `keep_blur_info` (布尔值 `true`/`false`): 是否为每个处理后的照片文件夹生成一个 `blur_info.txt` 文件，记录每帧的模糊度方差。

## 使用方法

### 方法一：使用一键运行脚本 (推荐)

确保已按上述方法设置好环境 (特别是激活了虚拟环境)。

```bash
python run_extractor.py
```
此脚本会读取 `config.json` 中的配置并执行提取和过滤。

### 方法二：直接运行核心脚本

#### 使用 `config.json` 配置:
```bash
python extractor.py
```

#### 使用命令行参数覆盖配置:
```bash
# 示例：更改输入输出路径，设置模糊阈值为150，禁用人脸检测
python extractor.py -i /path/to/your/input_photos -o /path/to/your/output_frames --blur-threshold 150 --no-face-detect

# 示例：保留模糊度信息
python extractor.py --keep-blur-info
```

**命令行参数详解:**

*   `-i` 或 `--input`: 包含动态照片的输入文件夹路径 (默认: `config.json` 中的 `input_folder`)。
*   `-o` 或 `--output`: 存放提取结果的输出根文件夹路径 (默认: `config.json` 中的 `output_folder`)。
*   `--blur-threshold <数值>`: 设置模糊度阈值 (默认: `config.json` 中的 `min_blur_threshold`)。
*   `--no-face-detect`: 禁用无人脸帧剔除功能 (默认: `config.json` 中的 `detect_faces` 为 `true` 时启用)。
*   `--keep-blur-info`: 保留模糊度信息文件 (默认: `config.json` 中的 `keep_blur_info`)。

## 输出结构

处理完成后，`output_folder` (例如 `extracted_frames`) 的结构如下：

```
extracted_frames/
├── PHOTO_NAME_1_frames/
│   ├── frame_0001.jpg  (保留的清晰帧)
│   ├── frame_0003.jpg  (保留的清晰帧)
│   ├── ...
│   ├── filtered_out/   (被剔除的帧)
│   │   ├── frame_0000.jpg (模糊)
│   │   ├── frame_0002.jpg (无人脸)
│   │   └── ...
│   └── blur_info.txt   (如果启用) 记录每帧模糊度
├── PHOTO_NAME_2_frames/
│   ├── frame_0000.jpg
│   ├── ...
│   └── filtered_out/
└── ...
```

## 许可证

本项目采用 MIT 许可证 - 请参阅 [LICENSE](LICENSE) 文件了解详情。
