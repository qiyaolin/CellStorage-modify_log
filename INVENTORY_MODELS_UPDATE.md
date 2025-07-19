# 库存管理系统模型更新说明

## 更新概述

本次更新为库存管理系统添加了多个新的数据模型和字段，以支持更完整的实验室库存管理功能。

## 新增模型

### 1. PurchaseRequest（采购请求）
- **用途**: 管理采购请求流程
- **主要字段**:
  - `user_id`: 请求用户
  - `item_name`: 物品名称
  - `quantity_requested`: 请求数量
  - `status`: 状态（草稿、已提交、已批准、已拒绝、已订购）
  - `priority`: 优先级
  - `justification`: 采购理由

### 2. ShoppingCart（购物车）
- **用途**: 用户购物车功能
- **主要字段**:
  - `user_id`: 用户ID
  - `item_name`: 物品名称
  - `quantity`: 数量
  - `estimated_price`: 预估价格
  - `notes`: 备注

### 3. SupplierContact（供应商联系人）
- **用途**: 管理供应商的多个联系人
- **主要字段**:
  - `supplier_id`: 供应商ID
  - `name`: 联系人姓名
  - `title`: 职位
  - `email`: 邮箱
  - `phone`: 电话
  - `is_primary`: 是否主要联系人
  - `is_technical_contact`: 是否技术联系人
  - `is_sales_contact`: 是否销售联系人

### 4. UserPermission（用户权限）
- **用途**: 细粒度权限管理
- **主要字段**:
  - `user_id`: 用户ID
  - `permission`: 权限名称
  - `granted_at`: 授权时间
  - `granted_by_user_id`: 授权人

### 5. SupplierRating（供应商评级）
- **用途**: 供应商服务质量评价
- **主要字段**:
  - `supplier_id`: 供应商ID
  - `delivery_rating`: 交付评级
  - `quality_rating`: 质量评级
  - `service_rating`: 服务评级
  - `overall_rating`: 综合评级
  - `comments`: 评价意见

### 6. ItemPriceHistory（物品价格历史）
- **用途**: 跟踪物品价格变化
- **主要字段**:
  - `supplier_id`: 供应商ID
  - `catalog_number`: 目录号
  - `item_name`: 物品名称
  - `unit_price`: 单价
  - `effective_date`: 生效日期

## 现有模型增强

### InventoryItem（库存物品）
**新增字段**:
- `cas_number`: CAS编号（化学物质）
- `lot_number`: 批次号
- `safety_document_url`: 安全文档链接
- `responsible_person_id`: 负责人ID
- `storage_conditions`: 存储条件
- `qr_code`: 二维码

### Location（位置）
**新增字段**:
- `max_capacity`: 最大容量
- `capacity_unit`: 容量单位
- `current_usage`: 当前使用量

**新增属性**:
- `usage_percentage`: 使用百分比
- `is_full`: 是否已满
- `is_nearly_full`: 是否接近满容量
- `update_usage()`: 更新使用量方法

## 数据库迁移

### 自动迁移
运行迁移脚本：
```bash
python migrate_inventory_models.py
```

### 手动迁移（如果需要）
如果自动迁移失败，可能需要手动执行SQL：

```sql
-- 为 inventory_items 表添加新列
ALTER TABLE inventory_items ADD COLUMN cas_number VARCHAR(64);
ALTER TABLE inventory_items ADD COLUMN lot_number VARCHAR(64);
ALTER TABLE inventory_items ADD COLUMN safety_document_url VARCHAR(255);
ALTER TABLE inventory_items ADD COLUMN responsible_person_id INTEGER;
ALTER TABLE inventory_items ADD COLUMN storage_conditions VARCHAR(128);
ALTER TABLE inventory_items ADD COLUMN qr_code VARCHAR(255);

-- 为 locations 表添加新列
ALTER TABLE locations ADD COLUMN max_capacity INTEGER;
ALTER TABLE locations ADD COLUMN capacity_unit VARCHAR(32) DEFAULT 'items';
ALTER TABLE locations ADD COLUMN current_usage INTEGER DEFAULT 0;
```

## 功能特性

### 1. 容量管理
- 位置可以设置最大容量
- 自动计算使用百分比
- 容量不足时发出警告

### 2. 采购流程
- 用户提交采购请求
- 管理员审批流程
- 购物车功能

### 3. 供应商管理
- 多联系人支持
- 服务质量评价
- 价格历史跟踪

### 4. 权限控制
- 细粒度权限管理
- 用户权限分配
- 权限审计

### 5. 安全合规
- CAS编号支持
- 安全文档链接
- 批次号跟踪
- 存储条件记录

## 使用建议

1. **数据备份**: 迁移前请备份现有数据库
2. **测试环境**: 建议先在测试环境验证
3. **权限设置**: 根据实际需求配置用户权限
4. **容量规划**: 为位置设置合理的容量限制
5. **供应商信息**: 完善供应商联系人和评价体系

## 注意事项

- 新字段可能包含NULL值，请确保应用程序正确处理
- 权限系统需要与现有的认证系统集成
- 容量管理功能需要定期更新使用量数据
- 价格历史功能会增加数据库存储需求 