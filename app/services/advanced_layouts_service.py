"""
Advanced Layouts Service - Additional visualization layouts for History Tree
Phase 4 Implementation - Force-directed, timeline, and custom layouts
"""
import json
import math
from datetime import datetime
from flask import current_app


class AdvancedLayoutsService:
    """
    Service providing advanced layout algorithms for lineage visualization
    Includes force-directed, timeline, circular, and custom layouts
    """
    
    @classmethod
    def generate_force_directed_layout(cls, lineage_data, width=800, height=600):
        """
        Generate force-directed layout coordinates for lineage data
        
        Args:
            lineage_data (dict): Lineage data from BatchLineageService
            width (int): Canvas width
            height (int): Canvas height
            
        Returns:
            dict: Layout data with node positions and physics parameters
        """
        try:
            nodes = []
            links = []
            
            # Process current node
            current = lineage_data.get('current')
            if current:
                nodes.append({
                    'id': current['id'],
                    'name': current['name'],
                    'type': 'current',
                    'x': width / 2,
                    'y': height / 2,
                    'fx': width / 2,  # Fixed position for current node
                    'fy': height / 2,
                    'cell_line': current.get('cell_line'),
                    'passage_number': current.get('passage_number'),
                    'date_frozen': current.get('date_frozen'),
                    'group': 1,
                    'size': 12
                })
            
            # Process ancestors
            ancestors = lineage_data.get('ancestors', [])
            for i, ancestor in enumerate(ancestors):
                nodes.append({
                    'id': ancestor['id'],
                    'name': ancestor['name'],
                    'type': 'ancestor',
                    'depth': ancestor.get('depth', i + 1),
                    'cell_line': ancestor.get('cell_line'),
                    'passage_number': ancestor.get('passage_number'),
                    'date_frozen': ancestor.get('date_frozen'),
                    'group': 2,
                    'size': 8
                })
                
                # Create links
                if current:
                    links.append({
                        'source': ancestor['id'],
                        'target': current['id'],
                        'type': 'parent-child',
                        'strength': 0.7
                    })
            
            # Process descendants
            descendants = lineage_data.get('descendants', [])
            for i, descendant in enumerate(descendants):
                nodes.append({
                    'id': descendant['id'],
                    'name': descendant['name'],
                    'type': 'descendant',
                    'depth': descendant.get('depth', i + 1),
                    'cell_line': descendant.get('cell_line'),
                    'passage_number': descendant.get('passage_number'),
                    'date_frozen': descendant.get('date_frozen'),
                    'group': 3,
                    'size': 8
                })
                
                # Create links
                if current:
                    links.append({
                        'source': current['id'],
                        'target': descendant['id'],
                        'type': 'parent-child',
                        'strength': 0.7
                    })
            
            # Calculate physics parameters
            physics_params = cls._calculate_force_physics(len(nodes), width, height)
            
            return {
                'type': 'force_directed',
                'nodes': nodes,
                'links': links,
                'physics': physics_params,
                'width': width,
                'height': height,
                'center': {'x': width / 2, 'y': height / 2}
            }
            
        except Exception as e:
            current_app.logger.error(f"Force-directed layout error: {e}")
            return cls._get_empty_layout('force_directed', width, height)
    
    @classmethod
    def generate_timeline_layout(cls, lineage_data, width=800, height=600):
        """
        Generate timeline layout based on creation dates
        
        Args:
            lineage_data (dict): Lineage data from BatchLineageService
            width (int): Canvas width
            height (int): Canvas height
            
        Returns:
            dict: Timeline layout data with chronological positioning
        """
        try:
            nodes = []
            timeline_events = []
            
            # Collect all nodes with dates
            all_nodes = []
            current = lineage_data.get('current')
            if current:
                all_nodes.append(current)
            
            all_nodes.extend(lineage_data.get('ancestors', []))
            all_nodes.extend(lineage_data.get('descendants', []))
            
            # Parse and sort by date
            dated_nodes = []
            for node in all_nodes:
                date_str = node.get('date_frozen') or node.get('created_date')
                if date_str:
                    try:
                        date_obj = cls._parse_date(date_str)
                        dated_nodes.append((date_obj, node))
                    except:
                        # If date parsing fails, put at end
                        dated_nodes.append((datetime.now(), node))
            
            dated_nodes.sort(key=lambda x: x[0])
            
            if not dated_nodes:
                return cls._get_empty_layout('timeline', width, height)
            
            # Calculate timeline positions
            min_date = dated_nodes[0][0]
            max_date = dated_nodes[-1][0]
            date_range = (max_date - min_date).total_seconds()
            
            margin = 50
            timeline_width = width - (2 * margin)
            
            for i, (date_obj, node) in enumerate(dated_nodes):
                # Calculate x position based on date
                if date_range > 0:
                    x_ratio = (date_obj - min_date).total_seconds() / date_range
                    x = margin + (x_ratio * timeline_width)
                else:
                    x = width / 2
                
                # Calculate y position based on node type
                if node.get('type') == 'current':
                    y = height / 2
                    size = 12
                    group = 1
                elif node['id'] in [a['id'] for a in lineage_data.get('ancestors', [])]:
                    y = height * 0.3  # Ancestors in upper third
                    size = 8
                    group = 2
                else:
                    y = height * 0.7  # Descendants in lower third
                    size = 8
                    group = 3
                
                nodes.append({
                    'id': node['id'],
                    'name': node['name'],
                    'type': node.get('type', 'unknown'),
                    'x': x,
                    'y': y,
                    'cell_line': node.get('cell_line'),
                    'passage_number': node.get('passage_number'),
                    'date_frozen': node.get('date_frozen'),
                    'date_obj': date_obj.isoformat(),
                    'group': group,
                    'size': size
                })
                
                timeline_events.append({
                    'date': date_obj.isoformat(),
                    'batch_name': node['name'],
                    'batch_id': node['id'],
                    'x': x,
                    'y': y
                })
            
            # Generate timeline axis
            timeline_axis = cls._generate_timeline_axis(min_date, max_date, margin, timeline_width)
            
            return {
                'type': 'timeline',
                'nodes': nodes,
                'timeline_events': timeline_events,
                'timeline_axis': timeline_axis,
                'date_range': {
                    'min': min_date.isoformat(),
                    'max': max_date.isoformat()
                },
                'width': width,
                'height': height
            }
            
        except Exception as e:
            current_app.logger.error(f"Timeline layout error: {e}")
            return cls._get_empty_layout('timeline', width, height)
    
    @classmethod
    def generate_circular_layout(cls, lineage_data, width=800, height=600):
        """
        Generate circular/radial layout with concentric rings
        
        Args:
            lineage_data (dict): Lineage data from BatchLineageService
            width (int): Canvas width
            height (int): Canvas height
            
        Returns:
            dict: Circular layout data with radial positioning
        """
        try:
            nodes = []
            center_x = width / 2
            center_y = height / 2
            max_radius = min(width, height) / 2 - 50
            
            # Current node at center
            current = lineage_data.get('current')
            if current:
                nodes.append({
                    'id': current['id'],
                    'name': current['name'],
                    'type': 'current',
                    'x': center_x,
                    'y': center_y,
                    'cell_line': current.get('cell_line'),
                    'passage_number': current.get('passage_number'),
                    'date_frozen': current.get('date_frozen'),
                    'radius': 0,
                    'angle': 0,
                    'group': 1,
                    'size': 12
                })
            
            # Ancestors in inner rings
            ancestors = lineage_data.get('ancestors', [])
            if ancestors:
                ancestor_radius = max_radius * 0.4
                ancestor_angle_step = (2 * math.pi) / max(len(ancestors), 1)
                
                for i, ancestor in enumerate(ancestors):
                    angle = i * ancestor_angle_step
                    x = center_x + ancestor_radius * math.cos(angle)
                    y = center_y + ancestor_radius * math.sin(angle)
                    
                    nodes.append({
                        'id': ancestor['id'],
                        'name': ancestor['name'],
                        'type': 'ancestor',
                        'x': x,
                        'y': y,
                        'cell_line': ancestor.get('cell_line'),
                        'passage_number': ancestor.get('passage_number'),
                        'date_frozen': ancestor.get('date_frozen'),
                        'radius': ancestor_radius,
                        'angle': angle,
                        'group': 2,
                        'size': 8
                    })
            
            # Descendants in outer ring
            descendants = lineage_data.get('descendants', [])
            if descendants:
                descendant_radius = max_radius * 0.8
                descendant_angle_step = (2 * math.pi) / max(len(descendants), 1)
                
                for i, descendant in enumerate(descendants):
                    angle = i * descendant_angle_step
                    x = center_x + descendant_radius * math.cos(angle)
                    y = center_y + descendant_radius * math.sin(angle)
                    
                    nodes.append({
                        'id': descendant['id'],
                        'name': descendant['name'],
                        'type': 'descendant',
                        'x': x,
                        'y': y,
                        'cell_line': descendant.get('cell_line'),
                        'passage_number': descendant.get('passage_number'),
                        'date_frozen': descendant.get('date_frozen'),
                        'radius': descendant_radius,
                        'angle': angle,
                        'group': 3,
                        'size': 8
                    })
            
            # Generate concentric circles for visual reference
            circles = [
                {'radius': max_radius * 0.4, 'label': 'Ancestors'},
                {'radius': max_radius * 0.8, 'label': 'Descendants'}
            ]
            
            return {
                'type': 'circular',
                'nodes': nodes,
                'circles': circles,
                'center': {'x': center_x, 'y': center_y},
                'max_radius': max_radius,
                'width': width,
                'height': height
            }
            
        except Exception as e:
            current_app.logger.error(f"Circular layout error: {e}")
            return cls._get_empty_layout('circular', width, height)
    
    @classmethod
    def generate_matrix_layout(cls, lineage_data, width=800, height=600):
        """
        Generate matrix/grid layout for systematic organization
        
        Args:
            lineage_data (dict): Lineage data from BatchLineageService
            width (int): Canvas width
            height (int): Canvas height
            
        Returns:
            dict: Matrix layout data with grid positioning
        """
        try:
            nodes = []
            all_nodes = []
            
            # Collect all nodes
            current = lineage_data.get('current')
            if current:
                all_nodes.append(('current', current))
            
            for ancestor in lineage_data.get('ancestors', []):
                all_nodes.append(('ancestor', ancestor))
            
            for descendant in lineage_data.get('descendants', []):
                all_nodes.append(('descendant', descendant))
            
            if not all_nodes:
                return cls._get_empty_layout('matrix', width, height)
            
            # Calculate grid dimensions
            total_nodes = len(all_nodes)
            cols = math.ceil(math.sqrt(total_nodes))
            rows = math.ceil(total_nodes / cols)
            
            # Calculate cell dimensions
            margin = 50
            cell_width = (width - 2 * margin) / cols
            cell_height = (height - 2 * margin) / rows
            
            # Position nodes in grid
            for i, (node_type, node) in enumerate(all_nodes):
                col = i % cols
                row = i // cols
                
                x = margin + (col * cell_width) + (cell_width / 2)
                y = margin + (row * cell_height) + (cell_height / 2)
                
                group = {'current': 1, 'ancestor': 2, 'descendant': 3}.get(node_type, 1)
                size = 12 if node_type == 'current' else 8
                
                nodes.append({
                    'id': node['id'],
                    'name': node['name'],
                    'type': node_type,
                    'x': x,
                    'y': y,
                    'cell_line': node.get('cell_line'),
                    'passage_number': node.get('passage_number'),
                    'date_frozen': node.get('date_frozen'),
                    'grid_col': col,
                    'grid_row': row,
                    'group': group,
                    'size': size
                })
            
            return {
                'type': 'matrix',
                'nodes': nodes,
                'grid': {
                    'cols': cols,
                    'rows': rows,
                    'cell_width': cell_width,
                    'cell_height': cell_height
                },
                'width': width,
                'height': height
            }
            
        except Exception as e:
            current_app.logger.error(f"Matrix layout error: {e}")
            return cls._get_empty_layout('matrix', width, height)
    
    # Helper methods
    
    @classmethod
    def _calculate_force_physics(cls, node_count, width, height):
        """Calculate physics parameters for force-directed layout"""
        return {
            'charge_strength': -300 - (node_count * 10),
            'link_distance': 80 + (node_count * 2),
            'link_strength': 0.7,
            'collision_radius': 20,
            'alpha': 0.3,
            'alpha_decay': 0.02,
            'velocity_decay': 0.4,
            'center_force': 0.1
        }
    
    @classmethod
    def _parse_date(cls, date_str):
        """Parse date string into datetime object"""
        try:
            # Try various date formats
            formats = [
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%d/%m/%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If all formats fail, return current time
            return datetime.now()
            
        except Exception:
            return datetime.now()
    
    @classmethod
    def _generate_timeline_axis(cls, min_date, max_date, margin, timeline_width):
        """Generate timeline axis with date markers"""
        axis_points = []
        
        try:
            date_range = (max_date - min_date).total_seconds()
            
            if date_range <= 86400:  # Less than 1 day
                # Hour markers
                interval_hours = max(1, int(date_range / 3600 / 8))  # ~8 markers
                current_date = min_date.replace(minute=0, second=0, microsecond=0)
                
                while current_date <= max_date:
                    x_ratio = (current_date - min_date).total_seconds() / date_range
                    x = margin + (x_ratio * timeline_width)
                    
                    axis_points.append({
                        'x': x,
                        'date': current_date.isoformat(),
                        'label': current_date.strftime('%H:%M'),
                        'type': 'hour'
                    })
                    
                    current_date = current_date.replace(hour=current_date.hour + interval_hours)
            
            elif date_range <= 86400 * 30:  # Less than 30 days
                # Day markers
                interval_days = max(1, int(date_range / 86400 / 8))  # ~8 markers
                current_date = min_date.replace(hour=0, minute=0, second=0, microsecond=0)
                
                while current_date <= max_date:
                    x_ratio = (current_date - min_date).total_seconds() / date_range
                    x = margin + (x_ratio * timeline_width)
                    
                    axis_points.append({
                        'x': x,
                        'date': current_date.isoformat(),
                        'label': current_date.strftime('%m/%d'),
                        'type': 'day'
                    })
                    
                    current_date = current_date.replace(day=current_date.day + interval_days)
            
            else:
                # Month markers
                current_date = min_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                while current_date <= max_date:
                    x_ratio = (current_date - min_date).total_seconds() / date_range
                    x = margin + (x_ratio * timeline_width)
                    
                    axis_points.append({
                        'x': x,
                        'date': current_date.isoformat(),
                        'label': current_date.strftime('%m/%Y'),
                        'type': 'month'
                    })
                    
                    # Move to next month
                    if current_date.month == 12:
                        current_date = current_date.replace(year=current_date.year + 1, month=1)
                    else:
                        current_date = current_date.replace(month=current_date.month + 1)
            
        except Exception as e:
            current_app.logger.warning(f"Timeline axis generation error: {e}")
        
        return axis_points
    
    @classmethod
    def _get_empty_layout(cls, layout_type, width, height):
        """Return empty layout structure"""
        return {
            'type': layout_type,
            'nodes': [],
            'width': width,
            'height': height,
            'error': 'No data available for layout generation'
        }
    
    @classmethod
    def get_available_layouts(cls):
        """Get list of available layout types"""
        return [
            {
                'type': 'hierarchical',
                'name': 'Hierarchical Tree',
                'description': 'Traditional tree layout with clear parent-child relationships',
                'icon': 'diagram-3',
                'complexity': 'simple'
            },
            {
                'type': 'radial',
                'name': 'Radial Tree',
                'description': 'Circular tree layout centered on current batch',
                'icon': 'bullseye',
                'complexity': 'simple'
            },
            {
                'type': 'force_directed',
                'name': 'Force-Directed',
                'description': 'Physics-based layout with natural node positioning',
                'icon': 'arrows-move',
                'complexity': 'moderate'
            },
            {
                'type': 'timeline',
                'name': 'Timeline',
                'description': 'Chronological layout based on creation dates',
                'icon': 'clock-history',
                'complexity': 'moderate'
            },
            {
                'type': 'circular',
                'name': 'Circular',
                'description': 'Concentric circles with current batch at center',
                'icon': 'circle',
                'complexity': 'simple'
            },
            {
                'type': 'matrix',
                'name': 'Matrix Grid',
                'description': 'Systematic grid layout for large datasets',
                'icon': 'grid',
                'complexity': 'simple'
            }
        ]
    
    @classmethod
    def get_layout_config(cls, layout_type):
        """Get configuration options for a specific layout type"""
        configs = {
            'force_directed': {
                'charge_strength': {'min': -1000, 'max': -100, 'default': -300},
                'link_distance': {'min': 30, 'max': 200, 'default': 80},
                'collision_radius': {'min': 10, 'max': 50, 'default': 20},
                'alpha': {'min': 0.1, 'max': 1.0, 'default': 0.3}
            },
            'timeline': {
                'show_axis': {'type': 'boolean', 'default': True},
                'time_format': {'options': ['auto', 'hour', 'day', 'month'], 'default': 'auto'},
                'compress_time': {'type': 'boolean', 'default': False}
            },
            'circular': {
                'inner_radius': {'min': 0.2, 'max': 0.6, 'default': 0.4},
                'outer_radius': {'min': 0.6, 'max': 0.9, 'default': 0.8},
                'show_circles': {'type': 'boolean', 'default': True}
            },
            'matrix': {
                'aspect_ratio': {'options': ['auto', 'square', 'wide'], 'default': 'auto'},
                'padding': {'min': 10, 'max': 100, 'default': 50}
            }
        }
        
        return configs.get(layout_type, {})