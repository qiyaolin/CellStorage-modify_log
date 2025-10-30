# Bluehost快速部署指南

5步快速将Cell Storage Management System部署到Bluehost。

## 开始之前

### 1. 确认Bluehost服务类型

登录Bluehost cPanel，检查：
- [ ] 主机类型（共享/VPS/专用）
- [ ] Python支持（cPanel → Software → Select Python Version）
- [ ] SSH访问权限（cPanel → Advanced → SSH Access）
- [ ] 数据库类型（MySQL/PostgreSQL）

### 2. 选择部署路径

根据你的Bluehost服务类型：

| 服务类型 | 推荐方案 | 难度 | 文档 |
|---------|---------|------|------|
| VPS/专用服务器 | Nginx + Gunicorn | ⭐⭐ | [详细指南](BLUEHOST_DEPLOYMENT.md#vps部署方案) |
| 共享主机 | cPanel Python App | ⭐⭐⭐ | [详细指南](BLUEHOST_DEPLOYMENT.md#共享主机部署方案) |

---

## 方案A：VPS部署（推荐）

### 步骤1：准备服务器

```bash
# 1. SSH连接到服务器
ssh username@hayerlab.org

# 2. 运行自动部署脚本
wget https://raw.githubusercontent.com/your-repo/deploy_bluehost.sh
chmod +x deploy_bluehost.sh
sudo ./deploy_bluehost.sh
```

选择选项 **1. 完整部署（首次安装）**

### 步骤2：配置数据库

部署脚本会自动创建数据库。如需手动配置：

```bash
# 创建PostgreSQL数据库
sudo -u postgres psql
CREATE DATABASE cell_storage;
CREATE USER cellstorage_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE cell_storage TO cellstorage_user;
\q
```

### 步骤3：导入数据（如从Google Cloud迁移）

参考 [数据库迁移指南](DATABASE_MIGRATION_GUIDE.md)

```bash
# 简化版本
psql -U cellstorage_user -d cell_storage < backup.sql
```

### 步骤4：配置环境变量

```bash
# 编辑.env文件
nano /var/www/cellstorage/.env

# 关键配置
SECRET_KEY=<生成强密钥>
DB_PASS=<数据库密码>
SERVER_NAME=hayerlab.org
```

### 步骤5：配置SSL和测试

```bash
# 配置SSL证书
sudo ./deploy_bluehost.sh
# 选择选项 5. 配置SSL证书

# 创建管理员用户
sudo ./deploy_bluehost.sh
# 选择选项 6. 创建管理员用户

# 测试访问
curl https://hayerlab.org/health
```

✅ **完成！** 访问 https://hayerlab.org

---

## 方案B：共享主机部署

### 步骤1：上传文件

```bash
# 方法1：使用FileZilla/WinSCP上传
# 目标目录：/home/username/public_html/

# 方法2：使用cPanel文件管理器
# 上传整个项目文件夹到public_html
```

### 步骤2：配置Python应用

1. 登录cPanel
2. 进入 **Setup Python App**
3. 创建应用：
   - Python版本：选择最新版本
   - 应用根目录：`public_html/cellstorage`
   - 应用URL：`hayerlab.org`
   - 应用启动文件：`passenger_wsgi.py`

### 步骤3：安装依赖

在cPanel的Python应用页面：

```bash
# 进入虚拟环境
source /home/username/virtualenv/cellstorage/3.9/bin/activate

# 安装依赖
cd /home/username/public_html/cellstorage
pip install -r requirements.txt
```

### 步骤4：配置数据库

1. cPanel → MySQL数据库
2. 创建数据库：`cell_storage`
3. 创建用户：`cellstorage_user`
4. 添加用户到数据库并授予所有权限

配置.env文件：
```bash
DB_USER=cellstorage_user
DB_PASS=<从cPanel获取的密码>
DB_NAME=username_cell_storage  # 注意cPanel会添加前缀
DB_HOST=localhost
```

### 步骤5：导入数据和测试

```bash
# 通过phpMyAdmin导入数据
# cPanel → phpMyAdmin → cell_storage → 导入

# 测试应用
curl http://hayerlab.org/health
```

✅ **完成！** 访问 http://hayerlab.org

---

## 常见问题快速解决

### 500 Internal Server Error
```bash
# 检查日志
tail -f /var/log/cellstorage/app.log  # VPS
# 或在cPanel中查看错误日志

# 常见原因：
# 1. .env文件配置错误
# 2. 数据库连接失败
# 3. Python依赖缺失
```

### 无法连接数据库
```bash
# 测试数据库连接
python3 << EOF
from config_bluehost import BluehostConfig
import pymysql

try:
    conn = pymysql.connect(
        host=BluehostConfig.DB_HOST,
        user=BluehostConfig.DB_USER,
        password=BluehostConfig.DB_PASS,
        database=BluehostConfig.DB_NAME
    )
    print("✓ 数据库连接成功")
    conn.close()
except Exception as e:
    print(f"✗ 连接失败: {e}")
EOF
```

### 静态文件404
```bash
# 检查静态文件路径
ls -la /var/www/cellstorage/app/static

# 检查Nginx配置（VPS）
sudo nginx -t
sudo systemctl restart nginx
```

### 打印功能不工作
```bash
# 禁用打印服务（临时解决）
# 编辑.env
CENTRALIZED_PRINTING_ENABLED=false
```

---

## 检查清单

### 部署前
- [ ] 备份Google Cloud数据
- [ ] 确认Bluehost服务类型
- [ ] 准备数据库导出文件
- [ ] 生成SECRET_KEY

### 部署中
- [ ] 上传所有文件
- [ ] 安装Python依赖
- [ ] 配置数据库
- [ ] 设置.env文件
- [ ] 导入数据

### 部署后
- [ ] 测试登录功能
- [ ] 验证数据完整性
- [ ] 配置SSL证书
- [ ] 设置自动备份
- [ ] 测试所有关键功能

---

## 需要帮助？

### 文档资源
- [完整部署指南](BLUEHOST_DEPLOYMENT.md) - 详细的部署步骤
- [数据库迁移指南](DATABASE_MIGRATION_GUIDE.md) - 数据迁移详解
- [项目概览](CLAUDE.md) - 项目架构和功能

### 故障排查
1. 检查日志文件
2. 验证配置文件
3. 测试数据库连接
4. 查看cPanel错误日志

### 下一步优化
- 配置CDN加速静态文件
- 设置监控和告警
- 配置自动备份
- 优化数据库性能
