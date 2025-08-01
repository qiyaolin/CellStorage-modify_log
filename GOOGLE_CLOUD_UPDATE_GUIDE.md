# Google Cloud 集中式打印系统更新指南

为现有部署 `https://ambient-decoder-467517-h8.nn.r.appspot.com/` 添加集中式标签打印功能。

## 🚀 更新步骤

### 第一步：数据库迁移

1. **确保本地环境配置正确**：
```bash
# 确保有Google Cloud SDK和正确的凭据
gcloud auth application-default login
gcloud config set project ambient-decoder-467517-h8

# 设置Cloud SQL连接环境变量（如果需要）
export INSTANCE_CONNECTION_NAME=your-instance-connection-name
```

2. **运行数据库迁移**：
```bash
# 在项目根目录运行
python cloud_migration_update.py
```

这会：
- 连接到现有的Cloud SQL数据库
- 添加 `print_jobs` 和 `print_servers` 表
- 验证新表的功能
- 不会影响现有数据

### 第二步：更新App Engine配置

1. **检查 `app.yaml`**，确保包含打印配置：
```yaml
runtime: python39

env_variables:
  # 现有配置...
  CENTRALIZED_PRINTING_ENABLED: "true"
  
# 现有配置保持不变...
automatic_scaling:
  min_instances: 1
  max_instances: 10

handlers:
  - url: /.*
    script: auto
```

2. **如果需要，更新 `requirements.txt`**：
```txt
# 现有依赖保持不变
# 打印系统不需要额外的Python依赖
```

### 第三步：部署更新

1. **部署到App Engine**：
```bash
gcloud app deploy
```

2. **验证部署**：
```bash
# 检查应用状态
gcloud app browse

# 检查日志
gcloud app logs tail -s default
```

3. **测试打印API**：
```bash
# 检查打印服务状态
curl https://ambient-decoder-467517-h8.nn.r.appspot.com/api/print/status

# 应该返回类似：
# {
#   "available": true,
#   "online_servers": 0,
#   "pending_jobs": 0,
#   ...
# }
```

## 🖨️ 用户功能验证

### 测试用户界面

1. **访问应用**：https://ambient-decoder-467517-h8.nn.r.appspot.com/

2. **创建小管测试**：
   - 进入 "Add CryoVial(s)" 页面
   - 填写批次信息
   - 提交表单
   - 在确认页面应该看到 "Print vial labels after saving" 选项

3. **测试打印功能**：
   - 勾选打印选项并保存
   - 应该看到成功页面和打印模态框
   - Print Label模态框应该显示批次信息和小管列表

### 检查管理界面

1. **访问管理页面**：https://ambient-decoder-467517-h8.nn.r.appspot.com/admin

2. **查看新的表**：
   - 应该能看到 "Print Jobs" 和 "Print Servers" 
   - 可以查看已创建的打印任务

## 🖥️ 可选：设置打印服务器

如果需要自动打印功能，可以设置打印服务器：

### 在本地Windows机器上设置

1. **准备Windows环境**：
   - 安装Node.js 14+
   - 安装DYMO Label Software
   - 连接DYMO打印机

2. **配置打印服务器**：
```bash
cd dymo-print-server-nodejs
npm install
cp .env.example .env
```

3. **编辑 `.env`**：
```env
# 连接到Cloud部署
BACKEND_URL=https://ambient-decoder-467517-h8.nn.r.appspot.com
API_TOKEN=your-secure-token

# 服务器信息
SERVER_ID=biology-lab-printer-001
SERVER_NAME=Biology Lab Print Server
SERVER_LOCATION=Biology Lab - Room 101

# 打印机配置
PRINTER_NAME=DYMO LabelWriter 450
```

4. **启动打印服务器**：
```bash
npm start
```

### 验证打印服务器连接

1. **检查服务器状态**：
```bash
curl http://localhost:3001/api/status
```

2. **在Cloud应用中查看**：
   - 访问 https://ambient-decoder-467517-h8.nn.r.appspot.com/api/print/status
   - 应该显示 `"online_servers": 1`

## 📊 监控和维护

### 检查系统状态

1. **打印服务状态**：
```bash
curl https://ambient-decoder-467517-h8.nn.r.appspot.com/api/print/status
```

2. **打印统计**：
```bash
curl https://ambient-decoder-467517-h8.nn.r.appspot.com/api/print/stats
```

3. **应用日志**：
```bash
gcloud app logs tail -s default
```

### 数据库管理

1. **连接到Cloud SQL**：
```bash
gcloud sql connect your-instance-name --user=root
```

2. **查看打印任务**：
```sql
SELECT * FROM print_jobs ORDER BY created_at DESC LIMIT 10;
SELECT * FROM print_servers WHERE status = 'online';
```

### 清理旧数据（可选）

```sql
-- 删除30天前的已完成任务
DELETE FROM print_jobs 
WHERE status IN ('completed', 'failed') 
AND created_at < NOW() - INTERVAL 30 DAY;
```

## 🔧 故障排除

### 常见问题

#### 1. 数据库迁移失败
```
Error: Database connection failed
```

**解决方案**：
- 检查Google Cloud凭据：`gcloud auth list`
- 验证项目设置：`gcloud config get-value project`
- 确保Cloud SQL实例正在运行

#### 2. 部署后打印功能不可用
```
Print service not available
```

**解决方案**：
- 检查 `app.yaml` 中的 `CENTRALIZED_PRINTING_ENABLED: "true"`
- 查看应用日志：`gcloud app logs tail`
- 验证数据库表已创建

#### 3. 打印模态框不显示
**解决方案**：
- 清除浏览器缓存
- 检查浏览器控制台是否有JavaScript错误
- 确保模板文件已正确部署

#### 4. 打印服务器连接失败
```
Backend connection failed
```

**解决方案**：
- 检查 `BACKEND_URL` 设置
- 验证网络连接
- 确保API Token正确

### 回滚步骤

如果需要回滚更新：

1. **回滚App Engine部署**：
```bash
# 查看版本历史
gcloud app versions list

# 回滚到之前版本
gcloud app versions migrate PREVIOUS_VERSION
```

2. **删除数据库表**（谨慎操作）：
```sql
DROP TABLE IF EXISTS print_jobs;
DROP TABLE IF EXISTS print_servers;
```

## 📞 支持信息

### 检查清单

部署完成后，确认以下项目：

- [ ] 数据库迁移成功完成
- [ ] App Engine部署成功
- [ ] 打印API端点可访问
- [ ] 用户界面显示打印选项
- [ ] 管理界面显示打印表
- [ ] 打印服务器连接正常（如果使用）

### 验证命令

```bash
# 检查应用状态
curl https://ambient-decoder-467517-h8.nn.r.appspot.com/health

# 检查打印服务
curl https://ambient-decoder-467517-h8.nn.r.appspot.com/api/print/status

# 查看应用日志
gcloud app logs tail -s default

# 检查数据库连接
gcloud sql instances list
```

---

更新完成后，您的Cell Storage应用将支持集中式标签打印功能，用户可以在创建小管时选择自动打印标签！