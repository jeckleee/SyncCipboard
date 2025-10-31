# SyncClipboard Windows 打包脚本 (PowerShell)
# 使用 Nuitka 编译为单个 exe 文件

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SyncClipboard Windows 打包脚本" -ForegroundColor Cyan
Write-Host "  使用 Nuitka 编译为单个 exe 文件" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否安装了 Nuitka
Write-Host "[检查] 验证 Nuitka 是否已安装..." -ForegroundColor Yellow
$nuitkaCheck = python -m nuitka --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "       ✗ 未检测到 Nuitka，正在安装..." -ForegroundColor Red
    pip install nuitka zstandard ordered-set
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[失败] Nuitka 安装失败" -ForegroundColor Red
        Write-Host "请手动运行: pip install nuitka zstandard ordered-set" -ForegroundColor Yellow
        Read-Host "按回车键退出"
        exit 1
    }
    Write-Host "       ✓ Nuitka 安装完成" -ForegroundColor Green
} else {
    Write-Host "       ✓ Nuitka 已安装" -ForegroundColor Green
}

# 设置错误处理（在 Nuitka 检查之后）
$ErrorActionPreference = "Stop"

# 清理旧的构建产物
Write-Host ""
Write-Host "[1/4] 清理旧的构建产物..." -ForegroundColor Yellow
@("client_gui.build", "client_gui.dist", "client_gui.exe", "SyncClipboard.exe") | ForEach-Object {
    if (Test-Path $_) {
        Remove-Item $_ -Recurse -Force
    }
}
Write-Host "      已清理完成" -ForegroundColor Green

# 检查依赖
Write-Host ""
Write-Host "[2/4] 检查 Python 依赖..." -ForegroundColor Yellow
$pipList = pip list 2>&1 | Out-String
if ($pipList -notmatch "PyQt5") {
    Write-Host "       正在安装依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# 开始编译
Write-Host ""
Write-Host "[3/4] 开始编译（这可能需要 3-5 分钟）..." -ForegroundColor Yellow
Write-Host "      配置文件不会被打包，运行时从 exe 所在目录读取 config.ini" -ForegroundColor Cyan
Write-Host ""

$nuitkaArgs = @(
    "--standalone",
    "--onefile",
    "--windows-disable-console",
    "--enable-plugin=pyqt5",
    "--assume-yes-for-downloads",
    "--msvc=latest",
    "--output-filename=SyncClipboard.exe",
    "--company-name=SyncClipboard",
    "--product-name=SyncClipboard Client",
    "--file-version=1.0.0.0",
    "--product-version=1.0.0",
    "--file-description=跨设备剪贴板同步客户端"
)

# 如果存在图标文件，添加图标参数
if (Test-Path "icon.ico") {
    $nuitkaArgs += "--windows-icon-from-ico=icon.ico"
}

$nuitkaArgs += "client_gui.py"

python -m nuitka @nuitkaArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[失败] 编译过程中出现错误" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 整理产物
Write-Host ""
Write-Host "[4/4] 整理产物..." -ForegroundColor Yellow

if (Test-Path "SyncClipboard.exe") {
    # 创建 dist 目录
    if (-not (Test-Path "dist")) {
        New-Item -ItemType Directory -Path "dist" | Out-Null
    }
    
    # 移动 exe 文件
    Move-Item -Path "SyncClipboard.exe" -Destination "dist\" -Force
    
    # 复制配置文件模板
    if (Test-Path "config.ini") {
        Copy-Item -Path "config.ini" -Destination "dist\config.ini" -Force
        Write-Host "      已复制配置文件模板" -ForegroundColor Green
    }
    
    # 清理构建缓存（可选）
    if (Test-Path "client_gui.build") {
        Write-Host "      清理构建缓存..." -ForegroundColor Yellow
        Remove-Item "client_gui.build" -Recurse -Force
    }
    if (Test-Path "client_gui.dist") {
        Remove-Item "client_gui.dist" -Recurse -Force
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ✅ 打包完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📦 产物位置: dist\SyncClipboard.exe" -ForegroundColor Cyan
    Write-Host "⚙️  配置文件: dist\config.ini" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "💡 使用说明:" -ForegroundColor Yellow
    Write-Host "  1. 将 SyncClipboard.exe 和 config.ini 放在同一目录"
    Write-Host "  2. 编辑 config.ini 配置服务器地址"
    Write-Host "  3. 双击运行 SyncClipboard.exe"
    Write-Host ""
    
    # 显示文件大小
    $exeSize = (Get-Item "dist\SyncClipboard.exe").Length / 1MB
    Write-Host "📊 Exe 文件大小: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Cyan
    Write-Host ""
    
} else {
    Write-Host "[失败] 未找到生成的 exe 文件" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Read-Host "按回车键退出"

