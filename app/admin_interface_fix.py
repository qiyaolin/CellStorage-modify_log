# Flask-Admin PostgreSQL类型转换问题的系统性修复
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from flask import flash, redirect, url_for
from flask_login import current_user
from sqlalchemy import text

class VialBatchAdminFixed(ModelView):
    """修复PostgreSQL类型转换问题的VialBatchAdmin"""
    
    column_list = ['name', 'timestamp']
    column_searchable_list = ['name']
    column_filters = ['timestamp']
    column_sortable_list = ['name', 'timestamp']
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    @action('delete', '删除', '确定要删除选中的记录吗？')
    def action_delete(self, ids):
        """自定义批量删除方法，修复PostgreSQL类型转换问题"""
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
            
            # 执行删除操作
            delete_query = text("DELETE FROM vial_batches WHERE id = ANY(:ids)")
            self.session.execute(delete_query, {'ids': int_ids})
            self.session.commit()
            
            flash(f'成功删除 {len(records)} 条记录', 'success')
            
        except Exception as e:
            self.session.rollback()
            flash(f'删除失败: {str(e)}', 'error')
        
        return redirect(url_for('.index_view'))

class CryoVialAdminFixed(ModelView):
    """修复PostgreSQL类型转换问题的CryoVialAdmin"""
    
    column_list = ['unique_vial_id_tag', 'batch_id', 'cell_line_id', 'box_id', 
                   'row_in_box', 'col_in_box', 'passage_number', 'date_frozen', 
                   'status', 'notes']
    column_searchable_list = ['unique_vial_id_tag', 'notes']
    column_filters = ['status', 'date_frozen']
    column_sortable_list = ['unique_vial_id_tag', 'date_frozen', 'passage_number']
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
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