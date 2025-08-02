# Cell Storage 集中式打印功能设置指南

## 概述

Cell Storage项目已经成功集成了从Quartzy项目迁移的集中式打印功能，现在支持为每个vial打印包含Batch ID和Batch Name的标签。

## 已完成的集成

### ✅ 后端组件
- **打印数据模型**: `PrintJob`, `PrintServer`, `PrintJobHistory`
- **API端点**: `/api/print/*` 系列接口
- **打印服务层**: 任务队列管理和批量打印逻辑

### ✅ 前端组件  
- **打印模态框**: 完整的用户界面用于管理打印任务
- **工作流集成**: 在确认vial放置页面可选择打印
- **实时状态**: 显示打印进度和任务状态

### ✅ 打印服务器
- **Python打印代理**: 稳定的生产版本，已适配Flask API
- **自动轮询**: 从后端获取待打印任务
- **DYMO集成**: 支持DYMO标签打印机

## 使用方法

### 1. 用户工作流

1. **添加Vials**: 用户通过web界面添加vials
2. **确认放置**: 在确认页面查看计划的vial放置位置
3. **选择打印**: 勾选"Print vial labels after saving"
4. **保存并打印**: 系统保存vials并显示打印模态框
5. **监控进度**: 用户可以看到每个vial的打印状态

### 2. 标签内容

每个vial标签包含：
- **Batch Name**: 批次名称（如"HEK293-P5"）
- **Batch ID**: 批次ID（如"B123"）
- **Location**: 存储位置（如"Tower1/Drawer2/Box3"）
- **Position**: 网格位置（如"R1C1"）
- **Date**: 创建日期

### 3. 打印服务器设置

1. **安装依赖**:
   ```bash
   # 安装DYMO Label Framework
   # 安装Python 3.7+
   # 连接DYMO打印机
   ```

2. **配置服务器**:
   ```bash
   cd dymo-print-server-nodejs/src
   # 编辑 print_agent_config.json
   {
     "backend_url": "https://ambient-decoder-467517-h8.nn.r.appspot.com",
     "api_token": "zWCcDs_VmMWYVs6xWudyOZlRCwwC4Q-PAmKmrNpZ_kI"
   }
   ```

3. **启动服务**:
   ```bash
   # Windows
   start_print_agent.bat
   
   # 或手动启动
   python production_print_agent.py
   ```

## 配置说明

### 环境变量

在 `.env` 文件或系统环境中设置：

```env
CENTRALIZED_PRINTING_ENABLED=true
PRINT_API_TOKEN=zWCcDs_VmMWYVs6xWudyOZlRCwwC4Q-PAmKmrNpZ_kI
```

### 数据库迁移

如果需要设置数据库表：

```bash
python migrations/add_printing_tables.py migrate
```

## API端点

### 用户端点
- `GET /api/print/status` - 检查打印服务状态
- `POST /api/print/queue-job` - 队列单个打印任务
- `POST /api/print/queue-batch-labels` - 批量队列vial标签
- `GET /api/print/stats` - 获取打印统计

### 打印服务器端点
- `GET /api/print/fetch-pending-job` - 获取待处理任务
- `POST /api/print/update-job-status/{id}` - 更新任务状态
- `POST /api/print/heartbeat` - 服务器心跳
- `POST /api/print/register-server` - 注册服务器

## 测试方法

### 1. 前端测试
1. 访问Cell Storage web界面
2. 创建新的cell line和batch
3. 添加多个vials
4. 在确认页面选择打印选项
5. 验证打印模态框功能

### 2. API测试
```bash
# 检查打印服务状态
curl -X GET "https://your-backend.appspot.com/api/print/status"

# 队列测试打印任务
curl -X POST "https://your-backend.appspot.com/api/print/queue-job" \
  -H "Content-Type: application/json" \
  -d '{
    "label_data": {
      "batch_name": "Test-Batch",
      "batch_id": "B999",
      "vial_number": 1,
      "location": "Test/Location",
      "position": "R1C1",
      "date_created": "2024-08-02"
    },
    "priority": "normal"
  }'
```

### 3. 打印服务器测试
1. 启动打印代理: `python production_print_agent.py`
2. 检查日志文件: `print_agent.log`
3. 验证与后端的连接
4. 测试DYMO打印机功能

## 故障排除

### 常见问题

1. **打印服务不可用**
   - 检查`CENTRALIZED_PRINTING_ENABLED`配置
   - 验证API token是否正确
   - 确认打印服务器正在运行

2. **打印任务失败**
   - 检查DYMO Label Framework安装
   - 验证打印机连接
   - 查看`print_agent.log`日志

3. **API认证错误**
   - 确认API token匹配
   - 检查Bearer token格式
   - 验证网络连接

### 日志位置
- **后端日志**: Flask应用日志
- **打印服务器日志**: `dymo-print-server-nodejs/src/print_agent.log`
- **浏览器日志**: 开发者工具控制台

## 版本信息

- **迁移版本**: v1.0 - 从Quartzy项目完整迁移
- **适配内容**: 从item name/barcode改为Batch ID/Batch Name
- **技术栈**: Flask + Python + JavaScript + DYMO Framework
- **部署状态**: 生产就绪

## 支持

如有问题，请检查：
1. README.md - 基本使用说明
2. DEPLOYMENT_GUIDE.md - 详细部署指南  
3. print_agent.log - 错误日志
4. 后端API日志 - 服务端错误

集中式打印功能现已完全集成并可投入使用！