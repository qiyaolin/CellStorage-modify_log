import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量 (如果存在)
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    # 密钥，非常重要，用于保护会话和CSRF令牌等。
    # 强烈建议从环境变量获取，或者至少是一个复杂且随机的字符串。
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-very-secret-and-hard-to-guess-key'  # 请务必修改这个默认值

    # 数据库配置
    # 对于 SQLite，是一个文件路径。
    # os.path.join(basedir, 'app.db') 会在项目根目录下创建一个 app.db 文件作为数据库。
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')

    # SQLAlchemy 配置项，可以关闭一些不必要的通知，提升性能
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CSRF 保护配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # CSRF token 有效期 1 小时
    WTF_CSRF_HEADERS = ['X-CSRFToken', 'X-CSRF-Token']

    # 可以在这里添加其他应用配置...