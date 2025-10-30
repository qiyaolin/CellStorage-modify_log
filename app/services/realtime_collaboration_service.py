"""
Real-time Collaboration Service - WebSocket integration for live collaboration
Phase 4 Implementation - Real-time sync and collaborative features
"""
import json
import time
from datetime import datetime
from flask import current_app
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from ..cell_storage.models import User, VialBatch


class RealtimeCollaborationService:
    """
    Real-time collaboration service using WebSocket for live updates
    Handles user presence, batch viewing, and collaborative interactions
    """
    
    # User presence tracking
    _active_users = {}  # session_id -> user_info
    _batch_viewers = {}  # batch_id -> set of session_ids
    _user_cursors = {}  # session_id -> cursor position data
    
    @classmethod
    def init_socketio(cls, app):
        """Initialize SocketIO with the Flask app"""
        socketio = SocketIO(
            app, 
            cors_allowed_origins="*",
            async_mode='threading',
            ping_timeout=60,
            ping_interval=25
        )
        
        # Register event handlers
        cls._register_handlers(socketio)
        
        return socketio
    
    @classmethod
    def _register_handlers(cls, socketio):
        """Register WebSocket event handlers"""
        
        @socketio.on('connect')
        def handle_connect(auth):
            """Handle user connection"""
            try:
                # Verify authentication
                user_id = auth.get('user_id') if auth else None
                if not user_id:
                    return False  # Reject connection
                
                user = User.query.get(user_id)
                if not user:
                    return False  # Reject connection
                
                # Store user session
                session_id = request.sid
                cls._active_users[session_id] = {
                    'user_id': user_id,
                    'username': user.username,
                    'connected_at': time.time(),
                    'current_batch': None
                }
                
                current_app.logger.info(f"User {user.username} connected: {session_id}")
                
                # Notify others about new user
                emit('user_connected', {
                    'user_id': user_id,
                    'username': user.username
                }, broadcast=True, include_self=False)
                
                return True
                
            except Exception as e:
                current_app.logger.error(f"Connection error: {e}")
                return False
        
        @socketio.on('disconnect')
        def handle_disconnect():
            """Handle user disconnection"""
            try:
                session_id = request.sid
                
                if session_id in cls._active_users:
                    user_info = cls._active_users[session_id]
                    
                    # Leave any batch rooms
                    current_batch = user_info.get('current_batch')
                    if current_batch:
                        cls._leave_batch_room(session_id, current_batch)
                    
                    # Remove from active users
                    del cls._active_users[session_id]
                    
                    # Notify others about user leaving
                    emit('user_disconnected', {
                        'user_id': user_info['user_id'],
                        'username': user_info['username']
                    }, broadcast=True)
                    
                    current_app.logger.info(f"User {user_info['username']} disconnected: {session_id}")
                
            except Exception as e:
                current_app.logger.error(f"Disconnection error: {e}")
        
        @socketio.on('join_batch')
        def handle_join_batch(data):
            """Handle user joining a batch viewing room"""
            try:
                session_id = request.sid
                batch_id = data.get('batch_id')
                
                if not batch_id or session_id not in cls._active_users:
                    return
                
                # Verify batch exists
                batch = VialBatch.query.get(batch_id)
                if not batch:
                    emit('error', {'message': f'Batch {batch_id} not found'})
                    return
                
                # Leave previous batch room if any
                previous_batch = cls._active_users[session_id].get('current_batch')
                if previous_batch and previous_batch != batch_id:
                    cls._leave_batch_room(session_id, previous_batch)
                
                # Join new batch room
                join_room(f"batch_{batch_id}")
                cls._active_users[session_id]['current_batch'] = batch_id
                
                # Track batch viewers
                if batch_id not in cls._batch_viewers:
                    cls._batch_viewers[batch_id] = set()
                cls._batch_viewers[batch_id].add(session_id)
                
                user_info = cls._active_users[session_id]
                
                # Notify others in the batch room
                emit('user_joined_batch', {
                    'user_id': user_info['user_id'],
                    'username': user_info['username'],
                    'batch_id': batch_id,
                    'viewer_count': len(cls._batch_viewers[batch_id])
                }, room=f"batch_{batch_id}", include_self=False)
                
                # Send current viewers to the joining user
                current_viewers = []
                for viewer_session in cls._batch_viewers[batch_id]:
                    if viewer_session != session_id and viewer_session in cls._active_users:
                        viewer_info = cls._active_users[viewer_session]
                        current_viewers.append({
                            'user_id': viewer_info['user_id'],
                            'username': viewer_info['username']
                        })
                
                emit('batch_viewers_update', {
                    'batch_id': batch_id,
                    'viewers': current_viewers,
                    'viewer_count': len(cls._batch_viewers[batch_id])
                })
                
                current_app.logger.info(f"User {user_info['username']} joined batch {batch_id}")
                
            except Exception as e:
                current_app.logger.error(f"Join batch error: {e}")
                emit('error', {'message': 'Failed to join batch room'})
        
        @socketio.on('leave_batch')
        def handle_leave_batch(data):
            """Handle user leaving a batch viewing room"""
            try:
                session_id = request.sid
                batch_id = data.get('batch_id')
                
                if session_id in cls._active_users:
                    cls._leave_batch_room(session_id, batch_id)
                
            except Exception as e:
                current_app.logger.error(f"Leave batch error: {e}")
        
        @socketio.on('cursor_update')
        def handle_cursor_update(data):
            """Handle cursor position updates for collaborative awareness"""
            try:
                session_id = request.sid
                
                if session_id not in cls._active_users:
                    return
                
                batch_id = cls._active_users[session_id].get('current_batch')
                if not batch_id:
                    return
                
                user_info = cls._active_users[session_id]
                cursor_data = {
                    'user_id': user_info['user_id'],
                    'username': user_info['username'],
                    'x': data.get('x'),
                    'y': data.get('y'),
                    'node_id': data.get('node_id'),
                    'timestamp': time.time()
                }
                
                # Store cursor position
                cls._user_cursors[session_id] = cursor_data
                
                # Broadcast to other users in the same batch
                emit('cursor_moved', cursor_data, 
                     room=f"batch_{batch_id}", include_self=False)
                
            except Exception as e:
                current_app.logger.error(f"Cursor update error: {e}")
        
        @socketio.on('interaction_event')
        def handle_interaction_event(data):
            """Handle user interaction events (zoom, layout change, etc.)"""
            try:
                session_id = request.sid
                
                if session_id not in cls._active_users:
                    return
                
                batch_id = cls._active_users[session_id].get('current_batch')
                if not batch_id:
                    return
                
                user_info = cls._active_users[session_id]
                interaction_data = {
                    'user_id': user_info['user_id'],
                    'username': user_info['username'],
                    'type': data.get('type'),
                    'data': data.get('data', {}),
                    'timestamp': time.time()
                }
                
                # Broadcast interaction to other users in the same batch
                emit('user_interaction', interaction_data, 
                     room=f"batch_{batch_id}", include_self=False)
                
                current_app.logger.debug(f"Interaction {data.get('type')} by {user_info['username']} in batch {batch_id}")
                
            except Exception as e:
                current_app.logger.error(f"Interaction event error: {e}")
        
        @socketio.on('request_sync')
        def handle_sync_request(data):
            """Handle request for data synchronization"""
            try:
                session_id = request.sid
                
                if session_id not in cls._active_users:
                    return
                
                batch_id = data.get('batch_id')
                if not batch_id:
                    return
                
                # Get current state from the most recent user in the batch
                current_state = cls._get_batch_current_state(batch_id)
                
                emit('sync_response', {
                    'batch_id': batch_id,
                    'state': current_state,
                    'timestamp': time.time()
                })
                
            except Exception as e:
                current_app.logger.error(f"Sync request error: {e}")
                emit('error', {'message': 'Failed to sync data'})
    
    @classmethod
    def _leave_batch_room(cls, session_id, batch_id):
        """Helper method to handle leaving a batch room"""
        if not batch_id:
            return
        
        leave_room(f"batch_{batch_id}")
        
        # Update batch viewers
        if batch_id in cls._batch_viewers:
            cls._batch_viewers[batch_id].discard(session_id)
            if not cls._batch_viewers[batch_id]:
                del cls._batch_viewers[batch_id]
        
        # Update user's current batch
        if session_id in cls._active_users:
            cls._active_users[session_id]['current_batch'] = None
            user_info = cls._active_users[session_id]
            
            # Notify others in the batch room
            emit('user_left_batch', {
                'user_id': user_info['user_id'],
                'username': user_info['username'],
                'batch_id': batch_id,
                'viewer_count': len(cls._batch_viewers.get(batch_id, []))
            }, room=f"batch_{batch_id}")
            
            current_app.logger.info(f"User {user_info['username']} left batch {batch_id}")
    
    @classmethod
    def _get_batch_current_state(cls, batch_id):
        """Get current state of a batch from active viewers"""
        # This would typically return the current visualization state
        # For now, return basic information
        return {
            'layout': 'hierarchical',
            'zoom_level': 1.0,
            'center_node': None,
            'highlighted_paths': False
        }
    
    @classmethod
    def get_active_users_for_batch(cls, batch_id):
        """Get list of active users viewing a specific batch"""
        active_users = []
        
        if batch_id in cls._batch_viewers:
            for session_id in cls._batch_viewers[batch_id]:
                if session_id in cls._active_users:
                    user_info = cls._active_users[session_id]
                    active_users.append({
                        'user_id': user_info['user_id'],
                        'username': user_info['username'],
                        'connected_at': user_info['connected_at']
                    })
        
        return active_users
    
    @classmethod
    def get_collaboration_stats(cls):
        """Get real-time collaboration statistics"""
        total_active = len(cls._active_users)
        batches_with_multiple_viewers = sum(
            1 for viewers in cls._batch_viewers.values() if len(viewers) > 1
        )
        
        return {
            'total_active_users': total_active,
            'total_batch_rooms': len(cls._batch_viewers),
            'collaborative_batches': batches_with_multiple_viewers,
            'active_cursors': len(cls._user_cursors)
        }
    
    @classmethod
    def broadcast_batch_update(cls, batch_id, update_type, data):
        """Broadcast an update to all users viewing a specific batch"""
        try:
            from flask_socketio import SocketIO
            
            # This would be called when batch data changes
            socketio = current_app.extensions.get('socketio')
            if socketio:
                socketio.emit('batch_updated', {
                    'batch_id': batch_id,
                    'update_type': update_type,
                    'data': data,
                    'timestamp': time.time()
                }, room=f"batch_{batch_id}")
                
        except Exception as e:
            current_app.logger.error(f"Broadcast batch update error: {e}")
    
    @classmethod
    def notify_user_action(cls, user_id, batch_id, action, metadata=None):
        """Notify other users about a user's action"""
        try:
            from flask_socketio import SocketIO
            
            socketio = current_app.extensions.get('socketio')
            if socketio:
                # Find user session
                user_session = None
                for session_id, user_info in cls._active_users.items():
                    if user_info['user_id'] == user_id:
                        user_session = user_info
                        break
                
                if user_session:
                    socketio.emit('user_action_notification', {
                        'user_id': user_id,
                        'username': user_session['username'],
                        'batch_id': batch_id,
                        'action': action,
                        'metadata': metadata or {},
                        'timestamp': time.time()
                    }, room=f"batch_{batch_id}")
                    
        except Exception as e:
            current_app.logger.error(f"User action notification error: {e}")


# Enhanced WebSocket middleware for App Engine compatibility
class AppEngineWebSocketService:
    """
    App Engine compatible WebSocket alternative using Server-Sent Events (SSE)
    For environments where WebSocket is not available
    """
    
    # Event store for SSE
    _event_store = {}  # user_id -> list of events
    _max_events_per_user = 50
    
    @classmethod
    def add_event(cls, user_id, event_type, data):
        """Add an event for a specific user"""
        if user_id not in cls._event_store:
            cls._event_store[user_id] = []
        
        event = {
            'id': f"{int(time.time() * 1000)}_{len(cls._event_store[user_id])}",
            'type': event_type,
            'data': data,
            'timestamp': time.time()
        }
        
        cls._event_store[user_id].append(event)
        
        # Cleanup old events
        if len(cls._event_store[user_id]) > cls._max_events_per_user:
            cls._event_store[user_id] = cls._event_store[user_id][-cls._max_events_per_user:]
    
    @classmethod
    def get_events(cls, user_id, last_event_id=None):
        """Get events for a user since last_event_id"""
        if user_id not in cls._event_store:
            return []
        
        events = cls._event_store[user_id]
        
        if last_event_id:
            # Find events after the last_event_id
            try:
                last_timestamp = int(last_event_id.split('_')[0])
                events = [e for e in events if int(e['id'].split('_')[0]) > last_timestamp]
            except (ValueError, IndexError):
                # If parsing fails, return all events
                pass
        
        return events
    
    @classmethod
    def broadcast_to_batch_viewers(cls, batch_id, event_type, data):
        """Broadcast event to all users viewing a batch"""
        # This would require tracking batch viewers
        # For now, implement basic functionality
        for user_id in cls._event_store.keys():
            cls.add_event(user_id, event_type, {
                'batch_id': batch_id,
                **data
            })
    
    @classmethod
    def cleanup_old_events(cls, max_age_hours=24):
        """Cleanup events older than max_age_hours"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        for user_id in list(cls._event_store.keys()):
            cls._event_store[user_id] = [
                e for e in cls._event_store[user_id] 
                if e['timestamp'] > cutoff_time
            ]
            
            # Remove empty user stores
            if not cls._event_store[user_id]:
                del cls._event_store[user_id]