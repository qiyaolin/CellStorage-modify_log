import os
from dotenv import load_dotenv
from google.cloud.sql.connector import Connector

# 加载 .env 文件中的环境变量 (如果存在)
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# 仅当在 GAE 环境中时才初始化 connector 和 getconn
if os.environ.get("INSTANCE_CONNECTION_NAME"):
    connector = Connector()
    
    def getconn():
        conn = connector.connect(
            os.environ["INSTANCE_CONNECTION_NAME"],
            "pg8000",
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASS"],
            db=os.environ["DB_NAME"]
        )
        return conn

class Config:
    # 密钥，非常重要，用于保护会话和CSRF令牌等。
    # 强烈建议从环境变量获取，或者至少是一个复杂且随机的字符串。
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-very-secret-and-hard-to-guess-key'  # 请务必修改这个默认值

    # 数据库配置
    # 优先从环境变量获取，用于连接Google Cloud SQL
    if os.environ.get("INSTANCE_CONNECTION_NAME"):
        SQLALCHEMY_DATABASE_URI = "postgresql+pg8000://"
        SQLALCHEMY_ENGINE_OPTIONS = {
            "creator": getconn,
            # 增加连接池配置，以适应无服务器环境
            "pool_size": 5,
            "max_overflow": 2,
            "pool_timeout": 30,
            "pool_recycle": 1800,
        }
    else:
        # 本地开发时回退到SQLite
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                                  'sqlite:///' + os.path.join(basedir, 'app.db')

    # SQLAlchemy 配置项，可以关闭一些不必要的通知，提升性能
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CSRF 保护配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # CSRF token 有效期 1 小时
    WTF_CSRF_HEADERS = ['X-CSRFToken', 'X-CSRF-Token']

    # Centralized Printing Configuration
    CENTRALIZED_PRINTING_ENABLED = os.environ.get('CENTRALIZED_PRINTING_ENABLED', 'False').lower() == 'true'
    PRINT_SERVER_URL = os.environ.get('PRINT_SERVER_URL', 'http://localhost:5001')
    PRINT_API_TOKEN = os.environ.get('PRINT_API_TOKEN', '')
    
    # 可以在这里添加其他应用配置...