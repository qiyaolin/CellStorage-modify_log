# Model Import Validation Guide

## 模型导入依赖检查清单

### 🎯 问题识别
- ImportError: cannot import name 'X' from 'module'
- Worker boot failure due to missing models
- Flask-Admin view instantiation errors

### 🔍 系统性诊断步骤

1. **模型存在性验证**
   ```bash
   # 检查模型定义
   grep -n "class.*Model" app/*/models.py
   
   # 验证具体模型
   python -c "from app.cell_storage.models import ModelName; print('OK')"
   ```

2. **导入映射验证**
   ```python
   # 检查实际可用模型
   from app.cell_storage.models import *
   print([cls for cls in dir() if not cls.startswith('_')])
   ```

3. **Admin注册一致性**
   ```python
   # 确保Admin类与模型匹配
   - 导入语句与实际模型名称一致
   - Admin视图引用正确的模型类
   ```

### 🛡️ 预防措施

#### 1. 模型命名规范
- 使用一致的命名约定
- 避免重命名时的遗留引用
- 文档化模型结构变更

#### 2. 导入验证自动化
```python
# 添加到部署前检查
def validate_model_imports():
    try:
        from app.cell_storage.models import User, CellLine, Box, VialBatch, CryoVial, Tower, Drawer
        from app.inventory.models import StorageLocation, InventoryItem
        print("✅ All models imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
```

#### 3. Admin配置验证
```python
def validate_admin_config():
    """验证Admin配置与模型匹配"""
    from app import create_app
    app = create_app()
    with app.app_context():
        try:
            from app.admin_interface import init_admin
            admin = init_admin(app)
            print("✅ Admin configuration valid")
            return True
        except Exception as e:
            print(f"❌ Admin config error: {e}")
            return False
```

### 🚀 修复模板

#### 快速修复步骤
1. 识别缺失模型: `grep ImportError logs`
2. 检查实际模型: `cat app/*/models.py | grep "class.*Model"`
3. 更新导入语句: 修正模型名称映射
4. 验证Admin注册: 确保视图匹配模型
5. 测试部署: 本地验证后部署

#### 模型结构文档化
- 维护 MODEL_REFERENCE.md
- 记录模型重命名历史
- 更新文档时同步检查引用

### 📊 监控指标
- Worker启动成功率
- Import错误频率  
- Admin页面可访问性
- 模型注册完整性

### 🔧 工具集成
- Pre-commit hooks for import validation
- CI/CD pipeline model checks
- Development environment validation scripts