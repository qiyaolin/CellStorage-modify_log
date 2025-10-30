"""
Bluehost-specific configuration for Cell Storage Management System
"""
import os
from datetime import timedelta

class BluehostConfig:
    """Bluehost deployment configuration"""

    # ==================== 基础配置 ====================
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Flask配置
    DEBUG = False
    TESTING = False

    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True  # 仅在HTTPS下传输cookie
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ==================== 数据库配置 ====================
    # 环境变量
    DB_USER = os.environ.get('DB_USER', 'your_db_user')
    DB_PASS = os.environ.get('DB_PASS', 'your_db_password')
    DB_NAME = os.environ.get('DB_NAME', 'cell_storage')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')  # MySQL默认端口

    # 数据库URI - MySQL/MariaDB (Bluehost默认)
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'

    # 如果使用PostgreSQL (VPS环境)，取消下面的注释：
    # SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}'

    # SQLAlchemy配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # 生产环境禁用SQL日志
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,  # 自动检测断开的连接
        'max_overflow': 20,
        'connect_args': {
            'connect_timeout': 10,
        }
    }

    # ==================== 文件上传配置 ====================
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'uploads'
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 最大上传大小
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'txt'}

    # ==================== 打印服务配置 ====================
    CENTRALIZED_PRINTING_ENABLED = os.environ.get('CENTRALIZED_PRINTING_ENABLED', 'false').lower() == 'true'
    PRINT_SERVER_URL = os.environ.get('PRINT_SERVER_URL', 'http://localhost:5001')
    PRINT_API_TOKEN = os.environ.get('PRINT_API_TOKEN', 'your-secure-print-token')

    # 打印队列配置
    PRINT_QUEUE_CHECK_INTERVAL = 5  # 秒
    PRINT_JOB_TIMEOUT = 300  # 5分钟
    MAX_PRINT_RETRIES = 3

    # ==================== 安全配置 ====================
    # CSRF保护
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # 不设置CSRF令牌过期时间

    # CORS配置（如果需要跨域访问）
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else []

    # ==================== 日志配置 ====================
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', '/var/log/cellstorage/app.log')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    # ==================== 邮件配置 ====================
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@hayerlab.org')

    # ==================== 应用特定配置 ====================
    # 分页
    ITEMS_PER_PAGE = 20

    # 缓存配置
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = 300

    # 时区
    TIMEZONE = 'America/New_York'  # 根据实验室位置调整

    # ==================== 移动端配置 ====================
    MOBILE_USER_AGENTS = [
        'Mobile', 'Android', 'iPhone', 'iPad',
        'Windows Phone', 'webOS', 'BlackBerry'
    ]

    # ==================== Bluehost特定配置 ====================
    # 静态文件路径（Bluehost环境）
    STATIC_FOLDER = 'app/static'
    STATIC_URL_PATH = '/static'

    # 模板文件夹
    TEMPLATE_FOLDER = 'app/templates'

    # 应用根路径（用于cPanel部署）
    APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', '/')

    # 服务器名称
    SERVER_NAME = os.environ.get('SERVER_NAME', 'hayerlab.org')

    # 强制HTTPS
    PREFERRED_URL_SCHEME = 'https'

    # ==================== 性能优化 ====================
    # 压缩响应
    COMPRESS_MIMETYPES = [
        'text/html', 'text/css', 'text/xml', 'application/json',
        'application/javascript', 'text/javascript'
    ]
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500

    # ==================== 开发和调试 ====================
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保上传文件夹存在
        os.makedirs(BluehostConfig.UPLOAD_FOLDER, exist_ok=True)

        # 确保日志目录存在
        log_dir = os.path.dirname(BluehostConfig.LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)


class DevelopmentConfig(BluehostConfig):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False  # 开发环境可以使用HTTP


class ProductionConfig(BluehostConfig):
    """生产环境配置"""
    DEBUG = False
    TESTING = False

    # 生产环境必须设置的环境变量
    @classmethod
    def init_app(cls, app):
        BluehostConfig.init_app(app)

        # 确保关键配置已设置
        assert os.environ.get('SECRET_KEY'), 'SECRET_KEY must be set in production'
        assert os.environ.get('DB_PASS'), 'DB_PASS must be set in production'

        # 配置日志
        import logging
        from logging.handlers import RotatingFileHandler

        if not app.debug:
            # 文件日志
            file_handler = RotatingFileHandler(
                cls.LOG_FILE,
                maxBytes=cls.LOG_MAX_BYTES,
                backupCount=cls.LOG_BACKUP_COUNT
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(getattr(logging, cls.LOG_LEVEL))
            app.logger.addHandler(file_handler)

            app.logger.setLevel(getattr(logging, cls.LOG_LEVEL))
            app.logger.info('Cell Storage startup')


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}


def get_config():
    """获取当前环境配置"""
    env = os.environ.get('FLASK_ENV', 'production')
    return config.get(env, config['default'])
