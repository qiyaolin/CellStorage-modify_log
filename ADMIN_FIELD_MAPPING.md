# Admin Field Mapping Reference

## 字段配置修复记录

### User Model → UserAdmin
- **实际字段**: `username`, `role`, `password_plain`, `password_hash`
- **Admin配置**: `username`, `role`, `password_plain`
- **修复**: 移除不存在的 `email`, `is_admin`, `created_at`

### CellLine Model → CellLineAdmin  
- **实际字段**: `name`, `source`, `species`, `timestamp`, `notes`
- **Admin配置**: `name`, `source`, `species`, `timestamp`
- **修复**: 移除不存在的 `description`, `created_at`

### Box Model → StorageBoxAdmin
- **实际字段**: `name`, `drawer_id`, `rows`, `columns`, `description`
- **Admin配置**: `name`, `drawer_id`, `rows`, `columns`
- **修复**: 移除不存在的 `location`, `capacity`, `created_at`

### Location Model → StorageLocationAdmin
- **实际字段**: `name`, `location_type`, `parent_id`, `is_active`
- **Admin配置**: `name`, `location_type`, `parent_id`, `is_active`
- **修复**: 移除不存在的 `parent_location`, `created_at`

### InventoryItem Model → InventoryItemAdmin
- **实际字段**: `name`, `type_id`, `current_quantity`, `location_id`, `status`, `created_at`
- **Admin配置**: `name`, `type_id`, `current_quantity`, `location_id`, `status`, `created_at`
- **修复**: 移除不存在的 `category`, `quantity`, `location`

## 验证清单

### 字段存在性检查
```python
# 验证字段是否存在于模型中
def validate_admin_fields(model, admin_config):
    model_fields = [column.name for column in model.__table__.columns]
    missing_fields = [field for field in admin_config if field not in model_fields]
    return missing_fields
```

### 常见错误模式
1. 引用已删除的字段 (如 `email`)
2. 使用错误的字段名 (如 `parent_location` vs `parent_id`)
3. 引用计算属性而非数据库字段 (如 `is_admin`)
4. 使用不一致的时间戳字段名

### 预防措施
- 模型变更时同步更新Admin配置
- 使用验证脚本检查字段匹配
- 文档化字段映射关系