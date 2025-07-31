import os
from app import create_app, db
from app.cell_storage.models import User

# 应用将从 GAE 的运行环境中自动获取环境变量
app = create_app()

def get_all_users():
    """
    查询并打印所有用户的用户名和明文密码。
    """
    with app.app_context():
        try:
            users = User.query.all()
            if not users:
                print("数据库中没有找到任何用户。")
                return

            print("系统中的用户列表：")
            print("-" * 40)
            print(f"{'用户名':<20} | {'密码 (明文)':<20}")
            print("-" * 40)
            for user in users:
                # 检查 password_plain 字段是否存在且有值
                password = user.password_plain if hasattr(user, 'password_plain') and user.password_plain else "N/A"
                print(f"{user.username:<20} | {password:<20}")
            print("-" * 40)

        except Exception as e:
            print(f"查询用户时发生错误: {e}")
            print("请确保您的数据库连接配置正确，并且数据库服务正在运行。")

if __name__ == '__main__':
    get_all_users()