"""
Machine Learning Performance Predictor - AI-powered performance optimization
Phase 4 Implementation - Predictive analytics and intelligent optimization
"""
import json
import time
import math
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from flask import current_app
from .lineage_analytics_service import LineageAnalyticsService


class MLPerformancePredictor:
    """
    Machine learning-based performance predictor for History Tree system
    Uses historical data to predict performance issues and suggest optimizations
    """
    
    # Feature extraction weights
    FEATURE_WEIGHTS = {
        'complexity': 0.25,
        'data_size': 0.20,
        'user_load': 0.15,
        'cache_efficiency': 0.20,
        'time_of_day': 0.10,
        'historical_performance': 0.10
    }
    
    # Performance thresholds
    PERFORMANCE_THRESHOLDS = {
        'excellent': 100,  # < 100ms
        'good': 300,       # 100-300ms
        'acceptable': 800, # 300-800ms
        'slow': 2000,      # 800-2000ms
        'critical': 5000   # > 2000ms
    }
    
    @classmethod
    def predict_load_time(cls, batch_id, user_id=None, viewport_depth=3, include_details=True):
        """
        Predict expected load time for a specific batch request
        
        Args:
            batch_id (int): Batch identifier
            user_id (int): User requesting the data
            viewport_depth (int): Depth of data to load
            include_details (bool): Whether to include detailed information
            
        Returns:
            dict: Prediction results with confidence score and recommendations
        """
        try:
            # Extract features for prediction
            features = cls._extract_features(batch_id, user_id, viewport_depth, include_details)
            
            # Calculate prediction using weighted feature combination
            predicted_time = cls._calculate_prediction(features)
            
            # Determine confidence based on available data
            confidence = cls._calculate_confidence(features)
            
            # Generate recommendations
            recommendations = cls._generate_recommendations(features, predicted_time)
            
            # Classify performance level
            performance_level = cls._classify_performance(predicted_time)
            
            return {
                'predicted_load_time': predicted_time,
                'confidence': confidence,
                'performance_level': performance_level,
                'features': {
                    'complexity_score': features.get('complexity_score', 0),
                    'data_size_estimate': features.get('data_size_estimate', 0),
                    'user_load_factor': features.get('user_load_factor', 1.0),
                    'cache_hit_probability': features.get('cache_hit_probability', 0.5),
                    'time_factor': features.get('time_factor', 1.0)
                },
                'recommendations': recommendations,
                'model_version': '1.0'
            }
            
        except Exception as e:
            current_app.logger.error(f"Performance prediction error: {e}")
            return cls._get_fallback_prediction()
    
    @classmethod
    def predict_system_load(cls, time_horizon_minutes=60):
        """
        Predict system load and performance for the next time period
        
        Args:
            time_horizon_minutes (int): Minutes to predict ahead
            
        Returns:
            dict: System load prediction with capacity recommendations
        """
        try:
            current_time = time.time()
            
            # Analyze historical usage patterns
            usage_patterns = cls._analyze_usage_patterns(time_horizon_minutes)
            
            # Predict concurrent users
            predicted_users = cls._predict_concurrent_users(usage_patterns, time_horizon_minutes)
            
            # Predict system load
            predicted_load = cls._predict_system_load(predicted_users, usage_patterns)
            
            # Calculate capacity recommendations
            capacity_recommendations = cls._generate_capacity_recommendations(predicted_load)
            
            # Identify potential bottlenecks
            bottlenecks = cls._predict_bottlenecks(predicted_load, predicted_users)
            
            return {
                'prediction_horizon': time_horizon_minutes,
                'predicted_concurrent_users': predicted_users,
                'predicted_load_score': predicted_load,
                'capacity_utilization': min(100, (predicted_load / 100) * 100),
                'recommendations': capacity_recommendations,
                'potential_bottlenecks': bottlenecks,
                'prediction_timestamp': current_time
            }
            
        except Exception as e:
            current_app.logger.error(f"System load prediction error: {e}")
            return cls._get_fallback_system_prediction()
    
    @classmethod
    def predict_cache_efficiency(cls, batch_id, time_horizon_hours=24):
        """
        Predict cache efficiency for a specific batch
        
        Args:
            batch_id (int): Batch identifier
            time_horizon_hours (int): Hours to predict ahead
            
        Returns:
            dict: Cache efficiency prediction and optimization suggestions
        """
        try:
            # Analyze historical cache performance
            cache_history = cls._analyze_cache_history(batch_id, time_horizon_hours)
            
            # Predict hit rate
            predicted_hit_rate = cls._predict_cache_hit_rate(cache_history)
            
            # Calculate expected performance improvement
            performance_impact = cls._calculate_cache_performance_impact(predicted_hit_rate)
            
            # Generate optimization recommendations
            optimizations = cls._generate_cache_optimizations(cache_history, predicted_hit_rate)
            
            return {
                'batch_id': batch_id,
                'predicted_hit_rate': predicted_hit_rate,
                'performance_improvement': performance_impact,
                'current_efficiency': cache_history.get('current_hit_rate', 0.5),
                'optimization_potential': max(0, predicted_hit_rate - cache_history.get('current_hit_rate', 0.5)),
                'recommendations': optimizations
            }
            
        except Exception as e:
            current_app.logger.error(f"Cache efficiency prediction error: {e}")
            return {'batch_id': batch_id, 'predicted_hit_rate': 0.5, 'error': str(e)}
    
    @classmethod
    def predict_user_behavior(cls, user_id, batch_id=None):
        """
        Predict user behavior patterns and preferences
        
        Args:
            user_id (int): User identifier
            batch_id (int): Optional batch context
            
        Returns:
            dict: User behavior predictions and personalization suggestions
        """
        try:
            # Analyze user interaction history
            user_patterns = cls._analyze_user_patterns(user_id)
            
            # Predict preferred interaction types
            preferred_interactions = cls._predict_preferred_interactions(user_patterns)
            
            # Predict optimal UI configuration
            ui_preferences = cls._predict_ui_preferences(user_patterns)
            
            # Predict session duration
            predicted_session_duration = cls._predict_session_duration(user_patterns)
            
            # Generate personalization recommendations
            personalizations = cls._generate_personalization_recommendations(
                user_patterns, preferred_interactions, ui_preferences
            )
            
            return {
                'user_id': user_id,
                'predicted_session_duration': predicted_session_duration,
                'preferred_interactions': preferred_interactions,
                'ui_preferences': ui_preferences,
                'personalization_score': cls._calculate_personalization_score(user_patterns),
                'recommendations': personalizations
            }
            
        except Exception as e:
            current_app.logger.error(f"User behavior prediction error: {e}")
            return {'user_id': user_id, 'error': str(e)}
    
    # Feature extraction methods
    
    @classmethod
    def _extract_features(cls, batch_id, user_id, viewport_depth, include_details):
        """Extract features for ML prediction"""
        features = {}
        
        try:
            # Complexity score based on lineage structure
            features['complexity_score'] = cls._calculate_complexity_score(batch_id, viewport_depth)
            
            # Data size estimate
            features['data_size_estimate'] = cls._estimate_data_size(batch_id, include_details)
            
            # User load factor
            features['user_load_factor'] = cls._calculate_user_load_factor()
            
            # Cache hit probability
            features['cache_hit_probability'] = cls._calculate_cache_hit_probability(batch_id)
            
            # Time of day factor
            features['time_factor'] = cls._calculate_time_factor()
            
            # Historical performance data
            features['historical_performance'] = cls._get_historical_performance(batch_id)
            
        except Exception as e:
            current_app.logger.warning(f"Feature extraction error: {e}")
        
        return features
    
    @classmethod
    def _calculate_complexity_score(cls, batch_id, viewport_depth):
        """Calculate complexity score based on lineage structure"""
        try:
            from .batch_lineage_service import BatchLineageService
            
            # Get lineage data
            lineage_data = BatchLineageService.get_lineage_summary_stats(batch_id)
            
            # Calculate complexity factors
            ancestor_count = lineage_data.get('estimated_ancestors', 0)
            descendant_count = lineage_data.get('estimated_descendants', 0)
            total_nodes = ancestor_count + descendant_count + 1  # +1 for current
            
            # Base complexity
            complexity = math.log(max(1, total_nodes)) / math.log(10)  # Log10 scaling
            
            # Depth multiplier
            depth_multiplier = 1 + (viewport_depth * 0.2)
            
            # Final complexity score (0-10 scale)
            return min(10, complexity * depth_multiplier)
            
        except Exception:
            return 5.0  # Default medium complexity
    
    @classmethod
    def _estimate_data_size(cls, batch_id, include_details):
        """Estimate data size for the request"""
        base_size = 1.0  # Base size factor
        
        if include_details:
            base_size *= 1.5
        
        # Add complexity factor
        try:
            complexity = cls._calculate_complexity_score(batch_id, 3)
            base_size *= (1 + complexity / 10)
        except Exception:
            pass
        
        return base_size
    
    @classmethod
    def _calculate_user_load_factor(cls):
        """Calculate current user load factor"""
        try:
            # Get active users from analytics
            current_time = time.time()
            active_users = 0
            
            for batch_data in LineageAnalyticsService._usage_analytics.values():
                for interaction in batch_data:
                    if current_time - interaction['timestamp'] < 300:  # 5 minutes
                        active_users += 1
                        break  # Count each batch only once
            
            # Load factor based on active users
            if active_users == 0:
                return 0.8  # Light load
            elif active_users < 5:
                return 1.0  # Normal load
            elif active_users < 10:
                return 1.3  # Medium load
            else:
                return 1.6  # Heavy load
                
        except Exception:
            return 1.0  # Default normal load
    
    @classmethod
    def _calculate_cache_hit_probability(cls, batch_id):
        """Calculate probability of cache hit"""
        try:
            # Check if batch has been accessed recently
            current_time = time.time()
            recent_cutoff = current_time - 3600  # 1 hour
            
            batch_analytics = LineageAnalyticsService._usage_analytics.get(batch_id, [])
            recent_accesses = sum(1 for i in batch_analytics if i['timestamp'] > recent_cutoff)
            
            # Higher recent access = higher cache probability
            if recent_accesses >= 5:
                return 0.9
            elif recent_accesses >= 2:
                return 0.7
            elif recent_accesses >= 1:
                return 0.5
            else:
                return 0.2
                
        except Exception:
            return 0.5  # Default 50% probability
    
    @classmethod
    def _calculate_time_factor(cls):
        """Calculate time-of-day performance factor"""
        try:
            current_hour = datetime.now().hour
            
            # Performance varies by time of day
            if 2 <= current_hour <= 6:  # Low traffic hours
                return 0.8
            elif 9 <= current_hour <= 17:  # Business hours
                return 1.2
            elif 18 <= current_hour <= 22:  # Evening hours
                return 1.0
            else:
                return 0.9
                
        except Exception:
            return 1.0
    
    @classmethod
    def _get_historical_performance(cls, batch_id):
        """Get historical performance data for the batch"""
        try:
            # Get recent performance metrics
            load_times = []
            for metric in LineageAnalyticsService._performance_metrics.get('load_time', []):
                if metric.get('batch_id') == batch_id:
                    load_times.append(metric['value'])
            
            if load_times:
                return sum(load_times) / len(load_times)
            else:
                return 500  # Default 500ms
                
        except Exception:
            return 500
    
    # Prediction calculation methods
    
    @classmethod
    def _calculate_prediction(cls, features):
        """Calculate performance prediction using weighted features"""
        try:
            base_time = 100  # Base 100ms
            
            # Apply feature weights
            complexity_impact = features.get('complexity_score', 5) * 20  # 0-200ms
            data_size_impact = features.get('data_size_estimate', 1) * 50  # Variable
            user_load_impact = (features.get('user_load_factor', 1) - 1) * 100  # Load factor
            
            # Cache benefit
            cache_probability = features.get('cache_hit_probability', 0.5)
            cache_benefit = cache_probability * 200  # Up to 200ms savings
            
            # Time factor
            time_multiplier = features.get('time_factor', 1.0)
            
            # Historical adjustment
            historical_perf = features.get('historical_performance', 500)
            historical_weight = 0.3
            
            # Calculate weighted prediction
            predicted_time = (
                base_time + 
                complexity_impact + 
                data_size_impact + 
                user_load_impact - 
                cache_benefit
            ) * time_multiplier
            
            # Blend with historical data
            predicted_time = (predicted_time * (1 - historical_weight) + 
                            historical_perf * historical_weight)
            
            return max(50, predicted_time)  # Minimum 50ms
            
        except Exception as e:
            current_app.logger.warning(f"Prediction calculation error: {e}")
            return 500  # Fallback prediction
    
    @classmethod
    def _calculate_confidence(cls, features):
        """Calculate confidence score for the prediction"""
        confidence = 0.5  # Base confidence
        
        # More historical data = higher confidence
        if features.get('historical_performance'):
            confidence += 0.2
        
        # Recent cache data = higher confidence
        if features.get('cache_hit_probability', 0) > 0.3:
            confidence += 0.15
        
        # Complexity within normal range = higher confidence
        complexity = features.get('complexity_score', 5)
        if 2 <= complexity <= 8:
            confidence += 0.15
        
        return min(0.95, confidence)
    
    @classmethod
    def _classify_performance(cls, predicted_time):
        """Classify performance level based on predicted time"""
        if predicted_time < cls.PERFORMANCE_THRESHOLDS['excellent']:
            return 'excellent'
        elif predicted_time < cls.PERFORMANCE_THRESHOLDS['good']:
            return 'good'
        elif predicted_time < cls.PERFORMANCE_THRESHOLDS['acceptable']:
            return 'acceptable'
        elif predicted_time < cls.PERFORMANCE_THRESHOLDS['slow']:
            return 'slow'
        else:
            return 'critical'
    
    # Recommendation generation
    
    @classmethod
    def _generate_recommendations(cls, features, predicted_time):
        """Generate optimization recommendations"""
        recommendations = []
        
        # Cache recommendations
        cache_probability = features.get('cache_hit_probability', 0.5)
        if cache_probability < 0.3:
            recommendations.append({
                'type': 'cache_optimization',
                'priority': 'high',
                'message': 'Enable caching for this batch to improve load times',
                'expected_improvement': '40-60%'
            })
        
        # Complexity recommendations
        complexity = features.get('complexity_score', 5)
        if complexity > 7:
            recommendations.append({
                'type': 'complexity_reduction',
                'priority': 'medium',
                'message': 'Consider reducing viewport depth for large lineage trees',
                'expected_improvement': '20-30%'
            })
        
        # Load balancing recommendations
        user_load = features.get('user_load_factor', 1.0)
        if user_load > 1.4:
            recommendations.append({
                'type': 'load_balancing',
                'priority': 'high',
                'message': 'High user load detected - consider load balancing',
                'expected_improvement': '30-50%'
            })
        
        # Time-based recommendations
        time_factor = features.get('time_factor', 1.0)
        if time_factor > 1.1:
            recommendations.append({
                'type': 'timing_optimization',
                'priority': 'low',
                'message': 'Consider accessing during off-peak hours for better performance',
                'expected_improvement': '10-20%'
            })
        
        return recommendations
    
    # Advanced prediction methods (simplified implementations)
    
    @classmethod
    def _analyze_usage_patterns(cls, time_horizon_minutes):
        """Analyze historical usage patterns"""
        # Simplified pattern analysis
        return {
            'peak_hours': [9, 10, 11, 14, 15, 16],
            'average_concurrent_users': 3.5,
            'usage_growth_trend': 1.1  # 10% growth
        }
    
    @classmethod
    def _predict_concurrent_users(cls, usage_patterns, time_horizon_minutes):
        """Predict number of concurrent users"""
        current_hour = datetime.now().hour
        base_users = usage_patterns['average_concurrent_users']
        
        if current_hour in usage_patterns['peak_hours']:
            return int(base_users * 1.5)
        else:
            return int(base_users * 0.8)
    
    @classmethod
    def _predict_system_load(cls, predicted_users, usage_patterns):
        """Predict overall system load score"""
        base_load = predicted_users * 10  # 10 points per user
        growth_factor = usage_patterns['usage_growth_trend']
        
        return min(100, base_load * growth_factor)
    
    @classmethod
    def _generate_capacity_recommendations(cls, predicted_load):
        """Generate capacity recommendations"""
        recommendations = []
        
        if predicted_load > 80:
            recommendations.append('Consider scaling resources - high load predicted')
        elif predicted_load > 60:
            recommendations.append('Monitor closely - moderate load predicted')
        else:
            recommendations.append('Normal capacity sufficient')
        
        return recommendations
    
    @classmethod
    def _predict_bottlenecks(cls, predicted_load, predicted_users):
        """Predict potential system bottlenecks"""
        bottlenecks = []
        
        if predicted_users > 8:
            bottlenecks.append({
                'type': 'concurrent_users',
                'severity': 'medium',
                'description': 'High concurrent user load may impact response times'
            })
        
        if predicted_load > 75:
            bottlenecks.append({
                'type': 'system_resources',
                'severity': 'high',
                'description': 'System resources may become constrained'
            })
        
        return bottlenecks
    
    # Fallback methods
    
    @classmethod
    def _get_fallback_prediction(cls):
        """Return fallback prediction when ML prediction fails"""
        return {
            'predicted_load_time': 500,
            'confidence': 0.3,
            'performance_level': 'acceptable',
            'features': {},
            'recommendations': [{
                'type': 'system_check',
                'priority': 'medium',
                'message': 'Performance prediction unavailable - check system status',
                'expected_improvement': 'unknown'
            }],
            'model_version': '1.0-fallback'
        }
    
    @classmethod
    def _get_fallback_system_prediction(cls):
        """Return fallback system prediction"""
        return {
            'prediction_horizon': 60,
            'predicted_concurrent_users': 2,
            'predicted_load_score': 30,
            'capacity_utilization': 30,
            'recommendations': ['System prediction unavailable'],
            'potential_bottlenecks': [],
            'prediction_timestamp': time.time()
        }
    
    # Additional helper methods for user behavior prediction
    
    @classmethod
    def _analyze_user_patterns(cls, user_id):
        """Analyze user interaction patterns"""
        patterns = {
            'total_interactions': 0,
            'preferred_times': [],
            'interaction_types': Counter(),
            'session_lengths': [],
            'last_active': None
        }
        
        try:
            # Collect user data from analytics
            for batch_data in LineageAnalyticsService._usage_analytics.values():
                for interaction in batch_data:
                    if interaction['user_id'] == user_id:
                        patterns['total_interactions'] += 1
                        patterns['interaction_types'][interaction['interaction_type']] += 1
                        
                        # Track time patterns
                        hour = datetime.fromtimestamp(interaction['timestamp']).hour
                        patterns['preferred_times'].append(hour)
                        
                        patterns['last_active'] = max(
                            patterns['last_active'] or 0, 
                            interaction['timestamp']
                        )
        
        except Exception as e:
            current_app.logger.warning(f"User pattern analysis error: {e}")
        
        return patterns
    
    @classmethod
    def _predict_preferred_interactions(cls, user_patterns):
        """Predict user's preferred interaction types"""
        interaction_types = user_patterns['interaction_types']
        total = sum(interaction_types.values())
        
        if total == 0:
            return {'view': 0.6, 'zoom': 0.2, 'export': 0.1, 'search': 0.1}
        
        preferences = {}
        for interaction_type, count in interaction_types.items():
            preferences[interaction_type] = count / total
        
        return preferences
    
    @classmethod
    def _predict_ui_preferences(cls, user_patterns):
        """Predict optimal UI configuration for user"""
        preferences = {
            'enhanced_mode': True,
            'default_layout': 'hierarchical',
            'animation_speed': 300,
            'auto_zoom': False
        }
        
        # Customize based on user patterns
        if user_patterns['total_interactions'] > 20:
            preferences['enhanced_mode'] = True
            preferences['auto_zoom'] = True
        
        return preferences
    
    @classmethod
    def _predict_session_duration(cls, user_patterns):
        """Predict expected session duration"""
        session_lengths = user_patterns.get('session_lengths', [])
        
        if session_lengths:
            avg_session = sum(session_lengths) / len(session_lengths)
            return max(300, avg_session)  # Minimum 5 minutes
        
        return 900  # Default 15 minutes
    
    @classmethod
    def _generate_personalization_recommendations(cls, user_patterns, preferred_interactions, ui_preferences):
        """Generate personalization recommendations"""
        recommendations = []
        
        # Based on interaction patterns
        if preferred_interactions.get('export', 0) > 0.2:
            recommendations.append({
                'type': 'ui_customization',
                'suggestion': 'Show export options prominently',
                'reason': 'User frequently exports data'
            })
        
        if preferred_interactions.get('zoom', 0) > 0.3:
            recommendations.append({
                'type': 'ui_customization',
                'suggestion': 'Enable auto-zoom features',
                'reason': 'User frequently uses zoom controls'
            })
        
        # Based on usage frequency
        if user_patterns['total_interactions'] > 50:
            recommendations.append({
                'type': 'feature_access',
                'suggestion': 'Enable advanced features by default',
                'reason': 'Power user with high engagement'
            })
        
        return recommendations
    
    @classmethod
    def _calculate_personalization_score(cls, user_patterns):
        """Calculate how much personalization would benefit the user"""
        total_interactions = user_patterns['total_interactions']
        
        if total_interactions == 0:
            return 0.1  # Low benefit for new users
        elif total_interactions < 10:
            return 0.3  # Some benefit
        elif total_interactions < 50:
            return 0.6  # Good benefit
        else:
            return 0.9  # High benefit for power users
    
    # Cache-specific prediction methods
    
    @classmethod
    def _analyze_cache_history(cls, batch_id, time_horizon_hours):
        """Analyze historical cache performance"""
        history = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'current_hit_rate': 0.5,
            'performance_impact': 0.3
        }
        
        try:
            # Analyze cache performance from metrics
            current_time = time.time()
            cutoff_time = current_time - (time_horizon_hours * 3600)
            
            for metric in LineageAnalyticsService._performance_metrics.get('cache_hit', []):
                if (metric.get('batch_id') == batch_id and 
                    metric['timestamp'] > cutoff_time):
                    history['total_requests'] += 1
                    if metric['value'] > 0.5:  # Assume cache hit if value > 0.5
                        history['cache_hits'] += 1
                    else:
                        history['cache_misses'] += 1
            
            if history['total_requests'] > 0:
                history['current_hit_rate'] = history['cache_hits'] / history['total_requests']
        
        except Exception as e:
            current_app.logger.warning(f"Cache history analysis error: {e}")
        
        return history
    
    @classmethod
    def _predict_cache_hit_rate(cls, cache_history):
        """Predict future cache hit rate"""
        current_rate = cache_history['current_hit_rate']
        total_requests = cache_history['total_requests']
        
        # Improve prediction based on request volume
        if total_requests == 0:
            return 0.3  # Low hit rate for new data
        elif total_requests < 5:
            return min(0.6, current_rate + 0.1)  # Slight improvement
        else:
            return min(0.9, current_rate + 0.2)  # Good improvement potential
    
    @classmethod
    def _calculate_cache_performance_impact(cls, predicted_hit_rate):
        """Calculate expected performance improvement from caching"""
        # Assume cache saves 70% of load time on average
        cache_savings = 0.7
        return predicted_hit_rate * cache_savings
    
    @classmethod
    def _generate_cache_optimizations(cls, cache_history, predicted_hit_rate):
        """Generate cache optimization recommendations"""
        optimizations = []
        
        current_rate = cache_history['current_hit_rate']
        improvement_potential = predicted_hit_rate - current_rate
        
        if improvement_potential > 0.2:
            optimizations.append({
                'type': 'cache_warming',
                'priority': 'high',
                'description': 'Pre-warm cache for this batch',
                'expected_improvement': f"{improvement_potential*100:.1f}% hit rate increase"
            })
        
        if cache_history['total_requests'] < 3:
            optimizations.append({
                'type': 'usage_promotion',
                'priority': 'medium',
                'description': 'Promote usage to improve cache efficiency',
                'expected_improvement': 'Better cache utilization'
            })
        
        return optimizations