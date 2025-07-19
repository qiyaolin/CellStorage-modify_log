# 虚拟环境设置说明

## 问题解决

原来的项目包含 `Include/`、`Lib/` 和 `Scripts/` 文件夹，这些是 Python 虚拟环境的组成部分，占用了项目的大量空间。

## 解决方案

我们已经将虚拟环境移到了项目外部，现在项目结构更加清晰。

## 使用方法

### Windows 用户

1. **激活虚拟环境**：
   ```bash
   # 方法1：使用批处理文件
   activate_env.bat
   
   # 方法2：手动激活
   ..\venv_cellstorage\Scripts\activate
   ```

2. **运行应用**：
   ```bash
   python run.py
   ```

### Linux/Mac 用户

1. **激活虚拟环境**：
   ```bash
   source ../venv_cellstorage/bin/activate
   ```

2. **运行应用**：
   ```bash
   python run.py
   ```

## 虚拟环境位置

- **位置**：`../venv_cellstorage/`（项目上级目录）
- **包含**：所有 Python 依赖包和可执行文件

## 优势

1. **项目体积减小**：虚拟环境不再占用项目空间
2. **版本控制友好**：虚拟环境不会被提交到 Git
3. **多项目共享**：可以在多个相关项目间共享同一个虚拟环境
4. **清理方便**：可以轻松删除和重建虚拟环境

## 注意事项

- 确保在运行项目前激活虚拟环境
- 如果添加新的依赖，记得更新 `requirements.txt`
- 虚拟环境文件已添加到 `.gitignore` 中，不会被提交到版本控制 