# start_app.ps1
$currentDir = "C:\Inventory\CellStorage-modify_log\CellStorage-modify_log" 
Set-Location $currentDir

# 激活虚拟环境并运行 serve.py
# '&' 操作符用于运行脚本或可执行文件
& ".\venv\Scripts\activate.ps1"
python serve.py