# 实验室库存管理系统详细规划方案

## 现状分析

### 已有基础架构 ✅
当前系统已具备以下核心模型：
- `InventoryItem` - 库存物品核心模型
- `Location` - 层级存储位置管理
- `Supplier` - 供应商管理
- `Order` & `OrderItem` - 订单管理
- `UsageLog` - 使用记录日志
- `StockAlert` - 库存预警
- `InventoryType` - 物品分类

### 系统优势
- ✅ 完整的数据模型设计
- ✅ 用户权限系统集成
- ✅ 层级位置管理支持
- ✅ 订单工作流支持
- ✅ 自动预警机制
- ✅ 自定义字段支持

---

## 七大模块详细实现方案

## 模块1: 库存管理模块 (Inventory Management) 
**优先级: P0 (核心模块)**

### 1.1 物品列表与查看

#### 数据库增强
```sql
-- 为InventoryItem表增加字段
ALTER TABLE inventory_items ADD COLUMN cas_number VARCHAR(64);
ALTER TABLE inventory_items ADD COLUMN lot_number VARCHAR(64);
ALTER TABLE inventory_items ADD COLUMN safety_document_url VARCHAR(255);
ALTER TABLE inventory_items ADD COLUMN responsible_person_id INTEGER REFERENCES users(id);
ALTER TABLE inventory_items ADD COLUMN storage_conditions VARCHAR(128);
ALTER TABLE inventory_items ADD COLUMN qr_code VARCHAR(255);

-- 添加全文搜索索引
CREATE INDEX idx_inventory_search ON inventory_items 
USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '') || ' ' || COALESCE(catalog_number, '') || ' ' || COALESCE(cas_number, '')));
```

#### 功能实现清单
- [x] **全局搜索**: 基于PostgreSQL全文搜索
- [x] **高级筛选**: 多条件组合筛选
- [x] **智能排序**: 可配置排序字段
- [x] **快速操作**: 行内编辑、删除、库存调整
- [x] **批量操作**: 批量编辑、批量导出
- [x] **视图切换**: 表格视图/卡片视图

#### 前端组件设计
```html
<!-- 搜索与筛选栏 -->
<div class="inventory-controls">
    <div class="search-bar">
        <input type="text" placeholder="搜索物品名称、编号、CAS号..." />
        <button class="advanced-filter-btn">高级筛选</button>
    </div>
    
    <!-- 高级筛选面板 -->
    <div class="advanced-filters collapse">
        <select name="location">位置筛选</select>
        <select name="supplier">供应商筛选</select>
        <select name="type">类型筛选</select>
        <select name="status">状态筛选</select>
        <input type="date" name="expiry_before" placeholder="到期日期前">
        <button class="apply-filters">应用筛选</button>
    </div>
</div>

<!-- 物品列表 -->
<div class="inventory-list">
    <!-- 表格视图 -->
    <table class="inventory-table sortable">
        <thead>
            <tr>
                <th data-sort="name">物品名称 ↕</th>
                <th data-sort="catalog_number">编号</th>
                <th data-sort="supplier">供应商</th>
                <th data-sort="current_quantity">当前数量</th>
                <th data-sort="location">位置</th>
                <th data-sort="expiration_date">到期日期</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
            <!-- 动态生成行 -->
        </tbody>
    </table>
</div>
```

### 1.2 物品详情页

#### 增强功能实现
- [ ] **详情展示**: 完整信息展示界面
- [ ] **快速编辑**: 内联编辑模式
- [ ] **库存调整**: 可视化+/-调整
- [ ] **QR码生成**: 自动生成带信息的QR码
- [ ] **操作历史**: 完整的变更记录
- [ ] **复制创建**: 基于现有物品快速创建

#### QR码集成设计
```python
# QR码生成服务
class QRCodeService:
    @staticmethod
    def generate_item_qr(item_id):
        item = InventoryItem.query.get(item_id)
        qr_data = {
            'id': item.id,
            'name': item.name,
            'location': item.location_info.full_path if item.location_info else '',
            'url': url_for('inventory.item_detail', id=item.id, _external=True)
        }
        return QRCodeGenerator.create_qr(json.dumps(qr_data))
```

### 1.3 核心功能增强

#### 智能预警系统
```python
# 预警规则引擎
class AlertEngine:
    @staticmethod
    def check_low_stock():
        """检查低库存预警"""
        low_stock_items = InventoryItem.query.filter(
            InventoryItem.current_quantity <= InventoryItem.minimum_quantity,
            InventoryItem.status == 'Available'
        ).all()
        
        for item in low_stock_items:
            AlertEngine.create_alert(
                alert_type='low_stock',
                severity='high' if item.current_quantity == 0 else 'medium',
                item_id=item.id,
                title=f'低库存预警: {item.name}',
                message=f'{item.name} 当前库存 {item.current_quantity} {item.unit}，低于最小库存 {item.minimum_quantity} {item.unit}'
            )
    
    @staticmethod
    def check_expiration():
        """检查到期预警"""
        # 7天内到期
        warning_date = date.today() + timedelta(days=7)
        expiring_items = InventoryItem.query.filter(
            InventoryItem.expiration_date <= warning_date,
            InventoryItem.expiration_date > date.today(),
            InventoryItem.status == 'Available'
        ).all()
        
        for item in expiring_items:
            days_until_expiry = (item.expiration_date - date.today()).days
            AlertEngine.create_alert(
                alert_type='expiring_soon',
                severity='medium',
                item_id=item.id,
                title=f'即将到期: {item.name}',
                message=f'{item.name} 将在 {days_until_expiry} 天后到期'
            )
```

---

## 模块2: 位置管理模块 (Location Management)
**优先级: P0 (基础模块)**

### 现状: ✅ 已有完整实现
- 层级位置模型已完成
- 树形结构支持
- 路径自动生成

### 增强功能
- [ ] **可视化位置树**: 交互式树形组件
- [ ] **位置容量管理**: 设置位置最大容量
- [ ] **位置利用率**: 实时统计位置使用情况
- [ ] **位置模板**: 快速创建标准位置结构

#### 位置容量管理
```sql
-- 为位置表增加容量字段
ALTER TABLE locations ADD COLUMN max_capacity INTEGER;
ALTER TABLE locations ADD COLUMN current_usage INTEGER DEFAULT 0;
ALTER TABLE locations ADD COLUMN capacity_unit VARCHAR(32); -- 'items', 'volume', 'weight'
```

```python
# 位置利用率计算
class LocationService:
    @staticmethod
    def calculate_usage(location_id):
        location = Location.query.get(location_id)
        if not location.max_capacity:
            return None
            
        current_items = InventoryItem.query.filter_by(location_id=location_id).count()
        usage_percentage = (current_items / location.max_capacity) * 100
        
        # 更新使用情况
        location.current_usage = current_items
        db.session.commit()
        
        return {
            'current': current_items,
            'maximum': location.max_capacity,
            'percentage': usage_percentage,
            'status': 'full' if usage_percentage >= 100 else 'warning' if usage_percentage >= 80 else 'normal'
        }
```

---

## 模块3: 采购与订单模块 (Procurement & Order)
**优先级: P1 (核心流程)**

### 3.1 购物车/申请列表

#### 数据库设计
```sql
-- 采购申请表
CREATE TABLE purchase_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    item_name VARCHAR(255) NOT NULL,
    catalog_number VARCHAR(128),
    supplier_id INTEGER REFERENCES suppliers(id),
    quantity_requested FLOAT NOT NULL,
    unit VARCHAR(32),
    justification TEXT,
    project_code VARCHAR(64),
    priority VARCHAR(16) DEFAULT 'Normal',
    status VARCHAR(32) DEFAULT 'Draft', -- Draft, Submitted, Approved, Rejected, Ordered
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by_user_id INTEGER REFERENCES users(id),
    review_notes TEXT
);

-- 购物车表 (临时存储)
CREATE TABLE shopping_cart (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    item_name VARCHAR(255) NOT NULL,
    catalog_number VARCHAR(128),
    supplier_id INTEGER REFERENCES suppliers(id),
    quantity FLOAT NOT NULL,
    estimated_price FLOAT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 工作流设计
```python
class PurchaseWorkflow:
    """采购工作流管理"""
    
    STATUSES = {
        'draft': '草稿',
        'submitted': '已提交',
        'under_review': '审核中', 
        'approved': '已批准',
        'rejected': '已拒绝',
        'ordered': '已订购',
        'received': '已收货'
    }
    
    @staticmethod
    def submit_request(user_id, items):
        """提交采购申请"""
        request = PurchaseRequest(
            user_id=user_id,
            status='submitted',
            submitted_at=datetime.utcnow()
        )
        
        # 发送通知给管理员
        NotificationService.notify_admins(
            title='新的采购申请',
            message=f'{user.username} 提交了采购申请',
            link=url_for('inventory.review_request', id=request.id)
        )
        
        return request
    
    @staticmethod 
    def approve_request(request_id, admin_id, notes=""):
        """批准采购申请"""
        request = PurchaseRequest.query.get(request_id)
        request.status = 'approved'
        request.reviewed_by_user_id = admin_id
        request.reviewed_at = datetime.utcnow()
        request.review_notes = notes
        
        # 可选: 自动创建订单
        OrderService.create_from_requests([request])
        
        return request
```

### 3.2 申请审批

#### 审批中心界面
```html
<!-- 审批中心 -->
<div class="approval-center">
    <div class="approval-filters">
        <select name="status">
            <option value="submitted">待审批</option>
            <option value="all">全部申请</option>
        </select>
        <select name="user">按申请人筛选</select>
        <select name="supplier">按供应商筛选</select>
    </div>
    
    <div class="approval-list">
        {% for request in pending_requests %}
        <div class="approval-card">
            <div class="request-header">
                <h3>申请人: {{ request.user.username }}</h3>
                <span class="priority-badge {{ request.priority.lower() }}">{{ request.priority }}</span>
            </div>
            
            <div class="request-items">
                <!-- 申请物品列表 -->
            </div>
            
            <div class="approval-actions">
                <button class="btn-approve" data-id="{{ request.id }}">批准</button>
                <button class="btn-reject" data-id="{{ request.id }}">拒绝</button>
                <button class="btn-edit" data-id="{{ request.id }}">修改</button>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
```

### 3.3 订单管理

#### 订单聚合功能
```python
class OrderService:
    @staticmethod
    def create_from_requests(approved_requests):
        """从批准的申请创建订单"""
        # 按供应商分组
        supplier_groups = {}
        for request in approved_requests:
            supplier_id = request.supplier_id or 'unknown'
            if supplier_id not in supplier_groups:
                supplier_groups[supplier_id] = []
            supplier_groups[supplier_id].append(request)
        
        created_orders = []
        for supplier_id, requests in supplier_groups.items():
            order = Order(
                order_number=OrderService.generate_order_number(),
                supplier_id=supplier_id if supplier_id != 'unknown' else None,
                status='Draft',
                requested_by_user_id=current_user.id
            )
            
            # 添加订单项
            for request in requests:
                order_item = OrderItem(
                    order=order,
                    item_name=request.item_name,
                    catalog_number=request.catalog_number,
                    quantity_requested=request.quantity_requested,
                    unit=request.unit
                )
                order.items.append(order_item)
            
            order.calculate_total()
            created_orders.append(order)
        
        return created_orders
    
    @staticmethod
    def receive_order(order_id, received_items):
        """订单收货处理"""
        order = Order.query.get(order_id)
        
        for item_data in received_items:
            # 创建或更新库存物品
            inventory_item = InventoryService.receive_item(
                name=item_data['name'],
                quantity=item_data['quantity_received'],
                location_id=item_data['location_id'],
                lot_number=item_data.get('lot_number'),
                expiration_date=item_data.get('expiration_date'),
                supplier_id=order.supplier_id
            )
            
            # 更新订单项状态
            order_item = OrderItem.query.get(item_data['order_item_id'])
            order_item.quantity_received = item_data['quantity_received']
            order_item.status = 'Received'
        
        # 检查订单是否完全收货
        if all(item.status == 'Received' for item in order.items):
            order.status = 'Completed'
            order.received_date = datetime.utcnow()
        
        return order
```

---

## 模块4: 用户与权限模块
**优先级: P0 (已实现基础)**

### 现状分析
- ✅ 基础用户系统已实现
- ✅ 角色权限系统已实现 
- ✅ 登录认证已实现

### 增强功能
- [ ] **细粒度权限**: 基于资源的权限控制
- [ ] **用户组管理**: 项目组/实验室组管理
- [ ] **操作审计**: 详细的用户操作日志

#### 细粒度权限设计
```python
# 权限装饰器增强
class PermissionManager:
    PERMISSIONS = {
        'inventory.view': '查看库存',
        'inventory.edit': '编辑库存',
        'inventory.delete': '删除库存',
        'orders.create': '创建订单',
        'orders.approve': '审批订单',
        'suppliers.manage': '管理供应商',
        'locations.manage': '管理位置',
        'users.manage': '管理用户',
        'system.admin': '系统管理'
    }
    
    @staticmethod
    def require_permission(permission):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not current_user.has_permission(permission):
                    flash('您没有执行此操作的权限', 'error')
                    return redirect(url_for('main.index'))
                return f(*args, **kwargs)
            return decorated_function
        return decorator

# 使用示例
@bp.route('/items/<int:id>/edit')
@login_required
@PermissionManager.require_permission('inventory.edit')
def edit_item(id):
    # 编辑物品逻辑
    pass
```

---

## 模块5: 供应商管理模块
**优先级: P1 (基础数据)**

### 现状: ✅ 基础模型已实现
- Supplier模型已完成
- 基本字段已包含

### 增强功能
- [ ] **供应商评级**: 服务质量评分系统
- [ ] **价格历史**: 物品价格变化追踪
- [ ] **供应商统计**: 采购金额、频次统计
- [ ] **供应商文档**: 合同、资质文档管理

#### 供应商评级系统
```sql
-- 供应商评级表
CREATE TABLE supplier_ratings (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    order_id INTEGER REFERENCES orders(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    delivery_rating INTEGER CHECK (delivery_rating >= 1 AND delivery_rating <= 5),
    quality_rating INTEGER CHECK (quality_rating >= 1 AND quality_rating <= 5),
    service_rating INTEGER CHECK (service_rating >= 1 AND service_rating <= 5),
    
    overall_rating FLOAT,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 价格历史表
CREATE TABLE item_price_history (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    catalog_number VARCHAR(128),
    item_name VARCHAR(255),
    unit_price FLOAT NOT NULL,
    currency VARCHAR(8) DEFAULT 'USD',
    effective_date DATE NOT NULL,
    order_id INTEGER REFERENCES orders(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

```python
class SupplierAnalytics:
    @staticmethod
    def calculate_supplier_score(supplier_id):
        """计算供应商综合评分"""
        ratings = SupplierRating.query.filter_by(supplier_id=supplier_id).all()
        
        if not ratings:
            return None
            
        total_ratings = len(ratings)
        avg_delivery = sum(r.delivery_rating for r in ratings) / total_ratings
        avg_quality = sum(r.quality_rating for r in ratings) / total_ratings  
        avg_service = sum(r.service_rating for r in ratings) / total_ratings
        
        # 加权平均 (质量40%, 交付30%, 服务30%)
        overall_score = (avg_quality * 0.4 + avg_delivery * 0.3 + avg_service * 0.3)
        
        return {
            'overall_score': round(overall_score, 2),
            'delivery_score': round(avg_delivery, 2),
            'quality_score': round(avg_quality, 2), 
            'service_score': round(avg_service, 2),
            'total_reviews': total_ratings
        }
    
    @staticmethod
    def get_price_trends(supplier_id, catalog_number):
        """获取价格趋势"""
        price_history = ItemPriceHistory.query.filter_by(
            supplier_id=supplier_id,
            catalog_number=catalog_number
        ).order_by(ItemPriceHistory.effective_date).all()
        
        return [{
            'date': p.effective_date.isoformat(),
            'price': p.unit_price,
            'currency': p.currency
        } for p in price_history]
```

---

## 模块6: 系统设置和数据模块
**优先级: P2 (管理功能)**

### 6.1 数据导入/导出

#### Excel/CSV 批量处理
```python
class DataImportService:
    @staticmethod
    def import_inventory_from_excel(file_path, user_id):
        """从Excel导入库存数据"""
        import pandas as pd
        
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 验证必需列
            required_columns = ['name', 'catalog_number', 'supplier', 'quantity', 'unit']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"缺少必需列: {missing_columns}")
            
            success_count = 0
            error_rows = []
            
            for index, row in df.iterrows():
                try:
                    # 查找或创建供应商
                    supplier = Supplier.query.filter_by(name=row['supplier']).first()
                    if not supplier:
                        supplier = Supplier(name=row['supplier'])
                        db.session.add(supplier)
                        db.session.flush()
                    
                    # 创建库存物品
                    item = InventoryItem(
                        name=row['name'],
                        catalog_number=row.get('catalog_number'),
                        supplier_id=supplier.id,
                        current_quantity=row['quantity'],
                        unit=row['unit'],
                        minimum_quantity=row.get('minimum_quantity', 0),
                        expiration_date=pd.to_datetime(row.get('expiration_date'), errors='coerce'),
                        created_by_user_id=user_id
                    )
                    
                    db.session.add(item)
                    success_count += 1
                    
                except Exception as e:
                    error_rows.append({'row': index + 2, 'error': str(e)})
            
            db.session.commit()
            
            return {
                'success': True,
                'imported_count': success_count,
                'error_count': len(error_rows),
                'errors': error_rows
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def export_inventory_to_excel():
        """导出库存数据到Excel"""
        import pandas as pd
        from io import BytesIO
        
        # 查询数据
        items = db.session.query(
            InventoryItem.name,
            InventoryItem.catalog_number,
            InventoryItem.current_quantity,
            InventoryItem.unit,
            InventoryItem.minimum_quantity,
            InventoryItem.expiration_date,
            Supplier.name.label('supplier_name'),
            Location.full_path.label('location_path')
        ).outerjoin(Supplier).outerjoin(Location).all()
        
        # 转换为DataFrame
        df = pd.DataFrame([{
            '物品名称': item.name,
            '产品编号': item.catalog_number,
            '当前数量': item.current_quantity,
            '单位': item.unit,
            '最小库存': item.minimum_quantity,
            '到期日期': item.expiration_date,
            '供应商': item.supplier_name,
            '存储位置': item.location_path
        } for item in items])
        
        # 生成Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='库存清单')
        
        output.seek(0)
        return output
```

### 6.2 自定义字段系统

#### 动态字段管理
```python
class CustomFieldManager:
    @staticmethod
    def add_custom_field(model_name, field_config):
        """为模型添加自定义字段"""
        # field_config = {
        #     'name': 'field_name',
        #     'label': '字段显示名',
        #     'type': 'text|number|date|select',
        #     'required': True/False,
        #     'options': ['option1', 'option2'] # for select type
        # }
        
        # 获取模型的自定义字段配置
        if model_name == 'inventory_item':
            model_class = InventoryType
        else:
            raise ValueError(f"不支持的模型: {model_name}")
        
        # 更新字段配置
        # 这里可以存储在数据库的JSON字段中
        pass
    
    @staticmethod
    def render_custom_fields(item, field_configs):
        """渲染自定义字段表单"""
        html = ""
        custom_data = item.get_custom_data()
        
        for field_config in field_configs:
            field_name = field_config['name']
            field_value = custom_data.get(field_name, '')
            
            if field_config['type'] == 'text':
                html += f"""
                <div class="form-group">
                    <label for="{field_name}">{field_config['label']}</label>
                    <input type="text" class="form-control" name="{field_name}" 
                           value="{field_value}" {'required' if field_config.get('required') else ''}>
                </div>
                """
            elif field_config['type'] == 'select':
                options_html = ""
                for option in field_config.get('options', []):
                    selected = 'selected' if option == field_value else ''
                    options_html += f'<option value="{option}" {selected}>{option}</option>'
                
                html += f"""
                <div class="form-group">
                    <label for="{field_name}">{field_config['label']}</label>
                    <select class="form-control" name="{field_name}" 
                            {'required' if field_config.get('required') else ''}>
                        <option value="">请选择...</option>
                        {options_html}
                    </select>
                </div>
                """
        
        return html
```

---

## 模块7: 报表与分析模块 (高级扩展)
**优先级: P3 (分析功能)**

### 数据分析设计

#### 消耗率分析
```python
class InventoryAnalytics:
    @staticmethod
    def calculate_consumption_rate(item_id, days=30):
        """计算物品消耗率"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 获取期间内的使用记录
        usage_logs = UsageLog.query.filter(
            UsageLog.item_id == item_id,
            UsageLog.timestamp >= start_date,
            UsageLog.quantity_change < 0  # 只看消耗记录
        ).all()
        
        total_consumed = sum(abs(log.quantity_change) for log in usage_logs)
        daily_rate = total_consumed / days if days > 0 else 0
        
        # 预测耗尽时间
        item = InventoryItem.query.get(item_id)
        days_until_empty = (item.current_quantity / daily_rate) if daily_rate > 0 else float('inf')
        
        return {
            'total_consumed': total_consumed,
            'daily_consumption_rate': daily_rate,
            'days_until_empty': days_until_empty,
            'analysis_period_days': days
        }
    
    @staticmethod
    def supplier_spending_analysis(start_date, end_date):
        """供应商支出分析"""
        orders = Order.query.filter(
            Order.ordered_date >= start_date,
            Order.ordered_date <= end_date,
            Order.status.in_(['Ordered', 'Received', 'Completed'])
        ).all()
        
        supplier_stats = {}
        
        for order in orders:
            supplier_name = order.supplier_info.name if order.supplier_info else '未知供应商'
            
            if supplier_name not in supplier_stats:
                supplier_stats[supplier_name] = {
                    'total_orders': 0,
                    'total_amount': 0,
                    'avg_order_value': 0,
                    'orders': []
                }
            
            supplier_stats[supplier_name]['total_orders'] += 1
            supplier_stats[supplier_name]['total_amount'] += order.total_cost or 0
            supplier_stats[supplier_name]['orders'].append({
                'order_number': order.order_number,
                'date': order.ordered_date.isoformat(),
                'amount': order.total_cost
            })
        
        # 计算平均订单金额
        for supplier, stats in supplier_stats.items():
            if stats['total_orders'] > 0:
                stats['avg_order_value'] = stats['total_amount'] / stats['total_orders']
        
        return supplier_stats
    
    @staticmethod
    def generate_inventory_report():
        """生成库存状态报表"""
        # 总体统计
        total_items = InventoryItem.query.count()
        available_items = InventoryItem.query.filter_by(status='Available').count()
        low_stock_items = InventoryItem.query.filter(
            InventoryItem.current_quantity <= InventoryItem.minimum_quantity
        ).count()
        expired_items = InventoryItem.query.filter(
            InventoryItem.expiration_date < date.today()
        ).count()
        
        # 按类型统计
        type_stats = db.session.query(
            InventoryType.name,
            func.count(InventoryItem.id).label('count'),
            func.sum(InventoryItem.current_quantity * InventoryItem.unit_price).label('total_value')
        ).join(InventoryItem).group_by(InventoryType.name).all()
        
        # 按位置统计
        location_stats = db.session.query(
            Location.name,
            func.count(InventoryItem.id).label('count')
        ).join(InventoryItem).group_by(Location.name).all()
        
        return {
            'summary': {
                'total_items': total_items,
                'available_items': available_items,
                'low_stock_items': low_stock_items,
                'expired_items': expired_items
            },
            'by_type': [{'type': t.name, 'count': t.count, 'value': t.total_value} for t in type_stats],
            'by_location': [{'location': l.name, 'count': l.count} for l in location_stats]
        }
```

#### 可视化图表
```html
<!-- 报表仪表板 -->
<div class="analytics-dashboard">
    <!-- 概览卡片 -->
    <div class="overview-cards">
        <div class="stat-card">
            <h3>总物品数</h3>
            <div class="stat-value">{{ summary.total_items }}</div>
        </div>
        <div class="stat-card warning">
            <h3>低库存预警</h3>
            <div class="stat-value">{{ summary.low_stock_items }}</div>
        </div>
        <div class="stat-card danger">
            <h3>已过期</h3>
            <div class="stat-value">{{ summary.expired_items }}</div>
        </div>
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-section">
        <div class="chart-container">
            <h4>按类型分布</h4>
            <canvas id="typeDistributionChart"></canvas>
        </div>
        
        <div class="chart-container">
            <h4>供应商支出排名</h4>
            <canvas id="supplierSpendingChart"></canvas>
        </div>
        
        <div class="chart-container">
            <h4>库存消耗趋势</h4>
            <canvas id="consumptionTrendChart"></canvas>
        </div>
    </div>
</div>

<script>
// 使用Chart.js绘制图表
function renderCharts(data) {
    // 类型分布饼图
    new Chart(document.getElementById('typeDistributionChart'), {
        type: 'pie',
        data: {
            labels: data.by_type.map(t => t.type),
            datasets: [{
                data: data.by_type.map(t => t.count),
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
            }]
        }
    });
    
    // 供应商支出柱状图
    new Chart(document.getElementById('supplierSpendingChart'), {
        type: 'bar',
        data: {
            labels: data.supplier_spending.map(s => s.supplier),
            datasets: [{
                label: '支出金额',
                data: data.supplier_spending.map(s => s.total_amount),
                backgroundColor: '#36A2EB'
            }]
        }
    });
}
</script>
```

---

## 实施路线图

### Phase 1: 核心功能强化 (2-3周)
**目标**: 完善现有核心功能
- [x] 模块1.1: 增强物品列表界面
- [x] 模块1.2: 完善物品详情页  
- [x] 模块2: 位置管理优化
- [x] 模块4: 权限系统完善

### Phase 2: 采购流程实现 (3-4周)
**目标**: 建立完整采购工作流
- [ ] 模块3.1: 购物车功能
- [ ] 模块3.2: 申请审批系统
- [ ] 模块3.3: 订单管理增强
- [ ] 通知系统集成

### Phase 3: 数据管理与分析 (2-3周)
**目标**: 数据导入导出与基础分析
- [ ] 模块6.1: 批量导入导出
- [ ] 模块6.2: 自定义字段
- [ ] 模块5: 供应商管理增强
- [ ] 基础报表功能

### Phase 4: 高级分析与优化 (3-4周)
**目标**: 智能分析与系统优化
- [ ] 模块7: 报表分析系统
- [ ] 预测性分析
- [ ] 系统性能优化
- [ ] 移动端适配

### Phase 5: 部署与培训 (1-2周)
**目标**: 生产环境部署
- [ ] 生产环境配置
- [ ] 数据迁移
- [ ] 用户培训
- [ ] 监控告警设置

---

## 技术架构建议

### 前端技术栈
- **基础框架**: 保持现有Flask + Jinja2
- **UI组件**: Bootstrap 5 + 自定义组件
- **交互增强**: Alpine.js (轻量级响应式)
- **图表库**: Chart.js / ECharts
- **表格组件**: DataTables.js (排序、搜索、分页)

### 后端优化
- **任务队列**: Celery + Redis (处理批量导入、报表生成)
- **缓存系统**: Redis (缓存统计数据、会话)
- **全文搜索**: PostgreSQL + 全文搜索索引
- **文件存储**: 本地存储 + 可选云存储

### 数据库优化
- **索引策略**: 为常用查询字段创建合适索引
- **分区策略**: 大表按时间分区 (usage_logs)
- **备份策略**: 定期自动备份 + 事务日志

### 部署建议
- **容器化**: Docker + Docker Compose
- **负载均衡**: Nginx反向代理
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack (Elasticsearch + Logstash + Kibana)

---

这个规划提供了完整的实验室库存管理系统实现路径，基于您现有的优秀基础架构，可以逐步扩展成为功能完备的实验室管理平台。每个模块都有详细的技术实现方案和数据库设计，可以按优先级逐步实施。