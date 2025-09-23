#!/usr/bin/env python3
import subprocess
import sys
import os

# 配置路径（请根据你的实际路径修改）
INPUT_DIR = "/mnt/workspace/ComfyUI/input/mmv"
OUTPUT_DIR = "/mnt/workspace/ComfyUI/output/jpg"

# 可选配置
BLUR_THRESHOLD = 100.0
DETECT_FACES = True    # True = 检测人脸, False = 不检测
KEEP_BLUR_INFO = False # False = 剔除模糊帧, True = 保留并标注

print("使用 Python 解释器: .venv/bin/python")

# 构建命令
cmd = [
    ".venv/bin/python",
    "extractor.py",
    INPUT_DIR,
    OUTPUT_DIR,
    "--blur-threshold", str(BLUR_THRESHOLD)
]

if not DETECT_FACES:
    cmd.append("--no-face-detect")

if KEEP_BLUR_INFO:
    cmd.append("--keep-blur-info")

print("执行命令:", " ".join(cmd))

# 执行
result = subprocess.run(cmd)

if result.returncode == 0:
    print("✅ Done!")
else:
    print("❌ Error occurred during execution.")
    sys.exit(1)
