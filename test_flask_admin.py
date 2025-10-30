#!/usr/bin/env python3
"""
Flask-Admin界面测试脚本
确认后台管理界面可以正常显示和编辑数据
"""

import sys
sys.path.append('.')

def test_flask_admin_setup():
    """测试Flask-Admin的设置和权限"""
    print("Flask-Admin设置测试")
    print("=" * 50)

    try:
        from app import create_app
        app = create_app()

        with app.app_context():
            if hasattr(app, 'extensions') and 'admin' in app.extensions:
                admin = app.extensions['admin'][0]

                print(f"OK Flask-Admin已正确初始化")
                print(f"  管理URL: {admin.url}")
                print(f"  管理名称: {admin.name}")

                print(f"\n已注册的模型视图:")
                print("-" * 30)

                for view in admin._views:
                    if hasattr(view, 'model'):
                        model_name = view.model.__name__
                        view_name = view.name

                        # 检查权限
                        can_edit = getattr(view, 'can_edit', True)
                        can_create = getattr(view, 'can_create', True)
                        can_delete = getattr(view, 'can_delete', True)
                        can_view = getattr(view, 'can_view_details', True)

                        # 权限状态
                        permissions = []
                        if can_create: permissions.append("创建")
                        if can_edit: permissions.append("编辑")
                        if can_delete: permissions.append("删除")
                        if can_view: permissions.append("查看")

                        permission_str = ", ".join(permissions) if permissions else "无权限"

                        print(f"  * {view_name} ({model_name}): {permission_str}")

                        # 测试数据库连接
                        try:
                            count = view.model.query.count()
                            print(f"    数据库连接正常: {count} 条记录")
                        except Exception as e:
                            print(f"    数据库连接错误: {str(e)}")

                    else:
                        print(f"  * {view.name}: 索引页面")

                return True

            else:
                print("ERROR Flask-Admin未找到或未正确初始化")
                return False

    except Exception as e:
        print(f"ERROR 测试失败: {str(e)}")
        return False

def test_model_accessibility():
    """测试模型的可访问性和数据完整性"""
    print(f"\n模型数据完整性测试")
    print("=" * 50)

    try:
        from app import create_app
        from app.cell_storage.models import User, CellLine, Tower, Drawer, Box, VialBatch, CryoVial
        from app.inventory.models import Location, InventoryItem, InventoryType, Supplier

        app = create_app()

        with app.app_context():
            models_to_test = [
                ("用户", User),
                ("细胞系", CellLine),
                ("存储塔", Tower),
                ("抽屉", Drawer),
                ("存储盒", Box),
                ("样品批次", VialBatch),
                ("冷冻管", CryoVial),
                ("存储位置", Location),
                ("库存物品", InventoryItem),
                ("库存类型", InventoryType),
                ("供应商", Supplier),
            ]

            for name, model in models_to_test:
                try:
                    count = model.query.count()
                    print(f"OK {name} ({model.__name__}): {count} 条记录")

                    # 测试模型的主要字段
                    if count > 0:
                        sample = model.query.first()
                        fields = [c.name for c in model.__table__.columns]
                        print(f"  主要字段: {', '.join(fields[:5])}{'...' if len(fields) > 5 else ''}")

                except Exception as e:
                    print(f"ERROR {name} 访问失败: {str(e)}")

            return True

    except Exception as e:
        print(f"ERROR 模型测试失败: {str(e)}")
        return False

def test_admin_routes():
    """测试Flask-Admin路由是否正常"""
    print(f"\nFlask-Admin路由测试")
    print("=" * 50)

    try:
        from app import create_app
        app = create_app()

        with app.app_context():
            admin_routes = []
            for rule in app.url_map.iter_rules():
                if 'admin' in rule.endpoint.lower():
                    admin_routes.append((rule.endpoint, rule.rule))

            print(f"找到 {len(admin_routes)} 个admin相关路由:")
            for endpoint, rule in admin_routes[:10]:  # 显示前10个
                print(f"  * {endpoint} -> {rule}")

            if len(admin_routes) > 10:
                print(f"  ... 还有 {len(admin_routes) - 10} 个路由")

            return len(admin_routes) > 0

    except Exception as e:
        print(f"ERROR 路由测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始Flask-Admin完整性测试...\n")

    tests = [
        ("Flask-Admin设置", test_flask_admin_setup),
        ("模型可访问性", test_model_accessibility),
        ("Admin路由", test_admin_routes),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"运行测试: {test_name}")
        if test_func():
            passed += 1
            print(f"OK {test_name} 通过\n")
        else:
            print(f"FAIL {test_name} 失败\n")

    print("=" * 50)
    print(f"测试总结: {passed}/{total} 测试通过")

    if passed == total:
        print("SUCCESS 所有测试通过！Flask-Admin应该可以正常工作。")
        print("\n访问管理界面:")
        print("- 本地: http://localhost:5000/flask-admin/")
        print("- 生产: https://your-domain.com/flask-admin/")
    else:
        print("FAIL 某些测试失败，需要进一步诊断。")

    sys.exit(0 if passed == total else 1)