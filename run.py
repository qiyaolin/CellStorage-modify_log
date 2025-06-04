from app import create_app, db
from app.models import User, CellLine, Tower, Drawer, Box, CryoVial, AuditLog

application = create_app()
@application.shell_context_processor
def make_shell_context():
    return {'app': application, 'db': db, 'User': User, 'CellLine': CellLine,
            'Tower': Tower, 'Drawer': Drawer, 'Box': Box, 'CryoVial': CryoVial, 'AuditLog': AuditLog}

if __name__ == '__main__':
    application.run(debug=False)