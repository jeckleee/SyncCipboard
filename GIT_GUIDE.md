# Git 提交指南

## ✅ .gitignore 配置完成

已创建 `.gitignore` 文件，确保只提交源代码，排除所有构建产物和临时文件。

## 📋 应该提交的文件清单

以下是项目中应该提交到 Git 的核心文件：

```
📁 项目根目录
├── .gitignore              # Git 忽略规则
├── BUILD_GUIDE.md          # 快速构建指南
├── LICENSE                 # 开源许可证
├── PACKAGING.md            # 详细打包文档
├── README.md               # 项目说明
├── build_macos.sh          # macOS 构建脚本
├── client_gui.py           # 客户端主程序（源代码）
├── config.ini              # 配置文件模板
├── requirements.txt        # Python 依赖列表
└── server.py               # 服务端程序（源代码）
```

**共 10 个文件** - 全部为源代码和文档，无二进制文件。

## 🚫 被忽略的文件/目录

以下文件和目录已被自动忽略，不会提交到 Git：

### 构建产物
- `*.build/` - Nuitka 构建目录
- `*.dist/` - Nuitka 分发目录
- `*.onefile-build/` - Nuitka 单文件构建
- `*.bin` - 二进制可执行文件
- `*.app/` - macOS 应用包
- `build_nuitka/` - 自定义构建输出
- `client_gui.build/` - 客户端构建输出

### Python 相关
- `__pycache__/` - Python 字节码缓存
- `*.pyc` - 编译的 Python 文件
- `.venv/` - 虚拟环境
- `venv/` - 虚拟环境（备用名称）
- `.pytest_cache/` - pytest 缓存
- `*.egg-info/` - 包信息

### IDE 和编辑器
- `.idea/` - PyCharm/IntelliJ IDEA
- `.vscode/` - Visual Studio Code
- `*.swp` - Vim 临时文件
- `.DS_Store` - macOS Finder 元数据

### 日志和临时文件
- `*.log` - 日志文件
- `build.log` - 构建日志
- `*.tmp` - 临时文件
- `*.bak` - 备份文件

### 分发包
- `*.zip` - 压缩包
- `*.dmg` - macOS 安装镜像
- `*.tar.gz` - 压缩归档
- `dist_package/` - 分发包目录

## 🔄 Git 工作流程

### 1. 查看当前状态

```bash
git status
```

应该看到类似输出：
```
On branch master
Changes to be committed:
  deleted:    .DS_Store
  deleted:    .idea/...
  deleted:    client_gui.build/...

Untracked files:
  .gitignore
```

### 2. 添加 .gitignore

```bash
git add .gitignore
```

### 3. 提交更改

```bash
git commit -m "chore: 添加 .gitignore，清理构建产物和临时文件"
```

提交信息会包含：
- 删除之前误提交的构建产物
- 添加 .gitignore 规则

### 4. 后续开发流程

```bash
# 修改代码后
git add client_gui.py
git commit -m "feat: 添加配置文件智能读取功能"

# 更新文档
git add README.md
git commit -m "docs: 更新使用说明"

# 添加新功能
git add build_macos.sh
git commit -m "feat: 添加 macOS 一键构建脚本"
```

## 📦 提交代码更新的完整流程

### 场景 1：修改了源代码

```bash
# 1. 查看修改
git status
git diff

# 2. 添加修改的文件
git add client_gui.py server.py

# 3. 提交
git commit -m "feat: 实现新的同步功能"

# 4. 推送到远程（如果有）
git push origin master
```

### 场景 2：更新了配置和文档

```bash
# 添加所有文档变更
git add *.md config.ini

# 提交
git commit -m "docs: 更新打包和使用文档"

# 推送
git push
```

### 场景 3：重新构建后提交

```bash
# 构建应用（会生成很多文件，但都会被忽略）
./build_macos.sh

# 查看状态（应该看不到 .build/ .app 等文件）
git status

# 只会看到修改的源代码
git add -u
git commit -m "refactor: 优化代码结构"
```

## ✨ Git 提交最佳实践

### 提交信息规范

使用约定式提交（Conventional Commits）：

```bash
# 新功能
git commit -m "feat: 添加剪贴板加密功能"

# 修复 bug
git commit -m "fix: 修复连接超时问题"

# 文档更新
git commit -m "docs: 完善安装说明"

# 代码重构
git commit -m "refactor: 简化配置读取逻辑"

# 性能优化
git commit -m "perf: 优化同步性能"

# 构建相关
git commit -m "build: 更新 Nuitka 构建参数"

# 杂项
git commit -m "chore: 更新依赖版本"
```

### 检查提交内容

在提交前，确保：

```bash
# 1. 查看将要提交的文件
git status

# 2. 查看具体改动
git diff --staged

# 3. 确认没有敏感信息（密码、密钥等）
git diff | grep -i "password\|secret\|key"
```

## 🔍 验证 .gitignore 是否生效

```bash
# 查看被忽略的文件
git status --ignored

# 测试特定文件是否被忽略
git check-ignore -v client_gui.build/client_gui.app

# 应该输出类似：
# .gitignore:XX:*.build/    client_gui.build/client_gui.app
```

## 🧹 清理已提交的不需要的文件

如果之前误提交了构建产物，已经执行清理：

```bash
# 从 Git 缓存中移除（已完成）
git rm -r --cached .DS_Store .idea/ client_gui.build/

# 提交删除操作
git commit -m "chore: 移除构建产物和 IDE 配置文件"
```

## 📊 提交统计

查看仓库状态：

```bash
# 查看提交历史
git log --oneline

# 查看文件列表
git ls-files

# 统计代码行数（仅源代码）
git ls-files | grep -E '\.(py|sh|md)$' | xargs wc -l
```

## ⚠️ 注意事项

### 1. config.ini 的处理

当前 `config.ini` **已提交**到仓库，作为配置模板：
- ✅ 适合：包含默认配置值
- ❌ 不适合：包含敏感信息（密码、密钥）

如果需要排除配置文件（例如包含个人配置），可以：

```bash
# 取消跟踪但保留本地文件
git rm --cached config.ini

# 在 .gitignore 中取消注释
# config.ini

# 提交一个示例配置
cp config.ini config.example.ini
git add config.example.ini
git commit -m "docs: 添加配置文件示例"
```

### 2. 虚拟环境

`.venv/` 已被忽略，其他开发者克隆后需要自己创建：

```bash
# 克隆仓库后
git clone <repo-url>
cd SyncCipboard

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 构建产物

所有构建产物都会被忽略，如需分发：
- 使用 GitHub Releases
- 使用独立的分发渠道
- 创建专门的 `releases` 分支（不推荐）

## 📚 相关资源

- [Git 官方文档](https://git-scm.com/doc)
- [约定式提交规范](https://www.conventionalcommits.org/zh-hans/)
- [GitHub .gitignore 模板](https://github.com/github/gitignore)
- [Python .gitignore 最佳实践](https://github.com/github/gitignore/blob/main/Python.gitignore)

## 🎯 快速命令参考

```bash
# 查看状态
git status

# 添加文件
git add <file>
git add .              # 添加所有修改（小心使用）

# 提交
git commit -m "message"

# 查看历史
git log --oneline -10

# 查看差异
git diff
git diff --staged

# 撤销修改（慎用）
git restore <file>
git restore --staged <file>

# 查看被忽略的文件
git status --ignored

# 检查文件是否被忽略
git check-ignore <file>
```

---

现在您的 Git 仓库已经干净整洁，只包含必要的源代码和文档！ 🎉

