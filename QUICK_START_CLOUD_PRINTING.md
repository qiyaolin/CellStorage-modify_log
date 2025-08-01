# 🚀 快速开始：Google Cloud 集中式打印系统

为现有的 Cell Storage 应用 `https://ambient-decoder-467517-h8.nn.r.appspot.com/` 添加集中式标签打印功能。

## ⚡ 3分钟快速部署

### 1. 运行数据库迁移
```bash
# 在项目根目录执行
python cloud_migration_update.py
```
这会添加打印相关的数据库表到你的 Cloud SQL 实例。

### 2. 部署更新
```bash
# 自动化部署脚本
./deploy_printing_update.sh

# 或者手动部署
gcloud app deploy
```

### 3. 验证部署
```bash
# 运行验证脚本
python verify_printing_deployment.py
```

## ✅ 部署完成检查

- [ ] 访问 https://ambient-decoder-467517-h8.nn.r.appspot.com/ 
- [ ] 进入 "Add CryoVial(s)" 页面
- [ ] 确认页面显示 "Print vial labels after saving" 选项
- [ ] 测试创建小管并选择打印选项
- [ ] 查看打印模态框是否正确显示

## 🖨️ 用户使用流程

1. **创建小管**：进入 Add CryoVial(s) 页面，填写批次信息
2. **选择打印**：在确认页面勾选 "Print vial labels after saving"
3. **查看标签**：系统显示 Print Label 模态框，包含所有小管信息
4. **打印标签**：可选择打印所有标签或单个标签

## 🔧 可选：设置自动打印服务器

如果需要自动打印到物理打印机：

### Windows 环境设置
```bash
# 1. 安装依赖
cd dymo-print-server-nodejs
npm install

# 2. 配置连接
cp .env.example .env
# 编辑 .env，设置：
# BACKEND_URL=https://ambient-decoder-467517-h8.nn.r.appspot.com
# API_TOKEN=your-token

# 3. 启动服务器
npm start
```

### 打印机要求
- Windows 系统
- DYMO Label Software 已安装
- DYMO 打印机（如 LabelWriter 450）
- 建议标签：DYMO 30252 Address Labels

## 📊 监控和管理

### 检查系统状态
```bash
# 打印服务状态
curl https://ambient-decoder-467517-h8.nn.r.appspot.com/api/print/status

# 打印统计
curl https://ambient-decoder-467517-h8.nn.r.appspot.com/api/print/stats
```

### 管理界面
访问 `/admin` 查看：
- Print Jobs：所有打印任务
- Print Servers：注册的打印服务器

### 应用日志
```bash
gcloud app logs tail -s default
```

## 🔍 故障排除

### 问题：打印选项不显示
**解决**：检查 `app.yaml` 中是否设置了 `CENTRALIZED_PRINTING_ENABLED: "true"`

### 问题：API 返回 500 错误
**解决**：
1. 检查数据库迁移是否成功
2. 查看应用日志
3. 验证 Cloud SQL 连接

### 问题：打印模态框空白
**解决**：
1. 清除浏览器缓存
2. 检查浏览器控制台错误
3. 确认 JavaScript 文件正确加载

## 📞 技术支持

### 验证命令
```bash
# 应用健康检查
curl https://ambient-decoder-467517-h8.nn.r.appspot.com/

# 打印API检查
curl https://ambient-decoder-467517-h8.nn.r.appspot.com/api/print/status

# 完整验证
python verify_printing_deployment.py
```

### 回滚方法
如果需要回滚：
```bash
# 查看版本
gcloud app versions list

# 回滚到之前版本
gcloud app versions migrate PREVIOUS_VERSION

# 删除打印表（可选）
# 连接 Cloud SQL 后执行：
# DROP TABLE print_jobs, print_servers;
```

---

## 🎉 完成！

部署成功后，您的 Cell Storage 应用现在支持：
- ✅ 集中式标签打印
- ✅ 打印任务队列管理
- ✅ 实时打印状态跟踪
- ✅ 多服务器支持
- ✅ 管理界面监控

用户现在可以在创建小管时选择自动打印标签，每个小管都会有包含批次信息和位置的专用标签！