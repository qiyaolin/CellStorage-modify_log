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
    
    @staticmethod
    def get_optimized_lineage_for_frontend(batch_id, viewport_depth=3, include_details=True):
        """
        Get frontend-optimized lineage data with lazy loading support
        
        Args:
            batch_id (int): Batch ID
            viewport_depth (int): Maximum depth to load initially (default: 3)
            include_details (bool): Include detailed node information
            
        Returns:
            dict: Optimized lineage data structure for frontend rendering
        """
        batch = VialBatch.query.get_or_404(batch_id)
        
        def build_optimized_node(batch_obj, depth=0, node_type='current'):
            """Build optimized node data for frontend"""
            node_data = {
                'id': batch_obj.id,
                'name': batch_obj.name,
                'type': node_type,
                'depth': depth,
                'hasChildren': False,
                'hasParents': False,
                'canExpand': depth < viewport_depth
            }
            
            if include_details:
                node_data.update({
                    'cell_line': batch_obj.cell_line,
                    'passage_number': batch_obj.passage_number,
                    'date_frozen': batch_obj.date_frozen.isoformat() if batch_obj.date_frozen else None,
                    'parental_cell_line': batch_obj.parental_cell_line,
                    'vial_count': batch_obj.vials.count(),
                    'timestamp': batch_obj.timestamp.isoformat() if batch_obj.timestamp else None
                })
            
            return node_data
        
        def get_limited_ancestors(current_batch, max_depth, current_depth=0):
            """Get ancestors up to specified depth"""
            if current_depth >= max_depth:
                return []
            
            ancestors = []
            parents = current_batch.get_parent_batches()
            
            for parent in parents:
                ancestor_node = build_optimized_node(parent, current_depth + 1, 'ancestor')
                ancestor_node['hasParents'] = len(parent.get_parent_batches()) > 0
                ancestor_node['children'] = get_limited_ancestors(parent, max_depth, current_depth + 1)
                ancestors.append(ancestor_node)
            
            return ancestors
        
        def get_limited_descendants(current_batch, max_depth, current_depth=0):
            """Get descendants up to specified depth"""
            if current_depth >= max_depth:
                return []
            
            descendants = []
            children = current_batch.get_child_batches()
            
            for child in children:
                descendant_node = build_optimized_node(child, current_depth + 1, 'descendant')
                descendant_node['hasChildren'] = len(child.get_child_batches()) > 0
                descendant_node['children'] = get_limited_descendants(child, max_depth, current_depth + 1)
                descendants.append(descendant_node)
            
            return descendants
        
        # Build the optimized tree structure
        current_node = build_optimized_node(batch, 0, 'current')
        ancestors = get_limited_ancestors(batch, viewport_depth)
        descendants = get_limited_descendants(batch, viewport_depth)
        
        # Check if there are more nodes beyond the viewport
        total_ancestors = len(batch.get_parent_batches())
        total_descendants = len(batch.get_child_batches())
        
        return {
            'current': current_node,
            'ancestors': ancestors,
            'descendants': descendants,
            'metadata': {
                'viewport_depth': viewport_depth,
                'has_more_ancestors': total_ancestors > 0 and viewport_depth < 5,
                'has_more_descendants': total_descendants > 0 and viewport_depth < 5,
                'total_ancestor_count': total_ancestors,
                'total_descendant_count': total_descendants,
                'optimized_for_frontend': True
            }
        }
    
    @staticmethod
    def get_lineage_summary_stats(batch_id):
        """
        Get lightweight summary statistics for quick loading
        
        Args:
            batch_id (int): Batch ID
            
        Returns:
            dict: Summary statistics optimized for quick display
        """
        batch = VialBatch.query.get_or_404(batch_id)
        
        # Quick counts without deep traversal
        direct_parents = batch.get_parent_batches()
        direct_children = batch.get_child_batches()
        
        # Estimate total related batches (lightweight calculation)
        estimated_ancestors = len(direct_parents)
        estimated_descendants = len(direct_children)
        
        # Add one level deeper for better estimation
        for parent in direct_parents:
            estimated_ancestors += len(parent.get_parent_batches())
        
        for child in direct_children:
            estimated_descendants += len(child.get_child_batches())
        
        return {
            'batch_id': batch_id,
            'batch_name': batch.name,
            'has_lineage': len(direct_parents) > 0 or len(direct_children) > 0,
            'direct_parents': len(direct_parents),
            'direct_children': len(direct_children),
            'estimated_ancestors': estimated_ancestors,
            'estimated_descendants': estimated_descendants,
            'estimated_total_related': estimated_ancestors + estimated_descendants,
            'last_updated': datetime.now().isoformat(),
            'is_summary': True
        }
    
    @staticmethod
    def get_batch_nodes_by_depth(batch_id, depth_level, node_type='descendants', limit=50, offset=0):
        """
        Get batch nodes at specific depth level for lazy loading
        
        Args:
            batch_id (int): Root batch ID
            depth_level (int): Depth level to retrieve (1, 2, 3...)
            node_type (str): 'ancestors' or 'descendants'
            limit (int): Maximum number of nodes to return
            offset (int): Pagination offset
            
        Returns:
            dict: Paginated nodes at specified depth
        """
        batch = VialBatch.query.get_or_404(batch_id)
        nodes = []
        
        def traverse_to_depth(current_batch, target_depth, current_depth=0, visited=None):
            """Traverse to specific depth and collect nodes"""
            if visited is None:
                visited = set()
            
            if current_batch.id in visited:
                return []
            
            visited.add(current_batch.id)
            
            if current_depth == target_depth:
                return [current_batch]
            
            if current_depth >= target_depth:
                return []
            
            result_nodes = []
            
            if node_type == 'descendants':
                children = current_batch.get_child_batches()
                for child in children:
                    result_nodes.extend(traverse_to_depth(child, target_depth, current_depth + 1, visited))
            elif node_type == 'ancestors':
                parents = current_batch.get_parent_batches()
                for parent in parents:
                    result_nodes.extend(traverse_to_depth(parent, target_depth, current_depth + 1, visited))
            
            return result_nodes
        
        # Get nodes at the specified depth
        depth_nodes = traverse_to_depth(batch, depth_level)
        
        # Apply pagination
        total_count = len(depth_nodes)
        paginated_nodes = depth_nodes[offset:offset + limit]
        
        # Convert to JSON-friendly format
        for node_batch in paginated_nodes:
            nodes.append({
                'id': node_batch.id,
                'name': node_batch.name,
                'cell_line': node_batch.cell_line,
                'passage_number': node_batch.passage_number,
                'date_frozen': node_batch.date_frozen.isoformat() if node_batch.date_frozen else None,
                'parental_cell_line': node_batch.parental_cell_line,
                'vial_count': node_batch.vials.count(),
                'depth': depth_level,
                'has_children': len(node_batch.get_child_batches()) > 0,
                'has_parents': len(node_batch.get_parent_batches()) > 0
            })
        
        return {
            'nodes': nodes,
            'pagination': {
                'depth_level': depth_level,
                'limit': limit,
                'offset': offset,
                'total_count': total_count,
                'has_more': offset + limit < total_count,
                'next_offset': offset + limit if offset + limit < total_count else None
            },
            'metadata': {
                'node_type': node_type,
                'root_batch_id': batch_id
            }
        }