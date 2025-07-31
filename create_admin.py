#!/usr/bin/env python3
"""
脚本功能：创建或重置管理员用户密码。

- 如果 'admin' 用户不存在，则创建该用户。
- 如果 'admin' 用户已存在，则强制重置其密码，确保密码哈希值与明文密码同步。
"""

import os
from app import create_app, db
from app.cell_storage.models import User

def setup_admin_user():
    # 为了能在 Cloud Shell 或类似环境中运行，需要手动设置环境变量
    if os.environ.get("GAE_ENV", "").startswith("standard"):
        print("在 App Engine 环境中运行，无需手动设置环境变量。")
    else:
        print("正在为本地或 Cloud Shell 环境设置数据库连接环境变量...")
        os.environ['INSTANCE_CONNECTION_NAME'] = "ambient-decoder-467517-h8:northamerica-northeast1:cell-storage-instance"
        os.environ['DB_USER'] = "postgres"
        os.environ['DB_PASS'] = "Lqy960311!"
        os.environ['DB_NAME'] = "postgres"

    app = create_app()
    with app.app_context():
        admin_user = User.query.filter_by(username='admin').first()
        
        new_password = '111111' # 您可以按需修改这个密码

        if admin_user:
            print(f"管理员用户 'admin' 已存在。正在强制重置密码...")
            admin_user.set_password(new_password)
            print("密码已重置。")
        else:
            print("管理员用户 'admin' 不存在。正在创建新用户...")
            admin_user = User(username='admin', role='admin')
            admin_user.set_password(new_password)
            db.session.add(admin_user)
            print("新用户已创建。")
        
        db.session.commit()
        
        print("\\n--- 操作完成 ---")
        print(f"用户名: {admin_user.username}")
        print(f"新密码 (明文): {new_password}")
        print(f"角色: {admin_user.role}")
        print("现在您应该可以使用此凭据登录了。")

if __name__ == '__main__':
    setup_admin_user()
