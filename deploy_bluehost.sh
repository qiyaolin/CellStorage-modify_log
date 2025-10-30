#!/bin/bash

###############################################################################
# Cell Storage Management System - Bluehost部署脚本
# 用于VPS环境的自动化部署
###############################################################################

set -e  # 遇到错误立即退出

# ==================== 配置变量 ====================
APP_NAME="cellstorage"
APP_DIR="/var/www/$APP_NAME"
VENV_DIR="$APP_DIR/venv"
GIT_REPO="https://github.com/yourusername/cellstorage.git"  # 修改为你的仓库地址
BRANCH="main"

# 数据库配置
DB_NAME="cell_storage"
DB_USER="cellstorage_user"

# 服务配置
SYSTEMD_SERVICE="cellstorage.service"
NGINX_SITE="hayerlab.org"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==================== 辅助函数 ====================
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root权限运行此脚本"
        exit 1
    fi
}

# ==================== 主要部署函数 ====================

install_dependencies() {
    log_info "安装系统依赖..."

    apt-get update
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        nginx \
        postgresql \
        postgresql-contrib \
        libpq-dev \
        build-essential \
        git \
        supervisor

    log_info "系统依赖安装完成"
}

setup_database() {
    log_info "配置PostgreSQL数据库..."

    # 检查数据库是否已存在
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
        log_warn "数据库 $DB_NAME 已存在，跳过创建"
    else
        # 创建数据库用户
        sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD 'changeme';"

        # 创建数据库
        sudo -u postgres createdb -O $DB_USER $DB_NAME

        log_info "数据库创建完成"
        log_warn "请记得修改数据库密码！"
    fi
}

setup_application() {
    log_info "配置应用..."

    # 创建应用目录
    mkdir -p $APP_DIR
    cd $APP_DIR

    # 克隆或更新代码
    if [ -d ".git" ]; then
        log_info "更新现有代码..."
        git pull origin $BRANCH
    else
        log_info "克隆代码仓库..."
        git clone -b $BRANCH $GIT_REPO .
    fi

    # 创建虚拟环境
    if [ ! -d "$VENV_DIR" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv $VENV_DIR
    fi

    # 激活虚拟环境并安装依赖
    source $VENV_DIR/bin/activate
    log_info "安装Python依赖..."
    pip install --upgrade pip
    pip install -r requirements.txt

    # 创建必要的目录
    mkdir -p uploads logs

    # 设置权限
    chown -R www-data:www-data $APP_DIR
    chmod -R 755 $APP_DIR

    log_info "应用配置完成"
}

setup_env_file() {
    log_info "配置环境变量..."

    if [ -f "$APP_DIR/.env" ]; then
        log_warn ".env文件已存在，跳过创建"
    else
        cat > $APP_DIR/.env << EOF
# Flask配置
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
FLASK_ENV=production
BLUEHOST_DEPLOYMENT=true

# 数据库配置
DB_USER=$DB_USER
DB_PASS=changeme
DB_NAME=$DB_NAME
DB_HOST=localhost

# 服务器配置
SERVER_NAME=hayerlab.org

# 打印服务配置
CENTRALIZED_PRINTING_ENABLED=false
PRINT_SERVER_URL=http://localhost:5001
PRINT_API_TOKEN=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/cellstorage/app.log
EOF

        chmod 600 $APP_DIR/.env
        chown www-data:www-data $APP_DIR/.env

        log_info ".env文件创建完成"
        log_warn "请编辑 $APP_DIR/.env 修改数据库密码等配置"
    fi
}

init_database() {
    log_info "初始化数据库..."

    cd $APP_DIR
    source $VENV_DIR/bin/activate

    # 运行数据库初始化脚本
    python3 << EOF
from app import create_app, db
from config_bluehost import get_config

app = create_app(get_config())
with app.app_context():
    db.create_all()
    print("数据库表创建完成")
EOF

    log_info "数据库初始化完成"
}

setup_systemd() {
    log_info "配置systemd服务..."

    cat > /etc/systemd/system/$SYSTEMD_SERVICE << EOF
[Unit]
Description=Cell Storage Gunicorn Application
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn -w 4 -b 127.0.0.1:8000 --timeout 120 --access-logfile /var/log/cellstorage/access.log --error-logfile /var/log/cellstorage/error.log 'app:create_app()'
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # 创建日志目录
    mkdir -p /var/log/cellstorage
    chown www-data:www-data /var/log/cellstorage

    # 重新加载systemd配置
    systemctl daemon-reload
    systemctl enable $SYSTEMD_SERVICE
    systemctl restart $SYSTEMD_SERVICE

    log_info "systemd服务配置完成"
}

setup_nginx() {
    log_info "配置Nginx..."

    cat > /etc/nginx/sites-available/$NGINX_SITE << 'EOF'
server {
    listen 80;
    server_name hayerlab.org www.hayerlab.org;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name hayerlab.org www.hayerlab.org;

    # SSL证书（Let's Encrypt）
    # ssl_certificate /etc/letsencrypt/live/hayerlab.org/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/hayerlab.org/privkey.pem;

    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 日志
    access_log /var/log/nginx/hayerlab.org_access.log;
    error_log /var/log/nginx/hayerlab.org_error.log;

    # 客户端上传大小限制
    client_max_body_size 16M;

    # 静态文件
    location /static {
        alias /var/www/cellstorage/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 主应用代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

    # 启用站点
    ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/

    # 测试Nginx配置
    nginx -t

    # 重启Nginx
    systemctl restart nginx

    log_info "Nginx配置完成"
}

setup_ssl() {
    log_info "配置SSL证书..."

    # 检查certbot是否已安装
    if ! command -v certbot &> /dev/null; then
        log_info "安装Certbot..."
        apt-get install -y certbot python3-certbot-nginx
    fi

    # 获取SSL证书
    log_info "获取Let's Encrypt证书..."
    certbot --nginx -d hayerlab.org -d www.hayerlab.org --non-interactive --agree-tos --email admin@hayerlab.org

    # 设置自动续期
    systemctl enable certbot.timer

    log_info "SSL证书配置完成"
}

create_admin_user() {
    log_info "创建管理员用户..."

    cd $APP_DIR
    source $VENV_DIR/bin/activate

    python3 create_admin.py

    log_info "管理员用户创建完成"
}

# ==================== 部署菜单 ====================
show_menu() {
    echo ""
    echo "=================================="
    echo " Cell Storage - Bluehost部署脚本"
    echo "=================================="
    echo "1. 完整部署（首次安装）"
    echo "2. 更新应用代码"
    echo "3. 重启服务"
    echo "4. 查看日志"
    echo "5. 配置SSL证书"
    echo "6. 创建管理员用户"
    echo "7. 备份数据库"
    echo "8. 退出"
    echo "=================================="
    echo -n "请选择操作 [1-8]: "
}

full_deployment() {
    log_info "开始完整部署..."

    check_root
    install_dependencies
    setup_database
    setup_application
    setup_env_file
    init_database
    setup_systemd
    setup_nginx

    log_info "部署完成！"
    log_warn "请完成以下步骤："
    echo "1. 编辑 $APP_DIR/.env 修改数据库密码和其他配置"
    echo "2. 运行: ./deploy_bluehost.sh 选择选项5配置SSL证书"
    echo "3. 运行: ./deploy_bluehost.sh 选择选项6创建管理员用户"
}

update_application() {
    log_info "更新应用..."

    cd $APP_DIR
    git pull origin $BRANCH

    source $VENV_DIR/bin/activate
    pip install -r requirements.txt

    systemctl restart $SYSTEMD_SERVICE

    log_info "应用更新完成"
}

restart_services() {
    log_info "重启服务..."

    systemctl restart $SYSTEMD_SERVICE
    systemctl restart nginx

    log_info "服务重启完成"
}

view_logs() {
    echo "选择日志类型："
    echo "1. 应用日志"
    echo "2. Nginx访问日志"
    echo "3. Nginx错误日志"
    echo "4. 系统日志"
    echo -n "请选择 [1-4]: "

    read log_choice

    case $log_choice in
        1)
            tail -f /var/log/cellstorage/app.log
            ;;
        2)
            tail -f /var/log/nginx/hayerlab.org_access.log
            ;;
        3)
            tail -f /var/log/nginx/hayerlab.org_error.log
            ;;
        4)
            journalctl -u $SYSTEMD_SERVICE -f
            ;;
        *)
            log_error "无效选择"
            ;;
    esac
}

backup_database() {
    log_info "备份数据库..."

    BACKUP_DIR="$APP_DIR/backups"
    mkdir -p $BACKUP_DIR

    BACKUP_FILE="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"

    sudo -u postgres pg_dump $DB_NAME > $BACKUP_FILE

    log_info "数据库备份完成: $BACKUP_FILE"
}

# ==================== 主程序 ====================
main() {
    while true; do
        show_menu
        read choice

        case $choice in
            1)
                full_deployment
                ;;
            2)
                update_application
                ;;
            3)
                restart_services
                ;;
            4)
                view_logs
                ;;
            5)
                setup_ssl
                ;;
            6)
                create_admin_user
                ;;
            7)
                backup_database
                ;;
            8)
                log_info "退出部署脚本"
                exit 0
                ;;
            *)
                log_error "无效选择，请重试"
                ;;
        esac

        echo ""
        echo -n "按Enter键继续..."
        read
    done
}

# 运行主程序
main
