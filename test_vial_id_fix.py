#!/usr/bin/env python3
"""
测试 Vial ID 修复功能的脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.shared.utils import get_vial_counter, set_vial_counter
from app.cell_storage.models import CryoVial

def test_vial_counter_functionality():
    """测试 vial counter 功能"""
    app = create_app()
    
    with app.app_context():
        print("=== Vial ID 修复功能测试 ===\n")
        
        # 1. 测试获取当前 vial counter
        print("1. 测试获取当前 vial counter:")
        try:
            current_counter = get_vial_counter()
            print(f"   当前 vial counter: {current_counter}")
        except Exception as e:
            print(f"   错误: {e}")
        
        # 2. 测试获取当前最大 vial ID
        print("\n2. 测试获取当前最大 vial ID:")
        try:
            max_id = db.session.query(db.func.max(CryoVial.id)).scalar() or 0
            print(f"   当前最大 vial ID: {max_id}")
        except Exception as e:
            print(f"   错误: {e}")
        
        # 3. 测试获取 PostgreSQL 序列当前值
        print("\n3. 测试获取 PostgreSQL 序列当前值:")
        try:
            result = db.session.execute("SELECT last_value FROM cryovials_id_seq").fetchone()
            sequence_value = result[0] if result else 0
            print(f"   序列当前值: {sequence_value}")
        except Exception as e:
            print(f"   错误: {e}")
        
        # 4. 测试设置 vial counter
        print("\n4. 测试设置 vial counter:")
        test_value = max(max_id + 10, current_counter + 10)  # 设置一个安全的值
        try:
            print(f"   设置 vial counter 为: {test_value}")
            set_vial_counter(test_value)
            
            # 验证设置是否成功
            new_counter = get_vial_counter()
            print(f"   设置后的 vial counter: {new_counter}")
            
            # 验证序列是否同步
            result = db.session.execute("SELECT last_value FROM cryovials_id_seq").fetchone()
            new_sequence_value = result[0] if result else 0
            print(f"   设置后的序列值: {new_sequence_value}")
            
            if new_counter == test_value and new_sequence_value >= test_value:
                print("   ✅ vial counter 设置成功，序列已同步")
            else:
                print("   ❌ vial counter 设置可能有问题")
                
        except Exception as e:
            print(f"   错误: {e}")
        
        # 5. 测试边界情况
        print("\n5. 测试边界情况:")
        try:
            print("   测试设置无效值 (0):")
            set_vial_counter(0)
            print("   ❌ 应该抛出错误但没有")
        except ValueError as e:
            print(f"   ✅ 正确捕获错误: {e}")
        except Exception as e:
            print(f"   ❌ 意外错误: {e}")
        
        print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_vial_counter_functionality()