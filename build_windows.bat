@echo off
chcp 65001 >nul
echo ========================================
echo   SyncClipboard Windows 打包脚本
echo   使用 Nuitka 编译为单个 exe 文件
echo ========================================
echo.

REM 检查是否安装了 Nuitka
python -m nuitka --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Nuitka，正在安装...
    pip install nuitka zstandard ordered-set
    if errorlevel 1 (
        echo [失败] Nuitka 安装失败，请手动运行: pip install nuitka zstandard ordered-set
        pause
        exit /b 1
    )
)

echo [1/4] 清理旧的构建产物...
if exist "client_gui.build" rmdir /s /q "client_gui.build"
if exist "client_gui.dist" rmdir /s /q "client_gui.dist"
if exist "client_gui.exe" del /f /q "client_gui.exe"
echo       已清理完成

echo.
echo [2/4] 检查依赖...
pip list | findstr "PyQt5" >nul
if errorlevel 1 (
    echo [警告] 未检测到 PyQt5，正在安装依赖...
    pip install -r requirements.txt
)

echo.
echo [3/4] 开始编译（这可能需要 3-5 分钟）...
echo       配置文件不会被打包，运行时从 exe 所在目录读取 config.ini
echo.

REM 检查是否存在图标文件
set ICON_PARAM=
if exist "icon.ico" (
    set ICON_PARAM=--windows-icon-from-ico=icon.ico
    echo       检测到图标文件: icon.ico
) else (
    echo       未找到 icon.ico，将使用默认图标
)

REM 使用 MinGW64 编译器（Nuitka 会自动下载，无需安装 Visual Studio）
python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-disable-console ^
    --enable-plugin=pyqt5 ^
    --assume-yes-for-downloads ^
    --mingw64 ^
    --output-filename=SyncClipboard.exe ^
    --company-name="SyncClipboard" ^
    --product-name="SyncClipboard Client" ^
    --file-version=1.0.0.0 ^
    --product-version=1.0.0 ^
    --file-description="跨设备剪贴板同步客户端" ^
    %ICON_PARAM% ^
    client_gui.py

if errorlevel 1 (
    echo.
    echo [失败] 编译过程中出现错误
    pause
    exit /b 1
)

echo.
echo [4/4] 整理产物...
if exist "SyncClipboard.exe" (
    if not exist "dist" mkdir dist
    move /y "SyncClipboard.exe" "dist\"
    
    REM 复制配置文件模板到 dist 目录
    if exist "config.ini" (
        copy /y "config.ini" "dist\config.ini"
        echo       已复制配置文件模板
    )
    
    echo.
    echo ========================================
    echo   ✅ 打包完成！
    echo ========================================
    echo.
    echo 产物位置: dist\SyncClipboard.exe
    echo 配置文件: dist\config.ini
    echo.
    echo 💡 使用说明:
    echo   1. 将 SyncClipboard.exe 和 config.ini 放在同一目录
    echo   2. 编辑 config.ini 配置服务器地址
    echo   3. 双击运行 SyncClipboard.exe
    echo.
) else (
    echo [失败] 未找到生成的 exe 文件
    pause
    exit /b 1
)

pause

