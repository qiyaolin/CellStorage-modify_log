#!/usr/bin/env python3
"""
Model Import Validation Script
系统性验证模型导入和Admin配置的完整性

Usage:
    python validate_models.py
"""

def validate_model_imports():
    """验证所有模型导入"""
    print("验证模型导入...")
    
    try:
        from app.cell_storage.models import (
            User, CellLine, Box, VialBatch, CryoVial, 
            Tower, Drawer, AuditLog, AppConfig, 
            AlertConfig, Alert, ThemeConfig
        )
        print("OK: cell_storage.models - 所有模型导入成功")
        
        from app.inventory.models import Location, InventoryItem
        print("OK: inventory.models - 所有模型导入成功")
        
        return True
    except ImportError as e:
        print(f"ERROR: 模型导入错误: {e}")
        return False

def validate_admin_imports():
    """验证Admin接口导入"""
    print("\n验证Admin接口导入...")
    
    try:
        from flask_admin import Admin, AdminIndexView, expose
        from flask_admin.contrib.sqla import ModelView
        from flask_admin.actions import action
        print("OK: Flask-Admin组件导入成功")
        
        from app.admin_interface import (
            CustomAdminIndexView, UserAdmin, CellLineAdmin, 
            StorageBoxAdmin, VialBatchAdmin, CryoVialAdmin,
            StorageLocationAdmin, InventoryItemAdmin
        )
        print("OK: Admin类导入成功")
        
        return True
    except ImportError as e:
        print(f"ERROR: Admin导入错误: {e}")
        return False

def validate_admin_configuration():
    """验证Admin配置完整性"""
    print("\n验证Admin配置...")
    
    try:
        from app import create_app
        app = create_app('development')
        
        with app.app_context():
            from app.admin_interface import init_admin
            admin = init_admin(app)
            
            print(f"OK: Admin配置成功 - {len(admin._views)} 个视图注册")
            
            # 列出所有注册的视图
            for view in admin._views:
                if hasattr(view, 'model'):
                    print(f"   - {view.name}: {view.model.__name__}")
                else:
                    print(f"   - {view.name}: 索引视图")
            
            return True
            
    except Exception as e:
        print(f"ERROR: Admin配置错误: {e}")
        return False

def validate_database_models():
    """验证数据库模型完整性"""
    print("\n验证数据库模型...")
    
    try:
        from app import create_app, db
        app = create_app('development')
        
        with app.app_context():
            # 检查表结构
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            expected_tables = [
                'users', 'cell_lines', 'towers', 'drawers', 'boxes',
                'vial_batches', 'cryovials', 'audit_logs', 'app_config',
                'alert_configs', 'alerts', 'theme_configs',
                'locations', 'inventory_items'
            ]
            
            missing_tables = [t for t in expected_tables if t not in tables]
            if missing_tables:
                print(f"WARNING: 缺失表: {missing_tables}")
            else:
                print(f"OK: 所有 {len(expected_tables)} 个表都存在")
            
            return len(missing_tables) == 0
            
    except Exception as e:
        print(f"ERROR: 数据库验证错误: {e}")
        return False

def main():
    """主验证流程"""
    print("开始系统性模型验证...\n")
    
    results = []
    
    # 执行所有验证
    results.append(validate_model_imports())
    results.append(validate_admin_imports())
    results.append(validate_admin_configuration())
    results.append(validate_database_models())
    
    # 总结结果
    print(f"\n验证结果: {sum(results)}/{len(results)} 通过")
    
    if all(results):
        print("SUCCESS: 所有验证通过！系统准备就绪。")
        return 0
    else:
        print("ERROR: 存在问题需要修复。")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())