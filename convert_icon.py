# -*- coding: utf-8 -*-
"""
图标格式转换工具
将 .icns (macOS) 转换为 .ico (Windows)
"""
import sys
import os

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from PIL import Image
except ImportError:
    print("错误: 未安装 Pillow 库")
    print("请运行: pip install pillow")
    sys.exit(1)

def convert_icns_to_ico(icns_path, ico_path):
    """
    将 .icns 文件转换为 .ico 文件
    需要安装 pillow: pip install pillow
    """
    if not os.path.exists(icns_path):
        print(f"错误: 找不到文件 {icns_path}")
        return False
        
    try:
        print(f"正在读取: {icns_path}")
        # 尝试直接打开 .icns 文件
        img = Image.open(icns_path)
        
        # 转换为 RGBA 模式（如果需要）
        if img.mode != 'RGBA':
            print(f"  转换颜色模式: {img.mode} -> RGBA")
            img = img.convert('RGBA')
        
        # 创建多个尺寸的图标（Windows 标准尺寸）
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        print(f"  生成尺寸: {', '.join([f'{w}x{h}' for w, h in sizes])}")
        
        # 保存为 .ico 格式（包含多个尺寸）
        img.save(ico_path, format='ICO', sizes=sizes)
        
        print(f"[成功] 已转换: {icns_path} -> {ico_path}")
        return True
        
    except Exception as e:
        print(f"[失败] 转换失败: {e}")
        print("\n提示:")
        print("  1. 确保已安装 Pillow: pip install pillow")
        print("  2. 或者使用在线工具转换: https://convertio.co/zh/icns-ico/")
        print("  3. 或者使用 ImageMagick: magick convert app.icns icon.ico")
        return False

if __name__ == "__main__":
    # 默认转换 app.icns -> icon.ico
    icns_file = "app.icns"
    ico_file = "icon.ico"
    
    if len(sys.argv) > 1:
        icns_file = sys.argv[1]
    if len(sys.argv) > 2:
        ico_file = sys.argv[2]
    
    print("="*50)
    print("图标转换工具 (ICNS -> ICO)")
    print("="*50)
    success = convert_icns_to_ico(icns_file, ico_file)
    print("="*50)
    
    if not success:
        sys.exit(1)

