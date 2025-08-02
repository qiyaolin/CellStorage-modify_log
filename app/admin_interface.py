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
        from app.cell_storage.models import User, CellLine, Tower, Drawer, Box, VialBatch, CryoVial, PrintJob, PrintServer
        
        # Calculate stats
        stats = {
            'users': User.query.count(),
            'vials': CryoVial.query.count(), 
            'available_vials': CryoVial.query.filter_by(status='Available').count(),
            'batches': VialBatch.query.count(),
            'cell_lines': CellLine.query.count(),
            'towers': Tower.query.count(),
            'drawers': Drawer.query.count(),
            'boxes': Box.query.count(),
            # 打印系统统计
            'print_jobs_total': PrintJob.query.count(),
            'print_jobs_pending': PrintJob.query.filter_by(status='pending').count(),
            'print_jobs_failed': PrintJob.query.filter_by(status='failed').count(),
            'print_servers_total': PrintServer.query.count(),
            'print_servers_online': PrintServer.query.filter_by(status='online').count()
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


class PrintJobAdmin(BaseModelView):
    """打印任务管理 - 支持查看、删除和状态修改"""
    
    column_list = ['id', 'label_data_preview', 'priority', 'status', 'requested_by', 
                   'created_at', 'started_at', 'completed_at', 'error_message', 'retry_count']
    column_searchable_list = ['label_data', 'error_message']
    column_filters = ['status', 'priority', 'created_at', 'requested_by']
    column_sortable_list = ['id', 'priority', 'status', 'created_at', 'retry_count']
    column_labels = {
        'id': '任务ID',
        'label_data_preview': '标签数据预览',
        'priority': '优先级',
        'status': '状态',
        'requested_by': '请求用户ID',
        'created_at': '创建时间',
        'started_at': '开始时间',
        'completed_at': '完成时间',
        'error_message': '错误消息',
        'retry_count': '重试次数'
    }
    
    # 默认按创建时间倒序排序，最新的在前面
    column_default_sort = ('created_at', True)
    
    # 允许删除，禁用创建，允许编辑状态相关字段
    can_create = False
    can_edit = True
    can_delete = True
    can_view_details = True
    
    # 只允许编辑状态相关字段
    form_columns = ['status', 'error_message', 'retry_count']
    
    def _label_data_preview(view, context, model, name):
        """显示标签数据的简短预览"""
        if model.label_data:
            # 尝试解析JSON并显示关键信息
            import json
            try:
                data = json.loads(model.label_data)
                if isinstance(data, dict):
                    # 提取关键字段进行预览
                    preview_parts = []
                    for key in ['batch_name', 'vial_id', 'cell_line', 'location']:
                        if key in data:
                            preview_parts.append(f"{key}: {data[key]}")
                    return " | ".join(preview_parts[:2]) if preview_parts else "JSON数据"
                return f"数据长度: {len(str(data))}"
            except:
                return f"数据长度: {len(model.label_data)}"
        return "无数据"
    
    column_formatters = {
        'label_data_preview': _label_data_preview
    }
    
    @action('reset_to_pending', '重置为待处理', '确定要将选中的任务重置为待处理状态吗？')
    def action_reset_to_pending(self, ids):
        """将选中的任务状态重置为待处理，用于重新处理失败的任务"""
        try:
            int_ids = [int(id_str) for id_str in ids]
            
            # 使用原生SQL更新状态
            update_query = text("""
                UPDATE print_jobs 
                SET status = 'pending', 
                    error_message = NULL, 
                    started_at = NULL, 
                    completed_at = NULL 
                WHERE id = ANY(:ids)
            """)
            result = self.session.execute(update_query, {'ids': int_ids})
            self.session.commit()
            
            flash(f'成功重置 {result.rowcount} 个打印任务为待处理状态', 'success')
            
        except Exception as e:
            self.session.rollback()
            flash(f'重置任务状态失败: {str(e)}', 'error')
        
        return redirect(url_for('.index_view'))
    
    @action('delete', '删除', '确定要删除选中的打印任务吗？')
    def action_delete(self, ids):
        """删除选中的打印任务"""
        try:
            int_ids = [int(id_str) for id_str in ids]
            
            # 先删除相关的历史记录
            delete_history_query = text("DELETE FROM print_job_history WHERE print_job_id = ANY(:ids)")
            history_result = self.session.execute(delete_history_query, {'ids': int_ids})
            
            # 再删除打印任务
            delete_query = text("DELETE FROM print_jobs WHERE id = ANY(:ids)")
            job_result = self.session.execute(delete_query, {'ids': int_ids})
            self.session.commit()
            
            flash(f'成功删除 {job_result.rowcount} 个打印任务（同时删除了 {history_result.rowcount} 条历史记录）', 'success')
            
        except Exception as e:
            self.session.rollback()
            flash(f'删除失败: {str(e)}', 'error')
        
        return redirect(url_for('.index_view'))

class PrintServerAdmin(BaseModelView):
    """打印服务器管理"""
    
    column_list = ['id', 'server_id', 'name', 'location', 'status', 'last_heartbeat', 
                   'total_jobs_processed', 'successful_jobs', 'failed_jobs', 'success_rate']
    column_searchable_list = ['server_id', 'name', 'location']
    column_filters = ['status', 'last_heartbeat']
    column_sortable_list = ['id', 'server_id', 'name', 'status', 'last_heartbeat', 'total_jobs_processed']
    column_labels = {
        'id': 'ID',
        'server_id': '服务器ID',
        'name': '服务器名称',
        'location': '位置',
        'status': '状态',
        'last_heartbeat': '最后心跳',
        'total_jobs_processed': '总处理任务数',
        'successful_jobs': '成功任务数',
        'failed_jobs': '失败任务数',
        'success_rate': '成功率'
    }
    
    # 默认按最后心跳时间倒序排序
    column_default_sort = ('last_heartbeat', True)
    
    # 允许编辑和删除
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    
    def _success_rate(view, context, model, name):
        """计算成功率"""
        if model.total_jobs_processed > 0:
            rate = (model.successful_jobs / model.total_jobs_processed) * 100
            return f"{rate:.1f}%"
        return "0%"
    
    column_formatters = {
        'success_rate': _success_rate
    }

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
    from app.cell_storage.models import User, CellLine, Box, VialBatch, CryoVial, Tower, Drawer, AppConfig, PrintJob, PrintServer
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
    
    # 打印系统管理
    admin.add_view(PrintJobAdmin(PrintJob, db.session, name='打印任务管理'))
    admin.add_view(PrintServerAdmin(PrintServer, db.session, name='打印服务器管理'))
    
    # 库存管理
    admin.add_view(StorageLocationAdmin(Location, db.session, name='存储位置管理'))
    admin.add_view(InventoryItemAdmin(InventoryItem, db.session, name='库存物品管理'))
    admin.add_view(BaseModelView(InventoryType, db.session, name='库存类型管理'))
    admin.add_view(BaseModelView(Supplier, db.session, name='供应商管理'))
    
    # 系统配置管理
    admin.add_view(AppConfigAdmin(AppConfig, db.session, name='系统配置管理'))
    
    return admin