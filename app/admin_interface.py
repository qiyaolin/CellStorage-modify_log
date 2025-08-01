from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView, expose
from flask_admin.actions import action
from flask import flash, redirect, url_for
from flask_login import current_user
from sqlalchemy import text

class BaseModelView(ModelView):
    """Base ModelView with consistent access control"""
    page_size = 100  # 设置每页显示100条记录
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access admin panel', 'warning')
            return redirect(url_for('auth.login'))
        else:
            flash('Admin access required', 'error')
            return redirect(url_for('cell_storage.index'))

class CustomAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        
        # Debug info - remove this in production later
        from flask import current_app
        current_app.logger.info(f'Flask-Admin access check: user={current_user.username}, role={current_user.role}, is_admin={current_user.is_admin}')
        
        return current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        from flask import redirect, url_for, flash
        if not current_user.is_authenticated:
            flash('Please login to access admin panel', 'warning')
            return redirect(url_for('auth.login'))
        else:
            flash('Admin access required', 'error')
            return redirect(url_for('cell_storage.index'))
    
    @expose('/')
    def index(self):
        from app.cell_storage.models import User, CellLine, Tower, Drawer, Box, VialBatch, CryoVial
        
        # Calculate stats
        stats = {
            'users': User.query.count(),
            'vials': CryoVial.query.count(), 
            'available_vials': CryoVial.query.filter_by(status='Available').count(),
            'batches': VialBatch.query.count(),
            'cell_lines': CellLine.query.count(),
            'towers': Tower.query.count(),
            'drawers': Drawer.query.count(),
            'boxes': Box.query.count()
        }
        
        return self.render('admin/index.html', stats=stats)

class UserAdmin(BaseModelView):
    column_list = ['username', 'role', 'password_plain']
    column_searchable_list = ['username', 'role']
    column_filters = ['role']
    column_sortable_list = ['username', 'role']

class CellLineAdmin(BaseModelView):
    column_list = ['name', 'source', 'species', 'timestamp']
    column_searchable_list = ['name', 'source', 'species']
    column_filters = ['timestamp']
    column_sortable_list = ['name', 'source', 'timestamp']

class StorageBoxAdmin(BaseModelView):
    column_list = ['name', 'drawer_id', 'rows', 'columns']
    column_searchable_list = ['name']
    column_filters = ['drawer_id']
    column_sortable_list = ['name', 'drawer_id']

class VialBatchAdmin(BaseModelView):
    """修复PostgreSQL类型转换问题的VialBatchAdmin"""
    
    column_list = ['name', 'timestamp']
    column_searchable_list = ['name']
    column_filters = ['timestamp']
    column_sortable_list = ['name', 'timestamp']
    
    @action('delete', '删除', '确定要删除选中的记录吗？')
    def action_delete(self, ids):
        """自定义批量删除方法，修复PostgreSQL类型转换问题并处理外键约束"""
        try:
            # 将字符串ID转换为整数
            int_ids = [int(id_str) for id_str in ids]
            
            # 使用原生SQL查询避免类型转换问题
            query = text("SELECT * FROM vial_batches WHERE id = ANY(:ids)")
            result = self.session.execute(query, {'ids': int_ids})
            records = result.fetchall()
            
            if not records:
                flash('未找到要删除的记录', 'error')
                return redirect(url_for('.index_view'))
            
            # 先删除相关的 alerts 记录以避免外键约束
            delete_alerts_query = text("DELETE FROM alerts WHERE batch_id = ANY(:ids)")
            alerts_result = self.session.execute(delete_alerts_query, {'ids': int_ids})
            deleted_alerts_count = alerts_result.rowcount
            
            # 再删除相关的 cryovials 记录
            delete_vials_query = text("DELETE FROM cryovials WHERE batch_id = ANY(:ids)")
            vials_result = self.session.execute(delete_vials_query, {'ids': int_ids})
            deleted_vials_count = vials_result.rowcount
            
            # 最后删除 vial_batches 记录
            delete_query = text("DELETE FROM vial_batches WHERE id = ANY(:ids)")
            self.session.execute(delete_query, {'ids': int_ids})
            
            self.session.commit()
            
            flash(f'成功删除 {len(records)} 个批次记录（同时删除了 {deleted_alerts_count} 个相关告警和 {deleted_vials_count} 个相关冷冻管）', 'success')
            
        except Exception as e:
            self.session.rollback()
            flash(f'删除失败: {str(e)}', 'error')
        
        return redirect(url_for('.index_view'))

class CryoVialAdmin(BaseModelView):
    """CryoVial记录管理 - 以PostgreSQL主键ID为索引，支持删除操作"""
    
    # 以id主键为第一列显示
    column_list = ['id', 'unique_vial_id_tag', 'batch_id', 'box_id', 
                   'row_in_box', 'col_in_box', 'status', 'date_frozen', 'date_created']
    column_searchable_list = ['unique_vial_id_tag', 'notes']
    column_filters = ['status', 'date_frozen', 'batch_id', 'box_id']
    column_sortable_list = ['id', 'unique_vial_id_tag', 'date_frozen', 'date_created']
    column_labels = {
        'id': 'ID (主键)',
        'unique_vial_id_tag': 'Vial标签',
        'batch_id': '批次ID',
        'box_id': '盒子ID',
        'row_in_box': '行',
        'col_in_box': '列',
        'status': '状态',
        'date_frozen': '冷冻日期',
        'date_created': '创建时间'
    }
    
    # 默认按ID排序
    column_default_sort = 'id'
    
    # 禁用创建和编辑，只允许查看和删除
    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True
    
    @action('delete', '删除', '确定要删除选中的记录吗？')
    def action_delete(self, ids):
        """自定义批量删除方法，修复PostgreSQL类型转换问题"""
        try:
            # 将字符串ID转换为整数
            int_ids = [int(id_str) for id_str in ids]
            
            # 使用原生SQL查询避免类型转换问题
            query = text("SELECT * FROM cryovials WHERE id = ANY(:ids)")
            result = self.session.execute(query, {'ids': int_ids})
            records = result.fetchall()
            
            if not records:
                flash('未找到要删除的记录', 'error')
                return redirect(url_for('.index_view'))
            
            # 执行删除操作
            delete_query = text("DELETE FROM cryovials WHERE id = ANY(:ids)")
            self.session.execute(delete_query, {'ids': int_ids})
            self.session.commit()
            
            flash(f'成功删除 {len(records)} 条记录', 'success')
            
        except Exception as e:
            self.session.rollback()
            flash(f'删除失败: {str(e)}', 'error')
        
        return redirect(url_for('.index_view'))

class StorageLocationAdmin(BaseModelView):
    column_list = ['name', 'location_type', 'parent_id', 'is_active']
    column_searchable_list = ['name', 'location_type']
    column_filters = ['location_type', 'is_active']
    column_sortable_list = ['name', 'location_type']

class InventoryItemAdmin(BaseModelView):
    column_list = ['name', 'type_id', 'current_quantity', 'location_id', 'status', 'created_at']
    column_searchable_list = ['name', 'status']
    column_filters = ['type_id', 'status', 'created_at']
    column_sortable_list = ['name', 'current_quantity', 'created_at']


class AppConfigAdmin(BaseModelView):
    """应用配置管理，包括Batch ID和Vial ID计数器"""
    
    column_list = ['key', 'value', 'description', 'created_at', 'updated_at']
    column_searchable_list = ['key', 'value', 'description']
    column_filters = ['key', 'created_at']
    column_sortable_list = ['key', 'created_at', 'updated_at']
    column_labels = {
        'key': '配置键',
        'value': '配置值',
        'description': '描述',
        'created_at': '创建时间',
        'updated_at': '更新时间'
    }
    
    # 只允许编辑 value 和 description 字段
    form_columns = ['value', 'description']
    
    def on_model_change(self, form, model, is_created):
        """在模型更改时进行验证并同步数据库序列"""
        from app import db
        
        # 验证计数器值必须是正整数
        if model.key in ['batch_counter', 'vial_counter']:
            try:
                val = int(model.value)
                if val < 1:
                    raise ValueError(f"{model.key} must be a positive integer")
                model.value = str(val)
                
                # 同步 PostgreSQL 序列
                if model.key == 'vial_counter':
                    # 检查是否小于当前最大ID
                    from app.cell_storage.models import CryoVial
                    max_id = db.session.query(db.func.max(CryoVial.id)).scalar() or 0
                    if val <= max_id:
                        flash(f'警告：设置的 Vial ID ({val}) 小于或等于当前最大ID ({max_id})，可能导致ID冲突', 'warning')
                    
                    # 更新序列
                    db.session.execute(text(f"ALTER SEQUENCE cryovials_id_seq RESTART WITH {val}"))
                    flash(f'Vial ID 序列已更新为从 {val} 开始', 'info')
                    
                elif model.key == 'batch_counter':
                    # 检查是否小于当前最大ID
                    from app.cell_storage.models import VialBatch
                    max_id = db.session.query(db.func.max(VialBatch.id)).scalar() or 0
                    if val <= max_id:
                        flash(f'警告：设置的 Batch ID ({val}) 小于或等于当前最大ID ({max_id})，可能导致ID冲突', 'warning')
                    
                    # 更新序列
                    db.session.execute(text(f"ALTER SEQUENCE vial_batches_id_seq RESTART WITH {val}"))
                    flash(f'Batch ID 序列已更新为从 {val} 开始', 'info')
                    
            except ValueError as e:
                flash(f'Invalid value for {model.key}: {str(e)}', 'error')
                raise e
            except Exception as e:
                flash(f'更新序列时出错: {str(e)}', 'error')
                raise e
        
        # 更新时间戳
        from datetime import datetime
        model.updated_at = datetime.utcnow()
        
        super().on_model_change(form, model, is_created)

def init_admin(app):
    """初始化Flask-Admin"""
    from app import db
    
    # 创建Admin实例
    admin = Admin(
        app, 
        name='Cell Storage Admin',
        template_mode='bootstrap3',
        index_view=CustomAdminIndexView(name='首页', url='/flask-admin')
    )
    
    # 导入模型
    from app.cell_storage.models import User, CellLine, Box, VialBatch, CryoVial, Tower, Drawer, AppConfig
    from app.inventory.models import Location, InventoryItem, InventoryType, Supplier
    
    # 注册模型视图 - 按层级组织
    admin.add_view(UserAdmin(User, db.session, name='用户管理'))
    admin.add_view(CellLineAdmin(CellLine, db.session, name='细胞系管理'))
    
    # 存储层级管理
    admin.add_view(BaseModelView(Tower, db.session, name='塔管理'))
    admin.add_view(BaseModelView(Drawer, db.session, name='抽屉管理'))
    admin.add_view(StorageBoxAdmin(Box, db.session, name='存储盒管理'))
    
    # 样品管理
    admin.add_view(VialBatchAdmin(VialBatch, db.session, name='样品批次管理'))
    admin.add_view(CryoVialAdmin(CryoVial, db.session, name='冷冻管管理'))
    
    # 库存管理
    admin.add_view(StorageLocationAdmin(Location, db.session, name='存储位置管理'))
    admin.add_view(InventoryItemAdmin(InventoryItem, db.session, name='库存物品管理'))
    admin.add_view(BaseModelView(InventoryType, db.session, name='库存类型管理'))
    admin.add_view(BaseModelView(Supplier, db.session, name='供应商管理'))
    
    # 系统配置管理
    admin.add_view(AppConfigAdmin(AppConfig, db.session, name='系统配置管理'))
    
    return admin