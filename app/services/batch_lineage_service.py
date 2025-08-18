"""
Batch Lineage Service - 管理batch家谱树和历史追溯功能
"""
from datetime import datetime
from flask import current_app
from ..cell_storage.models import VialBatch, CryoVial, CellLine
from .. import db


class BatchLineageService:
    """Batch家谱树服务类"""
    
    @staticmethod
    def get_batch_lineage(batch_id, max_depth=5):
        """
        获取指定batch的完整家谱树
        
        Args:
            batch_id (int): Batch ID
            max_depth (int): 最大深度，防止无限递归
            
        Returns:
            dict: 包含完整家谱信息的字典
        """
        batch = VialBatch.query.get_or_404(batch_id)
        return batch.get_lineage_tree(max_depth)
    
    @staticmethod
    def find_lineage_paths(batch_id):
        """
        查找从根节点到当前batch的所有路径
        
        Args:
            batch_id (int): Batch ID
            
        Returns:
            list: 所有可能的路径列表
        """
        batch = VialBatch.query.get_or_404(batch_id)
        paths = []
        
        def build_path_to_root(current_batch, current_path=[]):
            """递归构建到根节点的路径"""
            current_path = current_path + [current_batch]
            parents = current_batch.get_parent_batches()
            
            if not parents:
                # 到达根节点
                paths.append(current_path[::-1])  # 反转路径，从根到当前
            else:
                for parent in parents:
                    build_path_to_root(parent, current_path)
        
        build_path_to_root(batch)
        return paths
    
    @staticmethod
    def get_lineage_statistics(batch_id):
        """
        获取batch家谱的统计信息
        
        Args:
            batch_id (int): Batch ID
            
        Returns:
            dict: 统计信息
        """
        lineage = BatchLineageService.get_batch_lineage(batch_id)
        
        def count_nodes(tree_list):
            count = len(tree_list)
            for node in tree_list:
                if 'parents' in node:
                    count += count_nodes(node['parents'])
                if 'children' in node:
                    count += count_nodes(node['children'])
            return count
        
        ancestor_count = count_nodes(lineage['ancestors'])
        descendant_count = count_nodes(lineage['descendants'])
        
        # 计算最大深度
        def get_max_depth(tree_list, current_depth=0):
            if not tree_list:
                return current_depth
            max_d = current_depth
            for node in tree_list:
                if 'parents' in node:
                    max_d = max(max_d, get_max_depth(node['parents'], current_depth + 1))
                if 'children' in node:
                    max_d = max(max_d, get_max_depth(node['children'], current_depth + 1))
            return max_d
        
        max_ancestor_depth = get_max_depth(lineage['ancestors'])
        max_descendant_depth = get_max_depth(lineage['descendants'])
        
        return {
            'batch_id': batch_id,
            'has_lineage': lineage['has_lineage'],
            'ancestor_count': ancestor_count,
            'descendant_count': descendant_count,
            'total_related_batches': ancestor_count + descendant_count,
            'max_ancestor_depth': max_ancestor_depth,
            'max_descendant_depth': max_descendant_depth,
            'generation_span': max_ancestor_depth + max_descendant_depth + 1
        }
    
    @staticmethod
    def find_related_batches(batch_id, relationship_type='all'):
        """
        查找与指定batch相关的所有batch
        
        Args:
            batch_id (int): Batch ID
            relationship_type (str): 'parents', 'children', 'siblings', 'all'
            
        Returns:
            list: 相关batch列表
        """
        batch = VialBatch.query.get_or_404(batch_id)
        related = []
        
        if relationship_type in ['parents', 'all']:
            related.extend(batch.get_parent_batches())
        
        if relationship_type in ['children', 'all']:
            related.extend(batch.get_child_batches())
        
        if relationship_type in ['siblings', 'all']:
            # 查找兄弟节点（共享相同parent的batch）
            siblings = set()
            for parent in batch.get_parent_batches():
                for sibling in parent.get_child_batches():
                    if sibling.id != batch_id:
                        siblings.add(sibling)
            related.extend(list(siblings))
        
        # 去重并排序
        unique_related = list(set(related))
        unique_related.sort(key=lambda x: x.timestamp, reverse=True)
        
        return unique_related
    
    @staticmethod
    def suggest_parental_cell_lines(query='', limit=10):
        """
        为新batch建议可能的parental cell line
        
        Args:
            query (str): 搜索查询
            limit (int): 返回结果数量限制
            
        Returns:
            list: 建议的parental cell line列表
        """
        suggestions = []
        
        # 1. 从现有batch名称中搜索
        batch_names = db.session.query(VialBatch.name).filter(
            VialBatch.name.ilike(f'%{query}%')
        ).distinct().limit(limit).all()
        suggestions.extend([name[0] for name in batch_names])
        
        # 2. 从cell line名称中搜索
        cell_line_names = db.session.query(CellLine.name).filter(
            CellLine.name.ilike(f'%{query}%')
        ).distinct().limit(limit).all()
        suggestions.extend([name[0] for name in cell_line_names])
        
        # 3. 从现有parental_cell_line中搜索
        parental_names = db.session.query(CryoVial.parental_cell_line).filter(
            CryoVial.parental_cell_line.ilike(f'%{query}%'),
            CryoVial.parental_cell_line.isnot(None),
            CryoVial.parental_cell_line != ''
        ).distinct().limit(limit).all()
        suggestions.extend([name[0] for name in parental_names if name[0]])
        
        # 去重并排序
        unique_suggestions = list(set(suggestions))
        unique_suggestions.sort()
        
        return unique_suggestions[:limit]
    
    @staticmethod
    def validate_lineage_consistency(batch_id):
        """
        验证batch家谱的一致性
        
        Args:
            batch_id (int): Batch ID
            
        Returns:
            dict: 验证结果和问题报告
        """
        batch = VialBatch.query.get_or_404(batch_id)
        issues = []
        warnings = []
        
        # 检查是否存在循环引用
        def has_circular_reference(current_batch, visited=None, path=None):
            if visited is None:
                visited = set()
            if path is None:
                path = []
            
            if current_batch.id in visited:
                return True
            
            visited.add(current_batch.id)
            path.append(current_batch.id)
            
            try:
                for parent in current_batch.get_parent_batches():
                    if has_circular_reference(parent, visited, path):
                        return True
                return False
            finally:
                # 确保在递归返回时清理状态
                visited.remove(current_batch.id)
                path.pop()
        
        if has_circular_reference(batch):
            issues.append("Circular reference detected in lineage")
        
        # 检查parental_cell_line字段一致性
        if batch.parental_cell_line:
            parents = batch.get_parent_batches()
            if not parents:
                warnings.append(f"Parental cell line '{batch.parental_cell_line}' specified but no matching parent batch found")
        
        # 检查同一batch内vial的parental_cell_line一致性
        vial_parental_lines = set()
        for vial in batch.vials:
            if vial.parental_cell_line:
                vial_parental_lines.add(vial.parental_cell_line)
        
        if len(vial_parental_lines) > 1:
            warnings.append(f"Inconsistent parental_cell_line values within batch: {list(vial_parental_lines)}")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'summary': f"Validation completed with {len(issues)} issues and {len(warnings)} warnings"
        }