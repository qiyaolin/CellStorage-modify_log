"""
Lineage Analytics Service - Advanced analytics and usage pattern tracking for History Tree
Phase 4 Implementation - Enterprise analytics and machine learning insights
"""
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from flask import current_app, request, session
from sqlalchemy import func, and_, or_
from ..cell_storage.models import VialBatch, CryoVial, CellLine, User
from .. import db


class LineageAnalyticsService:
    """
    Advanced analytics service for History Tree usage patterns and insights
    Enterprise-level analytics with privacy protection and performance optimization
    """
    
    # In-memory analytics storage for App Engine compatibility
    _usage_analytics = defaultdict(list)
    _performance_metrics = defaultdict(list)
    _user_patterns = defaultdict(dict)
    _collaboration_data = defaultdict(list)
    
    @classmethod
    def track_user_interaction(cls, user_id, batch_id, interaction_type, metadata=None):
        """
        Track user interactions with History Tree for pattern analysis
        
        Args:
            user_id (int): User identifier
            batch_id (int): Batch being viewed
            interaction_type (str): Type of interaction (view, zoom, export, etc.)
            metadata (dict): Additional interaction data
        """
        try:
            timestamp = time.time()
            interaction_data = {
                'timestamp': timestamp,
                'user_id': user_id,
                'batch_id': batch_id,
                'interaction_type': interaction_type,
                'metadata': metadata or {},
                'session_id': session.get('user_id', 'anonymous'),
                'ip_hash': hash(request.remote_addr) if request else None,  # Privacy-protected IP
                'user_agent_hash': hash(request.user_agent.string) if request else None
            }
            
            # Store in analytics
            cls._usage_analytics[batch_id].append(interaction_data)
            cls._user_patterns[user_id]['last_interaction'] = timestamp
            cls._user_patterns[user_id]['total_interactions'] = cls._user_patterns[user_id].get('total_interactions', 0) + 1
            
            # Cleanup old data (keep last 7 days)
            cls._cleanup_old_analytics()
            
        except Exception as e:
            current_app.logger.warning(f"Analytics tracking error: {e}")
    
    @classmethod
    def track_performance_metric(cls, metric_type, value, batch_id=None, user_id=None):
        """
        Track performance metrics for optimization insights
        
        Args:
            metric_type (str): Type of metric (load_time, render_time, cache_hit, etc.)
            value (float): Metric value
            batch_id (int): Associated batch ID
            user_id (int): Associated user ID
        """
        try:
            metric_data = {
                'timestamp': time.time(),
                'metric_type': metric_type,
                'value': value,
                'batch_id': batch_id,
                'user_id': user_id
            }
            
            cls._performance_metrics[metric_type].append(metric_data)
            
            # Cleanup old metrics (keep last 24 hours)
            cls._cleanup_old_metrics()
            
        except Exception as e:
            current_app.logger.warning(f"Performance tracking error: {e}")
    
    @classmethod
    def get_usage_patterns(cls, batch_id=None, time_range_hours=24):
        """
        Analyze usage patterns and return insights
        
        Args:
            batch_id (int): Optional batch filter
            time_range_hours (int): Time range for analysis
            
        Returns:
            dict: Usage pattern insights
        """
        try:
            cutoff_time = time.time() - (time_range_hours * 3600)
            
            # Filter data by time range
            if batch_id:
                interactions = [i for i in cls._usage_analytics[batch_id] 
                              if i['timestamp'] > cutoff_time]
            else:
                interactions = []
                for batch_data in cls._usage_analytics.values():
                    interactions.extend([i for i in batch_data if i['timestamp'] > cutoff_time])
            
            if not interactions:
                return cls._get_empty_patterns()
            
            # Analyze patterns
            interaction_types = Counter(i['interaction_type'] for i in interactions)
            user_activity = Counter(i['user_id'] for i in interactions)
            batch_popularity = Counter(i['batch_id'] for i in interactions)
            hourly_activity = cls._analyze_hourly_patterns(interactions)
            
            # Calculate insights
            total_interactions = len(interactions)
            unique_users = len(set(i['user_id'] for i in interactions))
            unique_batches = len(set(i['batch_id'] for i in interactions))
            avg_session_length = cls._calculate_avg_session_length(interactions)
            
            return {
                'summary': {
                    'total_interactions': total_interactions,
                    'unique_users': unique_users,
                    'unique_batches': unique_batches,
                    'avg_session_length': avg_session_length,
                    'time_range_hours': time_range_hours
                },
                'interaction_types': dict(interaction_types.most_common(10)),
                'user_activity': dict(user_activity.most_common(10)),
                'popular_batches': dict(batch_popularity.most_common(10)),
                'hourly_patterns': hourly_activity,
                'insights': cls._generate_usage_insights(interactions)
            }
            
        except Exception as e:
            current_app.logger.error(f"Usage pattern analysis error: {e}")
            return cls._get_empty_patterns()
    
    @classmethod
    def get_performance_insights(cls, metric_type=None, time_range_hours=24):
        """
        Analyze performance metrics and provide optimization insights
        
        Args:
            metric_type (str): Optional metric type filter
            time_range_hours (int): Time range for analysis
            
        Returns:
            dict: Performance insights and recommendations
        """
        try:
            cutoff_time = time.time() - (time_range_hours * 3600)
            
            if metric_type:
                metrics = [m for m in cls._performance_metrics[metric_type] 
                          if m['timestamp'] > cutoff_time]
            else:
                metrics = []
                for metric_data in cls._performance_metrics.values():
                    metrics.extend([m for m in metric_data if m['timestamp'] > cutoff_time])
            
            if not metrics:
                return cls._get_empty_performance_insights()
            
            # Group metrics by type
            metrics_by_type = defaultdict(list)
            for metric in metrics:
                metrics_by_type[metric['metric_type']].append(metric['value'])
            
            # Calculate statistics
            performance_stats = {}
            for m_type, values in metrics_by_type.items():
                performance_stats[m_type] = {
                    'count': len(values),
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'median': sorted(values)[len(values) // 2],
                    'p95': sorted(values)[int(len(values) * 0.95)] if len(values) > 20 else max(values)
                }
            
            # Generate recommendations
            recommendations = cls._generate_performance_recommendations(performance_stats)
            
            return {
                'summary': {
                    'total_metrics': len(metrics),
                    'metric_types': len(metrics_by_type),
                    'time_range_hours': time_range_hours
                },
                'performance_stats': performance_stats,
                'recommendations': recommendations,
                'trends': cls._analyze_performance_trends(metrics),
                'optimization_score': cls._calculate_optimization_score(performance_stats)
            }
            
        except Exception as e:
            current_app.logger.error(f"Performance analysis error: {e}")
            return cls._get_empty_performance_insights()
    
    @classmethod
    def get_collaboration_insights(cls, time_range_hours=24):
        """
        Analyze collaborative usage patterns
        
        Args:
            time_range_hours (int): Time range for analysis
            
        Returns:
            dict: Collaboration insights
        """
        try:
            cutoff_time = time.time() - (time_range_hours * 3600)
            
            # Get recent interactions
            all_interactions = []
            for batch_data in cls._usage_analytics.values():
                all_interactions.extend([i for i in batch_data if i['timestamp'] > cutoff_time])
            
            if not all_interactions:
                return cls._get_empty_collaboration_insights()
            
            # Analyze collaboration patterns
            concurrent_users = cls._analyze_concurrent_usage(all_interactions)
            shared_batches = cls._analyze_shared_batch_usage(all_interactions)
            user_overlap = cls._analyze_user_overlap(all_interactions)
            
            return {
                'summary': {
                    'total_collaborative_sessions': len(concurrent_users),
                    'shared_batches': len(shared_batches),
                    'collaboration_score': cls._calculate_collaboration_score(all_interactions)
                },
                'concurrent_usage': concurrent_users,
                'shared_batches': shared_batches,
                'user_overlap': user_overlap,
                'collaboration_opportunities': cls._identify_collaboration_opportunities(all_interactions)
            }
            
        except Exception as e:
            current_app.logger.error(f"Collaboration analysis error: {e}")
            return cls._get_empty_collaboration_insights()
    
    @classmethod
    def predict_batch_interest(cls, user_id, limit=10):
        """
        Machine learning-based prediction of batches a user might be interested in
        
        Args:
            user_id (int): User identifier
            limit (int): Number of recommendations
            
        Returns:
            list: Recommended batch IDs with confidence scores
        """
        try:
            # Get user interaction history
            user_interactions = []
            for batch_data in cls._usage_analytics.values():
                user_interactions.extend([i for i in batch_data if i['user_id'] == user_id])
            
            if not user_interactions:
                return cls._get_popular_batches(limit)
            
            # Analyze user preferences
            user_batches = set(i['batch_id'] for i in user_interactions)
            interaction_weights = {
                'view': 1.0,
                'zoom': 1.5,
                'export': 2.0,
                'search': 1.2,
                'layout_change': 1.3,
                'critical_path': 1.8
            }
            
            # Calculate batch scores based on user behavior
            batch_scores = defaultdict(float)
            for interaction in user_interactions:
                batch_id = interaction['batch_id']
                interaction_type = interaction['interaction_type']
                weight = interaction_weights.get(interaction_type, 1.0)
                
                # Recent interactions have higher weight
                time_weight = max(0.1, 1.0 - (time.time() - interaction['timestamp']) / (7 * 24 * 3600))
                batch_scores[batch_id] += weight * time_weight
            
            # Find similar batches using database relationships
            similar_batches = cls._find_similar_batches(list(user_batches))
            
            # Score similar batches
            recommendations = []
            for batch_id, similarity_score in similar_batches:
                if batch_id not in user_batches:
                    confidence = min(0.95, similarity_score * 0.8 + 0.2)
                    recommendations.append({
                        'batch_id': batch_id,
                        'confidence': confidence,
                        'reason': 'similar_lineage'
                    })
            
            # Add popular batches with lower confidence
            popular_batches = cls._get_popular_batches(limit * 2)
            for batch_id in popular_batches:
                if batch_id not in user_batches and not any(r['batch_id'] == batch_id for r in recommendations):
                    recommendations.append({
                        'batch_id': batch_id,
                        'confidence': 0.3,
                        'reason': 'popular'
                    })
            
            # Sort by confidence and limit results
            recommendations.sort(key=lambda x: x['confidence'], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            current_app.logger.error(f"Batch prediction error: {e}")
            return []
    
    @classmethod
    def get_system_health_metrics(cls):
        """
        Get overall system health and performance metrics
        
        Returns:
            dict: System health indicators
        """
        try:
            current_time = time.time()
            
            # Calculate system metrics
            total_analytics_entries = sum(len(data) for data in cls._usage_analytics.values())
            total_performance_entries = sum(len(data) for data in cls._performance_metrics.values())
            active_users_24h = len(set(
                i['user_id'] for batch_data in cls._usage_analytics.values() 
                for i in batch_data if current_time - i['timestamp'] < 24 * 3600
            ))
            
            # Memory usage estimation
            estimated_memory_kb = (total_analytics_entries + total_performance_entries) * 0.5  # ~500 bytes per entry
            
            # Performance health
            recent_load_times = [
                m['value'] for m in cls._performance_metrics.get('load_time', [])
                if current_time - m['timestamp'] < 3600  # Last hour
            ]
            avg_load_time = sum(recent_load_times) / len(recent_load_times) if recent_load_times else 0
            
            # System health score (0-100)
            health_score = cls._calculate_system_health_score(
                avg_load_time, estimated_memory_kb, active_users_24h
            )
            
            return {
                'health_score': health_score,
                'analytics': {
                    'total_entries': total_analytics_entries,
                    'active_users_24h': active_users_24h,
                    'memory_usage_kb': estimated_memory_kb
                },
                'performance': {
                    'total_metrics': total_performance_entries,
                    'avg_load_time_1h': avg_load_time,
                    'metrics_types': len(cls._performance_metrics)
                },
                'recommendations': cls._generate_system_recommendations(health_score)
            }
            
        except Exception as e:
            current_app.logger.error(f"System health metrics error: {e}")
            return {'health_score': 0, 'error': str(e)}
    
    # Helper methods
    
    @classmethod
    def _cleanup_old_analytics(cls):
        """Clean up analytics data older than 7 days"""
        cutoff_time = time.time() - (7 * 24 * 3600)
        for batch_id in list(cls._usage_analytics.keys()):
            cls._usage_analytics[batch_id] = [
                i for i in cls._usage_analytics[batch_id] 
                if i['timestamp'] > cutoff_time
            ]
            if not cls._usage_analytics[batch_id]:
                del cls._usage_analytics[batch_id]
    
    @classmethod
    def _cleanup_old_metrics(cls):
        """Clean up performance metrics older than 24 hours"""
        cutoff_time = time.time() - (24 * 3600)
        for metric_type in list(cls._performance_metrics.keys()):
            cls._performance_metrics[metric_type] = [
                m for m in cls._performance_metrics[metric_type] 
                if m['timestamp'] > cutoff_time
            ]
            if not cls._performance_metrics[metric_type]:
                del cls._performance_metrics[metric_type]
    
    @classmethod
    def _analyze_hourly_patterns(cls, interactions):
        """Analyze usage patterns by hour"""
        hourly_counts = defaultdict(int)
        for interaction in interactions:
            hour = datetime.fromtimestamp(interaction['timestamp']).hour
            hourly_counts[hour] += 1
        return dict(hourly_counts)
    
    @classmethod
    def _calculate_avg_session_length(cls, interactions):
        """Calculate average session length"""
        sessions = defaultdict(list)
        for interaction in interactions:
            session_id = interaction['session_id']
            sessions[session_id].append(interaction['timestamp'])
        
        session_lengths = []
        for timestamps in sessions.values():
            if len(timestamps) > 1:
                session_lengths.append(max(timestamps) - min(timestamps))
        
        return sum(session_lengths) / len(session_lengths) if session_lengths else 0
    
    @classmethod
    def _find_similar_batches(cls, user_batches):
        """Find batches similar to user's viewed batches"""
        try:
            similar_batches = []
            
            # Query database for related batches
            for batch_id in user_batches[:5]:  # Limit to avoid performance issues
                batch = VialBatch.query.get(batch_id)
                if batch:
                    # Find batches with same cell line
                    cell_line_batches = VialBatch.query.filter(
                        and_(
                            VialBatch.cell_line_id == batch.cell_line_id,
                            VialBatch.id != batch_id
                        )
                    ).limit(10).all()
                    
                    for similar_batch in cell_line_batches:
                        similar_batches.append((similar_batch.id, 0.8))
                    
                    # Find lineage-related batches
                    lineage_tree = batch.get_lineage_tree()
                    if lineage_tree:
                        for node in lineage_tree.get('ancestors', []) + lineage_tree.get('descendants', []):
                            similar_batches.append((node['id'], 0.6))
            
            # Remove duplicates and sort by similarity
            unique_batches = {}
            for batch_id, score in similar_batches:
                if batch_id not in unique_batches or unique_batches[batch_id] < score:
                    unique_batches[batch_id] = score
            
            return sorted(unique_batches.items(), key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            current_app.logger.warning(f"Similar batch finding error: {e}")
            return []
    
    @classmethod
    def _get_popular_batches(cls, limit):
        """Get most popular batches from analytics"""
        batch_popularity = defaultdict(int)
        for batch_data in cls._usage_analytics.values():
            for interaction in batch_data:
                batch_popularity[interaction['batch_id']] += 1
        
        popular_batches = sorted(batch_popularity.items(), key=lambda x: x[1], reverse=True)
        return [batch_id for batch_id, _ in popular_batches[:limit]]
    
    @classmethod
    def _calculate_system_health_score(cls, avg_load_time, memory_usage_kb, active_users):
        """Calculate overall system health score"""
        score = 100
        
        # Penalize slow load times
        if avg_load_time > 1000:  # 1 second
            score -= min(30, (avg_load_time - 1000) / 100)
        
        # Penalize high memory usage
        if memory_usage_kb > 10000:  # 10MB
            score -= min(20, (memory_usage_kb - 10000) / 1000)
        
        # Boost for active users
        score += min(10, active_users / 5)
        
        return max(0, min(100, score))
    
    @classmethod
    def _generate_system_recommendations(cls, health_score):
        """Generate system optimization recommendations"""
        recommendations = []
        
        if health_score < 70:
            recommendations.append("Consider enabling more aggressive caching")
            recommendations.append("Monitor memory usage and implement cleanup routines")
        
        if health_score < 50:
            recommendations.append("Critical: Review performance bottlenecks")
            recommendations.append("Consider scaling or optimization")
        
        if health_score > 90:
            recommendations.append("System performing well - consider enabling advanced features")
        
        return recommendations
    
    # Empty result helpers
    
    @classmethod
    def _get_empty_patterns(cls):
        """Return empty usage patterns structure"""
        return {
            'summary': {'total_interactions': 0, 'unique_users': 0, 'unique_batches': 0},
            'interaction_types': {},
            'user_activity': {},
            'popular_batches': {},
            'hourly_patterns': {},
            'insights': []
        }
    
    @classmethod
    def _get_empty_performance_insights(cls):
        """Return empty performance insights structure"""
        return {
            'summary': {'total_metrics': 0, 'metric_types': 0},
            'performance_stats': {},
            'recommendations': [],
            'trends': {},
            'optimization_score': 0
        }
    
    @classmethod
    def _get_empty_collaboration_insights(cls):
        """Return empty collaboration insights structure"""
        return {
            'summary': {'total_collaborative_sessions': 0, 'shared_batches': 0, 'collaboration_score': 0},
            'concurrent_usage': {},
            'shared_batches': {},
            'user_overlap': {},
            'collaboration_opportunities': []
        }
    
    # Additional helper methods for advanced analytics
    
    @classmethod
    def _generate_usage_insights(cls, interactions):
        """Generate actionable insights from usage data"""
        insights = []
        
        # Most popular interaction types
        interaction_types = Counter(i['interaction_type'] for i in interactions)
        if interaction_types:
            top_interaction = interaction_types.most_common(1)[0]
            insights.append(f"Most common interaction: {top_interaction[0]} ({top_interaction[1]} times)")
        
        # Peak usage times
        hourly_patterns = cls._analyze_hourly_patterns(interactions)
        if hourly_patterns:
            peak_hour = max(hourly_patterns, key=hourly_patterns.get)
            insights.append(f"Peak usage time: {peak_hour}:00 ({hourly_patterns[peak_hour]} interactions)")
        
        return insights
    
    @classmethod
    def _generate_performance_recommendations(cls, performance_stats):
        """Generate performance optimization recommendations"""
        recommendations = []
        
        for metric_type, stats in performance_stats.items():
            if metric_type == 'load_time' and stats['average'] > 1000:
                recommendations.append(f"Load times averaging {stats['average']:.0f}ms - consider caching optimization")
            
            if metric_type == 'render_time' and stats['average'] > 500:
                recommendations.append(f"Render times averaging {stats['average']:.0f}ms - consider reducing visual complexity")
            
            if metric_type == 'cache_hit' and stats['average'] < 0.7:
                recommendations.append(f"Cache hit rate at {stats['average']*100:.1f}% - consider warming cache")
        
        return recommendations
    
    @classmethod
    def _analyze_performance_trends(cls, metrics):
        """Analyze performance trends over time"""
        trends = {}
        
        # Group metrics by type and analyze trends
        metrics_by_type = defaultdict(list)
        for metric in metrics:
            metrics_by_type[metric['metric_type']].append((metric['timestamp'], metric['value']))
        
        for metric_type, values in metrics_by_type.items():
            if len(values) > 5:  # Need sufficient data for trend analysis
                # Simple trend analysis - compare first half vs second half
                values.sort(key=lambda x: x[0])  # Sort by timestamp
                mid_point = len(values) // 2
                first_half_avg = sum(v[1] for v in values[:mid_point]) / mid_point
                second_half_avg = sum(v[1] for v in values[mid_point:]) / (len(values) - mid_point)
                
                trend_direction = 'improving' if second_half_avg < first_half_avg else 'degrading'
                trend_magnitude = abs(second_half_avg - first_half_avg) / first_half_avg * 100
                
                trends[metric_type] = {
                    'direction': trend_direction,
                    'magnitude': trend_magnitude,
                    'first_half_avg': first_half_avg,
                    'second_half_avg': second_half_avg
                }
        
        return trends
    
    @classmethod
    def _calculate_optimization_score(cls, performance_stats):
        """Calculate overall optimization score"""
        if not performance_stats:
            return 0
        
        score = 100
        
        # Check load times
        if 'load_time' in performance_stats:
            load_avg = performance_stats['load_time']['average']
            if load_avg > 1000:
                score -= min(30, (load_avg - 1000) / 100)
        
        # Check cache hit rate
        if 'cache_hit' in performance_stats:
            cache_rate = performance_stats['cache_hit']['average']
            if cache_rate < 0.7:
                score -= (0.7 - cache_rate) * 50
        
        return max(0, min(100, score))
    
    @classmethod
    def _analyze_concurrent_usage(cls, interactions):
        """Analyze concurrent user activity"""
        # Group interactions by time windows (5-minute windows)
        time_windows = defaultdict(set)
        
        for interaction in interactions:
            window = int(interaction['timestamp'] // 300) * 300  # 5-minute windows
            time_windows[window].add(interaction['user_id'])
        
        # Find windows with multiple users
        concurrent_sessions = {}
        for window, users in time_windows.items():
            if len(users) > 1:
                concurrent_sessions[window] = len(users)
        
        return concurrent_sessions
    
    @classmethod
    def _analyze_shared_batch_usage(cls, interactions):
        """Analyze batches accessed by multiple users"""
        batch_users = defaultdict(set)
        
        for interaction in interactions:
            batch_users[interaction['batch_id']].add(interaction['user_id'])
        
        # Find batches accessed by multiple users
        shared_batches = {
            batch_id: len(users) for batch_id, users in batch_users.items() 
            if len(users) > 1
        }
        
        return shared_batches
    
    @classmethod
    def _analyze_user_overlap(cls, interactions):
        """Analyze user interaction overlap patterns"""
        user_batches = defaultdict(set)
        
        for interaction in interactions:
            user_batches[interaction['user_id']].add(interaction['batch_id'])
        
        # Calculate overlap between users
        user_overlap = {}
        users = list(user_batches.keys())
        
        for i, user1 in enumerate(users):
            for user2 in users[i+1:]:
                overlap = len(user_batches[user1] & user_batches[user2])
                if overlap > 0:
                    user_overlap[f"{user1}-{user2}"] = overlap
        
        return user_overlap
    
    @classmethod
    def _calculate_collaboration_score(cls, interactions):
        """Calculate overall collaboration score"""
        if not interactions:
            return 0
        
        unique_users = len(set(i['user_id'] for i in interactions))
        unique_batches = len(set(i['batch_id'] for i in interactions))
        
        if unique_users < 2:
            return 0
        
        # Calculate collaboration based on shared batch usage
        batch_users = defaultdict(set)
        for interaction in interactions:
            batch_users[interaction['batch_id']].add(interaction['user_id'])
        
        shared_batches = sum(1 for users in batch_users.values() if len(users) > 1)
        collaboration_score = (shared_batches / unique_batches) * 100 if unique_batches > 0 else 0
        
        return min(100, collaboration_score)
    
    @classmethod
    def _identify_collaboration_opportunities(cls, interactions):
        """Identify potential collaboration opportunities"""
        opportunities = []
        
        # Users working with related batches
        user_batches = defaultdict(set)
        for interaction in interactions:
            user_batches[interaction['user_id']].add(interaction['batch_id'])
        
        # Find users working with lineage-related batches
        try:
            for user1, batches1 in user_batches.items():
                for user2, batches2 in user_batches.items():
                    if user1 != user2:
                        # Check for lineage relationships between user batches
                        for batch1 in batches1:
                            for batch2 in batches2:
                                if cls._are_batches_related(batch1, batch2):
                                    opportunities.append({
                                        'type': 'related_lineage',
                                        'users': [user1, user2],
                                        'batches': [batch1, batch2],
                                        'description': f"Users working with related batches in lineage tree"
                                    })
        except Exception as e:
            current_app.logger.warning(f"Collaboration opportunity analysis error: {e}")
        
        return opportunities[:10]  # Limit to top 10 opportunities
    
    @classmethod
    def _are_batches_related(cls, batch1_id, batch2_id):
        """Check if two batches are related in lineage"""
        try:
            batch1 = VialBatch.query.get(batch1_id)
            batch2 = VialBatch.query.get(batch2_id)
            
            if not batch1 or not batch2:
                return False
            
            # Check if same cell line
            if batch1.cell_line_id == batch2.cell_line_id:
                return True
            
            # Check if in same lineage tree (simplified check)
            lineage1 = batch1.get_lineage_tree(max_depth=3)
            if lineage1:
                all_related_ids = set()
                for ancestor in lineage1.get('ancestors', []):
                    all_related_ids.add(ancestor['id'])
                for descendant in lineage1.get('descendants', []):
                    all_related_ids.add(descendant['id'])
                
                return batch2_id in all_related_ids
            
            return False
            
        except Exception as e:
            current_app.logger.warning(f"Batch relationship check error: {e}")
            return False