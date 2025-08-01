# Cell Storage 集中式标签打印用户指南

## 概述

集中式标签打印系统允许用户在确认小管位置后自动打印标签。每个小管都会获得包含批次信息和存储位置的独立标签。

## 🔧 系统架构

```
用户界面 → 后端服务器 → 数据库 (打印任务) ← 打印服务器 → DYMO 打印机
```

- **前端**: 用户创建小管并请求打印标签
- **后端**: 管理数据库中的打印任务队列
- **打印服务器**: 监控后端任务并通过DYMO服务打印标签
- **DYMO服务**: 控制打印机的本地DYMO标签软件

## 📋 使用流程

### 1. 创建小管并选择打印

1. 在Cell Storage系统中，进入"Add CryoVial(s)"页面
2. 填写批次信息（批次名称、细胞系、通道数等）
3. 选择要添加的小管数量
4. 点击"Submit"提交表单

### 2. 确认位置并请求打印

1. 系统显示"Confirm Vial Placement"页面，显示所有小管的预定位置
2. 检查位置分配是否正确
3. 点击"Confirm and Save These X Vial(s)"
4. 在弹出的确认对话框中，**勾选"Print vial labels after saving"**
5. 点击"Save Vials"

### 3. 查看打印选项

系统保存小管后，会显示成功页面，并自动弹出"Print Label"模态框，包含：

- **批次信息**: 批次名称、批次ID、小管数量
- **服务状态**: 显示打印服务是否可用
- **小管列表**: 每个小管的位置和打印状态

### 4. 执行打印

在Print Label模态框中，您可以：

- **打印所有标签**: 点击"Print All Labels"按钮
- **打印单个标签**: 点击特定小管行的"Print"按钮
- **查看打印进度**: 实时查看每个打印任务的状态

### 5. 监控打印状态

每个打印任务会显示以下状态之一：
- **Ready**: 准备打印
- **Printing...**: 正在打印
- **Job #X queued**: 已加入打印队列
- **Print failed**: 打印失败

## 🏷️ 标签内容

每个小管标签包含：

```
批次名称 (粗体)
BXX - Vial N (粗体，大字体)
Tower/Drawer/Box (存储位置)
Position: RXC (行列位置)     日期
```

示例：
```
HEK293 Transfection
B123 - Vial 2
Tower1/Drawer2/Box3
Position: R2C3        2024-01-15
```

## ⚙️ 管理员设置

### 启用集中式打印

在后端配置文件中设置：
```python
# config.py
CENTRALIZED_PRINTING_ENABLED = True
```

### 数据库迁移

添加打印相关表：
```bash
# 在Flask应用目录中运行
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Print tables created successfully')
"
```

### 打印服务器设置

1. **安装打印服务器**:
```bash
cd dymo-print-server-nodejs
npm install
```

2. **配置环境变量**:
```bash
cp .env.example .env
# 编辑 .env 文件，设置后端URL和API令牌
```

3. **启动打印服务器**:
```bash
npm start
```

## 🔍 故障排除

### 用户端问题

#### 没有看到打印选项
**问题**: 确认页面没有打印复选框

**解决方案**:
- 确认管理员已启用集中式打印
- 检查后端服务器是否运行正常
- 联系管理员检查配置

#### 打印模态框显示"服务不可用"
**问题**: Print Label模态框显示打印服务不可用

**解决方案**:
- 等待几分钟后重试
- 联系管理员检查打印服务器状态
- 可以稍后手动打印标签

#### 打印任务失败
**问题**: 单个打印任务显示"Print failed"

**解决方案**:
- 点击该行的"Print"按钮重试
- 检查实验室打印机是否有纸
- 联系管理员检查打印机状态

### 管理员故障排除

#### 打印服务器无法连接后端
```bash
# 检查配置
cat dymo-print-server-nodejs/.env

# 检查后端URL是否正确
curl http://your-backend-url:5000/api/print/status

# 查看服务器日志
tail -f dymo-print-server-nodejs/logs/print-server.log
```

#### DYMO打印机未找到
```bash
# 测试DYMO服务
curl http://127.0.0.1:41951/DYMO/DLS/Printing/StatusConnected

# 列出可用打印机
curl http://127.0.0.1:41951/DYMO/DLS/Printing/GetPrinters

# 检查打印机名称配置
grep PRINTER_NAME dymo-print-server-nodejs/.env
```

#### 数据库中打印任务积压
```python
# 在Flask shell中检查
from app.cell_storage.models import PrintJob
pending_jobs = PrintJob.query.filter_by(status='pending').all()
print(f"Pending jobs: {len(pending_jobs)}")

# 检查失败的任务
failed_jobs = PrintJob.query.filter_by(status='failed').all()
for job in failed_jobs:
    print(f"Job {job.id}: {job.error_message}")
```

## 📊 监控和维护

### 检查系统状态

1. **后端API状态**:
```bash
curl http://your-backend:5000/api/print/status
```

2. **打印服务器状态**:
```bash
curl http://print-server:3001/api/status
```

3. **数据库统计**:
```python
from app.cell_storage.models import PrintJob, PrintServer

# 任务统计
total = PrintJob.query.count()
pending = PrintJob.query.filter_by(status='pending').count()
completed = PrintJob.query.filter_by(status='completed').count()
failed = PrintJob.query.filter_by(status='failed').count()

print(f"总任务: {total}, 待处理: {pending}, 已完成: {completed}, 失败: {failed}")

# 服务器统计
servers = PrintServer.query.all()
online_servers = [s for s in servers if s.is_online]
print(f"在线服务器: {len(online_servers)}/{len(servers)}")
```

### 定期维护

1. **清理旧任务** (可选):
```python
from datetime import datetime, timedelta
from app.cell_storage.models import PrintJob
from app import db

# 删除30天前的已完成/失败任务
cutoff_date = datetime.utcnow() - timedelta(days=30)
old_jobs = PrintJob.query.filter(
    PrintJob.status.in_(['completed', 'failed']),
    PrintJob.created_at < cutoff_date
).all()

for job in old_jobs:
    db.session.delete(job)
db.session.commit()
print(f"Cleaned up {len(old_jobs)} old jobs")
```

2. **日志轮转**:
```bash
# 配置logrotate或手动清理
find dymo-print-server-nodejs/logs -name "*.log" -mtime +30 -delete
```

## 🔧 高级配置

### 自定义标签模板

修改 `dymo-print-server-nodejs/src/dymo-service.js` 中的 `generateVialLabelXml` 函数来自定义标签布局。

### 打印优先级

支持四种优先级：
- `urgent`: 紧急
- `high`: 高
- `normal`: 普通 (默认)
- `low`: 低

### 批量操作

管理员可以通过数据库批量操作打印任务：

```python
# 重置失败的任务
failed_jobs = PrintJob.query.filter_by(status='failed').all()
for job in failed_jobs:
    job.status = 'pending'
    job.retry_count = 0
    job.error_message = None
db.session.commit()
```

## 📞 技术支持

### 联系信息
- 系统管理员: [管理员联系方式]
- 技术支持: [技术支持联系方式]

### 常用命令
```bash
# 检查打印服务器状态
curl http://print-server:3001/api/status

# 测试打印 (警告：会打印实际标签!)
curl -X POST http://print-server:3001/api/test-print

# 查看服务器日志
tail -f dymo-print-server-nodejs/logs/print-server.log

# 重启打印服务器
# 在打印服务器目录中按 Ctrl+C 停止，然后运行：
npm start
```

### 应急处理

如果集中式打印不可用：
1. 用户可以先保存小管，稍后再打印
2. 管理员可以从数据库导出标签数据手动打印
3. 系统仍然正常运行，只是没有自动打印功能

---

有关详细技术信息，请参阅 `dymo-print-server-nodejs/README.md`。