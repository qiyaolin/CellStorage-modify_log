"""
Passenger WSGI entry point for cPanel deployment
This file is required when deploying to Bluehost shared hosting via cPanel
"""
import sys
import os

# ==================== 虚拟环境配置 ====================
# 重要：修改为你的实际路径
# 示例：/home/username/virtualenv/cellstorage/3.9/bin/python3
INTERP = os.path.join(
    os.environ.get('HOME', '/home/username'),
    'virtualenv',
    'cellstorage',
    '3.9',  # Python版本，根据cPanel中选择的版本修改
    'bin',
    'python3'
)

# 如果当前Python解释器不是虚拟环境中的，则切换
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# ==================== 路径配置 ====================
# 应用根目录（当前文件所在目录）
cwd = os.getcwd()
sys.path.insert(0, cwd)

# 添加应用目录到Python路径
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# ==================== 环境变量加载 ====================
# 加载.env文件（如果存在）
try:
    from dotenv import load_dotenv
    env_path = os.path.join(app_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    # 如果没有python-dotenv，跳过
    pass

# 设置Bluehost部署标志
os.environ['BLUEHOST_DEPLOYMENT'] = 'true'
os.environ['FLASK_ENV'] = 'production'

# ==================== 日志配置 ====================
import logging
import sys

# 配置日志输出到stderr（cPanel可以捕获）
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# ==================== 应用初始化 ====================
try:
    # 导入Flask应用工厂
    from app import create_app

    # 创建应用实例
    from config_bluehost import get_config
    config = get_config()

    application = create_app(config)

    # 日志记录
    logging.info('Cell Storage application started successfully')
    logging.info(f'Application root: {app_dir}')
    logging.info(f'Python path: {sys.path}')

except Exception as e:
    # 详细的错误日志
    logging.error(f'Failed to start application: {str(e)}', exc_info=True)
    raise

# ==================== 健康检查端点 ====================
@application.route('/health')
def health_check():
    """健康检查端点"""
    return {
        'status': 'healthy',
        'python_version': sys.version,
        'app_dir': app_dir,
        'environment': os.environ.get('FLASK_ENV', 'unknown')
    }, 200

# ==================== 错误处理 ====================
@application.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logging.error(f'Internal Server Error: {error}', exc_info=True)
    return 'Internal Server Error', 500

@application.errorhandler(404)
def not_found_error(error):
    """404错误处理"""
    logging.warning(f'Page not found: {error}')
    return 'Page Not Found', 404

# ==================== 调试信息 ====================
if __name__ == '__main__':
    # 仅在直接运行时输出调试信息
    print("=" * 60)
    print("Cell Storage Management System - Passenger WSGI")
    print("=" * 60)
    print(f"Python Executable: {sys.executable}")
    print(f"Python Version: {sys.version}")
    print(f"Application Directory: {app_dir}")
    print(f"Current Working Directory: {cwd}")
    print(f"Python Path: {sys.path}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'unknown')}")
    print("=" * 60)

    # 测试应用是否可以创建
    try:
        test_app = application
        print("✓ Application created successfully")
        print(f"✓ Routes: {len(test_app.url_map._rules)} registered")
    except Exception as e:
        print(f"✗ Application creation failed: {e}")
        import traceback
        traceback.print_exc()
