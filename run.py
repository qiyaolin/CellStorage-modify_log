from app import create_app, db # 从 app 包导入 create_app 函数和 db 实例
from app.models import User, CellLine, Tower, Drawer, Box, CryoVial, AuditLog # 导入所有模型

# 创建应用实例，使用默认的Config配置
application = create_app()

# 这个上下文处理器使得在Flask shell中可以直接使用app和db实例，以及所有模型
@application.shell_context_processor
def make_shell_context():
    return {'app': application, 'db': db, 'User': User, 'CellLine': CellLine,
            'Tower': Tower, 'Drawer': Drawer, 'Box': Box, 'CryoVial': CryoVial, 'AuditLog': AuditLog}

if __name__ == '__main__':
    # 启动开发服务器，开启调试模式
    application.run(debug=True)