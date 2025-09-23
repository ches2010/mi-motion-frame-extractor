# 文件名: run_extractor.py
#!/usr/bin/env python3
"""一键运行脚本，用于执行小米动态照片帧提取器。"""

import subprocess
import sys
import os

def find_python_executable():
    """尝试找到合适的 Python 可执行文件。"""
    # 1. 检查虚拟环境
    venv_bin_python = os.path.join('.venv', 'bin', 'python') # Linux/macOS
    venv_scripts_python = os.path.join('.venv', 'Scripts', 'python.exe') # Windows
    if os.name == 'nt' and os.path.exists(venv_scripts_python):
        return venv_scripts_python
    elif os.path.exists(venv_bin_python):
        return venv_bin_python

    # 2. 检查 'python3'
    try:
        subprocess.check_call(['python3', '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return 'python3'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # 3. 检查 'python' (希望是 Python 3)
    try:
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        if result.returncode == 0 and 'Python 3' in result.stdout:
             return 'python'
    except FileNotFoundError:
        pass

    # 4. 如果都找不到，返回 None
    return None

def main():
    """主函数，执行 extractor.py。"""
    python_exe = find_python_executable()

    if not python_exe:
        print("错误: 找不到合适的 Python 3 解释器。请确保已安装 Python 3。")
        sys.exit(1)

    print(f"使用 Python 解释器: {python_exe}")

    # 构建命令
    cmd = [python_exe, 'extractor.py']

    print(f"执行命令: {' '.join(cmd)}")
    try:
        # 使用 subprocess.run 执行命令，并将 stdin, stdout, stderr 连接以便交互
        result = subprocess.run(cmd)
        # 脚本的退出码通常由 extractor.py 决定
        sys.exit(result.returncode)
    except FileNotFoundError:
        print(f"错误: 找不到脚本 'extractor.py' 或 Python 解释器 '{python_exe}'。")
        sys.exit(1)
    except Exception as e:
        print(f"运行脚本时发生未预期的错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
