#!/bin/bash

# 小米动态照片帧提取工具安装脚本
# 适用于Ubuntu系统

# 更新系统包
echo "更新系统包..."
sudo apt update -y

# 安装系统依赖
echo "安装系统依赖..."
sudo apt install -y python3 python3-pip python3-opencv

# 安装Python依赖
echo "安装Python依赖..."
pip3 install -r requirements.txt

echo "安装完成！"
echo "使用方法: python3 xiaomi_live_photo_extractor.py --help"
    
