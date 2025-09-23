#!/bin/bash
# 文件名: setup.sh
# 一键安装/设置脚本

set -e # 遇到错误时退出

echo "=== 小米动态照片帧提取器 设置脚本 ==="

# 1. 检查 Python 3 和 pip
echo "检查 Python 3 和 pip..."
if ! command -v python3 &> /dev/null
then
    echo "错误: 未找到 python3 命令。请先安装 Python 3。"
    exit 1
fi

if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null
then
    echo "错误: 未找到 pip 或 pip3 命令。请先安装 pip。"
    exit 1
fi

PYTHON_CMD="python3"
# 确定 pip 命令
if command -v pip3 &> /dev/null
then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null
then
    # 检查 pip 是否是 Python 3 的
    if pip --version | grep -q "python 3"; then
        PIP_CMD="pip"
    else
        echo "警告: 找到的 pip 不是 Python 3 的。尝试使用 pip3。"
        PIP_CMD="pip3" # 回退到 pip3
    fi
else
    echo "错误: 无法确定 pip 命令。"
    exit 1
fi

echo "使用 Python: $($PYTHON_CMD --version)"
echo "使用 Pip: $($PIP_CMD --version)"

# 2. 创建虚拟环境 (命名为 .venv，与 run_extractor.py 保持一致)
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "创建虚拟环境 '$VENV_DIR'..."
    $PYTHON_CMD -m venv $VENV_DIR
    echo "虚拟环境已创建。"
else
    echo "虚拟环境 '$VENV_DIR' 已存在。"
fi

# 3. 激活虚拟环境 (仅在当前脚本执行期间)
# 注意：脚本结束后，环境不会保持激活状态。用户需要手动 source .venv/bin/activate
# 但 run_extractor.py 会自动寻找 .venv
echo "激活虚拟环境..."
# POSIX 兼容的激活方式
# source $VENV_DIR/bin/activate # 这在脚本中不会影响父 shell
# 我们直接使用虚拟环境内的 pip 路径
VENV_PIP="$VENV_DIR/bin/pip"
if [ ! -f "$VENV_PIP" ]; then
    VENV_PIP="$VENV_DIR/Scripts/pip.exe" # Windows
fi

if [ ! -f "$VENV_PIP" ]; then
    echo "错误: 在虚拟环境 '$VENV_DIR' 中找不到 pip。"
    exit 1
fi

# 4. 升级 pip
echo "升级 pip..."
$VENV_PIP install --upgrade pip

# 5. 安装依赖
echo "安装依赖 (来自 requirements.txt)..."
$VENV_PIP install -r requirements.txt

echo ""
echo "=== 设置完成! ==="
echo "依赖已安装到虚拟环境 '$VENV_DIR'。"
echo ""
echo "要运行提取器，请执行:"
echo "  方法一 (推荐): ./run_extractor.py"
echo "  方法二: source .venv/bin/activate && python extractor.py && deactivate"
echo "  (Windows 方法二): .venv\Scripts\activate.bat && python extractor.py && deactivate"
echo ""
echo "请确保你的动态照片已放入 'input_photos' 文件夹，或修改 'config.json' 中的路径。"
echo "========================"
