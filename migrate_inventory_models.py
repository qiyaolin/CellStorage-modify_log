#!/usr/bin/env python3
"""
数据库迁移脚本 - 库存管理系统模型更新
应用新的模型和字段到现有数据库
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.inventory.models import *
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    app = create_app()
    
    with app.app_context():
        print("开始数据库迁移...")
        
        # 创建所有新表
        print("创建新表...")
        db.create_all()
        
        # 检查是否需要添加新字段到现有表
        print("检查现有表结构...")
        
        # 检查 InventoryItem 表的新字段
        inspector = db.inspect(db.engine)
        existing_columns = [col['name'] for col in inspector.get_columns('inventory_items')]
        
        new_columns = [
            'cas_number', 'lot_number', 'safety_document_url', 
            'responsible_person_id', 'storage_conditions', 'qr_code'
        ]
        
        missing_columns = [col for col in new_columns if col not in existing_columns]
        
        if missing_columns:
            print(f"需要添加的列: {missing_columns}")
            print("注意: 需要手动执行 ALTER TABLE 语句来添加这些列")
            print("或者删除现有数据库文件重新创建")
        else:
            print("所有新列已存在")
        
        # 检查 Location 表的新字段
        location_columns = [col['name'] for col in inspector.get_columns('locations')]
        location_new_columns = ['max_capacity', 'capacity_unit', 'current_usage']
        missing_location_columns = [col for col in location_new_columns if col not in location_columns]
        
        if missing_location_columns:
            print(f"Location 表需要添加的列: {missing_location_columns}")
        
        print("迁移完成！")

def create_sample_data():
    """创建示例数据"""
    app = create_app()
    
    with app.app_context():
        print("创建示例数据...")
        
        # 创建库存类型
        types = [
            {'name': 'Chemical', 'description': '化学试剂', 'icon': 'flask'},
            {'name': 'Antibody', 'description': '抗体', 'icon': 'microscope'},
            {'name': 'Equipment', 'description': '设备', 'icon': 'cog'},
            {'name': 'Consumable', 'description': '耗材', 'icon': 'box'}
        ]
        
        for type_data in types:
            existing = InventoryType.query.filter_by(name=type_data['name']).first()
            if not existing:
                inventory_type = InventoryType(**type_data)
                db.session.add(inventory_type)
                print(f"创建库存类型: {type_data['name']}")
        
        # 创建位置
        locations = [
            {'name': '实验室A', 'location_type': 'room', 'temperature': 'RT'},
            {'name': '冰箱1', 'location_type': 'freezer', 'temperature': '-20°C'},
            {'name': '冷藏柜', 'location_type': 'refrigerator', 'temperature': '4°C'}
        ]
        
        for loc_data in locations:
            existing = Location.query.filter_by(name=loc_data['name']).first()
            if not existing:
                location = Location(**loc_data)
                db.session.add(location)
                print(f"创建位置: {loc_data['name']}")
        
        # 创建供应商
        suppliers = [
            {'name': 'Sigma-Aldrich', 'website': 'https://www.sigmaaldrich.com'},
            {'name': 'Thermo Fisher', 'website': 'https://www.thermofisher.com'},
            {'name': 'Bio-Rad', 'website': 'https://www.bio-rad.com'}
        ]
        
        for supp_data in suppliers:
            existing = Supplier.query.filter_by(name=supp_data['name']).first()
            if not existing:
                supplier = Supplier(**supp_data)
                db.session.add(supplier)
                print(f"创建供应商: {supp_data['name']}")
        
        try:
            db.session.commit()
            print("示例数据创建成功！")
        except Exception as e:
            db.session.rollback()
            print(f"创建示例数据时出错: {e}")

if __name__ == '__main__':
    print("库存管理系统数据库迁移工具")
    print("=" * 50)
    
    choice = input("选择操作:\n1. 执行迁移\n2. 创建示例数据\n3. 两者都执行\n请输入选择 (1/2/3): ")
    
    if choice == '1':
        migrate_database()
    elif choice == '2':
        create_sample_data()
    elif choice == '3':
        migrate_database()
        create_sample_data()
    else:
        print("无效选择") 