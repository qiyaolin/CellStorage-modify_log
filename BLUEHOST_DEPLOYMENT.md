# Bluehost 部署指南

本指南将帮助你将Cell Storage Management System从Google App Engine迁移到Bluehost托管服务。

## 目录
1. [前提条件](#前提条件)
2. [服务类型识别](#服务类型识别)
3. [部署方案选择](#部署方案选择)
4. [数据库迁移](#数据库迁移)
5. [应用部署](#应用部署)
6. [域名配置](#域名配置)
7. [常见问题](#常见问题)

## 前提条件

### 检查Bluehost服务类型
登录Bluehost控制面板（cPanel），查看：
- **主机类型**：Shared Hosting / VPS / Dedicated Server
- **Python支持**：cPanel → Software → Select Python Version
- **SSH访问**：cPanel → Advanced → SSH Access
- **数据库**：cPanel → Databases（通常是MySQL）

### 所需信息
- Bluehost SSH登录信息（如果可用）
- cPanel登录凭据
- 数据库访问信息
- 域名：hayerlab.org

## 服务类型识别

### 方案A：共享主机（Shared Hosting）
**适用条件**：
- ✅ 只有cPanel访问权限
- ✅ 不支持Python或仅支持基础Python
- ❌ 无SSH访问或受限SSH

**推荐方案**：
1. **转换为静态前端 + API后端**（推荐）
   - 前端部署到Bluehost
   - 后端部署到免费服务（Render.com / Railway.app / Fly.io）
   - 数据库使用免费PostgreSQL（ElephantSQL / Supabase）

2. **使用Bluehost的Python支持**（如果可用）
   - 通过cPanel的Python应用管理器
   - 限制较多，性能可能不佳

### 方案B：VPS主机（推荐）
**适用条件**：
- ✅ 有SSH root访问权限
- ✅ 可以安装软件包
- ✅ 可以配置Web服务器

**推荐方案**：
- 使用Nginx + Gunicorn部署Flask应用
- 安装PostgreSQL或使用MySQL
- 完全控制服务器环境

### 方案C：专用服务器
**适用条件**：
- ✅ 完整的服务器控制权
- ✅ 高性能需求
- ✅ 可以运行额外服务（打印服务器等）

**推荐方案**：
- 与VPS方案类似，但资源更充足
- 可以在同一服务器运行打印服务

## 数据库迁移

### 从Google Cloud SQL导出数据

```bash
# 1. 连接到Google Cloud SQL
gcloud sql connect [INSTANCE_NAME] --user=postgres

# 2. 导出数据
pg_dump -h [CLOUD_SQL_IP] -U postgres -d cell_storage > backup.sql

# 或使用Google Cloud Console导出功能
```

### 导入到Bluehost数据库

#### MySQL方案（Bluehost默认）
```bash
# 1. 在cPanel创建MySQL数据库
# 2. 创建数据库用户并授权
# 3. 导入数据（需要转换PostgreSQL到MySQL）

# 修改config.py使用MySQL
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@localhost/database_name'
```

#### PostgreSQL方案（VPS可用）
```bash
# SSH连接到Bluehost VPS
ssh username@hayerlab.org

# 安装PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# 创建数据库
sudo -u postgres createdb cell_storage

# 导入数据
psql -U postgres -d cell_storage < backup.sql
```

## 应用部署

### VPS部署方案（推荐）

#### 1. 服务器环境配置

```bash
# SSH连接
ssh username@hayerlab.org

# 更新系统
sudo apt-get update
sudo apt-get upgrade -y

# 安装Python和依赖
sudo apt-get install python3 python3-pip python3-venv nginx -y

# 安装PostgreSQL（或使用MySQL）
sudo apt-get install postgresql postgresql-contrib libpq-dev -y
```

#### 2. 部署应用

```bash
# 创建应用目录
mkdir -p /var/www/cellstorage
cd /var/www/cellstorage

# 上传代码（使用FTP/SFTP或git）
# 方法1：使用git
git clone your-repository-url .

# 方法2：使用SFTP上传文件
# 使用FileZilla或WinSCP上传整个项目文件夹

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env
```

#### 3. 配置Gunicorn

```bash
# 测试应用
gunicorn -b 0.0.0.0:8000 'app:create_app()'

# 创建systemd服务
sudo nano /etc/systemd/system/cellstorage.service
```

添加以下内容：
```ini
[Unit]
Description=Cell Storage Gunicorn Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/cellstorage
Environment="PATH=/var/www/cellstorage/venv/bin"
ExecStart=/var/www/cellstorage/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 'app:create_app()'

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl start cellstorage
sudo systemctl enable cellstorage
sudo systemctl status cellstorage
```

#### 4. 配置Nginx

```bash
sudo nano /etc/nginx/sites-available/hayerlab.org
```

添加以下内容：
```nginx
server {
    listen 80;
    server_name hayerlab.org www.hayerlab.org;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/cellstorage/app/static;
        expires 30d;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/hayerlab.org /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 5. 配置SSL证书（Let's Encrypt）

```bash
# 安装Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# 获取SSL证书
sudo certbot --nginx -d hayerlab.org -d www.hayerlab.org

# 自动续期
sudo certbot renew --dry-run
```

### 共享主机部署方案

#### 使用cPanel Python应用

1. 登录cPanel
2. 进入 "Setup Python App"
3. 创建新应用：
   - **Python版本**：选择最新版本
   - **应用根目录**：public_html/cellstorage
   - **应用URL**：hayerlab.org
   - **应用启动文件**：passenger_wsgi.py

4. 上传文件到应用目录

5. 创建 `passenger_wsgi.py`：
```python
import sys
import os

# 添加虚拟环境路径
INTERP = "/home/username/virtualenv/cellstorage/bin/python3"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# 添加应用路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
application = create_app()
```

#### 使用.htaccess配置

创建 `public_html/.htaccess`：
```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^(.*)$ passenger_wsgi.py/$1 [QSA,L]
```

## 域名配置

### 在Bluehost设置主域名

1. 登录Bluehost控制面板
2. 进入 "Domains" → "Assign"
3. 将hayerlab.org设置为主域名

### DNS配置（如果域名在其他地方注册）

如果域名在Bluehost注册，DNS会自动配置。如果在其他地方注册：

1. 获取Bluehost的Nameservers（通常在cPanel首页显示）
2. 在域名注册商处更新Nameservers：
   - ns1.bluehost.com
   - ns2.bluehost.com

或者使用A记录指向Bluehost服务器IP：
```
Type: A
Name: @
Value: [Bluehost服务器IP]
TTL: 14400

Type: A
Name: www
Value: [Bluehost服务器IP]
TTL: 14400
```

## 配置文件修改

### 1. 创建Bluehost配置文件

创建 `config_bluehost.py`：
```python
import os

class BluehostConfig:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'

    # 数据库配置（MySQL）
    DB_USER = os.environ.get('DB_USER', 'your_db_user')
    DB_PASS = os.environ.get('DB_PASS', 'your_db_password')
    DB_NAME = os.environ.get('DB_NAME', 'cell_storage')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 打印服务配置
    CENTRALIZED_PRINTING_ENABLED = os.environ.get('CENTRALIZED_PRINTING_ENABLED', 'false').lower() == 'true'
    PRINT_SERVER_URL = os.environ.get('PRINT_SERVER_URL', 'http://localhost:5001')

    # 上传文件夹
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
```

### 2. 修改 `run.py`

```python
import os
from app import create_app

# 根据环境选择配置
if os.environ.get('BLUEHOST_DEPLOYMENT'):
    from config_bluehost import BluehostConfig as Config
else:
    from config import Config

app = create_app(Config)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### 3. 创建 `.env` 文件

```bash
# 数据库配置
DB_USER=your_database_user
DB_PASS=your_database_password
DB_NAME=cell_storage
DB_HOST=localhost

# Flask配置
SECRET_KEY=generate-a-strong-secret-key
FLASK_ENV=production
BLUEHOST_DEPLOYMENT=true

# 打印服务
CENTRALIZED_PRINTING_ENABLED=true
PRINT_SERVER_URL=http://localhost:5001
PRINT_API_TOKEN=your-secure-print-token
```

## 打印服务器配置

### VPS环境
在同一台服务器上运行打印服务器：

```bash
# 创建打印服务目录
cd /var/www/cellstorage/dymo-print-server-nodejs/src

# 运行打印服务
nohup python3 production_print_agent.py &

# 或创建systemd服务
sudo nano /etc/systemd/system/printserver.service
```

### 共享主机环境
需要在本地计算机运行打印服务器，通过公网访问API：

1. 在本地运行打印服务器
2. 使用ngrok或类似工具暴露本地端口
3. 在Bluehost配置PRINT_SERVER_URL指向公网URL

## 测试部署

### 基本功能测试

```bash
# 1. 测试应用是否运行
curl http://hayerlab.org

# 2. 测试数据库连接
python3 check_website.py

# 3. 检查日志
tail -f /var/log/nginx/error.log
sudo journalctl -u cellstorage -f
```

### 性能测试

```bash
# 使用ab进行压力测试
ab -n 100 -c 10 http://hayerlab.org/
```

## 常见问题

### 1. Python版本不兼容
**问题**：Bluehost的Python版本太低
**解决**：
- VPS：使用pyenv安装最新Python
- 共享主机：在cPanel中选择可用的最高Python版本

### 2. 数据库连接失败
**问题**：无法连接到MySQL数据库
**解决**：
```bash
# 检查数据库权限
mysql -u root -p
GRANT ALL PRIVILEGES ON cell_storage.* TO 'username'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 502 Bad Gateway
**问题**：Nginx无法连接到Gunicorn
**解决**：
```bash
# 检查Gunicorn状态
sudo systemctl status cellstorage

# 检查端口占用
sudo netstat -tlnp | grep 8000
```

### 4. 静态文件404
**问题**：CSS/JS文件无法加载
**解决**：
- 检查Nginx static配置
- 确认文件路径正确
- 设置正确的文件权限：`chmod -R 755 app/static`

### 5. 打印功能不工作
**问题**：无法连接到打印服务器
**解决**：
- 检查PRINT_SERVER_URL配置
- 确认API token正确
- 在防火墙中开放打印服务端口

## 维护和监控

### 日志管理
```bash
# 应用日志
sudo journalctl -u cellstorage -n 100

# Nginx访问日志
tail -f /var/log/nginx/access.log

# Nginx错误日志
tail -f /var/log/nginx/error.log
```

### 备份策略
```bash
# 数据库备份
mysqldump -u username -p cell_storage > backup_$(date +%Y%m%d).sql

# 应用备份
tar -czf cellstorage_backup_$(date +%Y%m%d).tar.gz /var/www/cellstorage
```

### 更新应用
```bash
cd /var/www/cellstorage
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart cellstorage
```

## 下一步

1. ✅ 确认Bluehost服务类型
2. ✅ 选择合适的部署方案
3. ✅ 导出Google Cloud数据
4. ✅ 配置Bluehost环境
5. ✅ 部署应用
6. ✅ 配置域名
7. ✅ 测试所有功能
8. ✅ 设置监控和备份

## 需要帮助？

如果遇到问题，请提供：
- Bluehost服务类型
- 错误信息和日志
- cPanel截图（如适用）
