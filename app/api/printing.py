"""
API endpoints for centralized printing functionality
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime
import logging
from functools import wraps
from .. import db

# Create the services directory if it doesn't exist
import os
services_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'services')
if not os.path.exists(services_dir):
    os.makedirs(services_dir)

# Import the printing service
try:
    from ..services.printing_service import printing_service
except ImportError:
    # Create a fallback if the service isn't available
    class FallbackPrintingService:
        def is_available(self):
            return False
        def queue_print_job(self, *args, **kwargs):
            return None
        def print_vial_labels(self, *args, **kwargs):
            return []
        def get_job_status(self, *args, **kwargs):
            return None
        def get_print_stats(self, *args, **kwargs):
            return None
    printing_service = FallbackPrintingService()

logger = logging.getLogger(__name__)

# Create blueprint
printing_api = Blueprint('printing_api', __name__, url_prefix='/api/print')


def require_api_token(f):
    """Decorator to require API token for print server endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_token = current_app.config.get('PRINT_API_TOKEN', '')
        
        # If no token is configured, allow access (for development)
        if not api_token:
            logger.warning("API token not configured - allowing access")
            return f(*args, **kwargs)
        
        # Check Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Bearer token required'}), 401
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        if token != api_token:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


@printing_api.route('/status', methods=['GET'])
@login_required
def print_service_status():
    """Check if the print service is available"""
    try:
        from ..cell_storage.models import PrintServer, PrintJob
        
        available = printing_service.is_available()
        
        # Get online servers
        online_servers = PrintServer.query.filter_by(status='online').all()
        online_count = len([s for s in online_servers if s.is_online])
        
        # Get job statistics
        pending_jobs = PrintJob.query.filter_by(status='pending').count()
        processing_jobs = PrintJob.query.filter_by(status='processing').count()
        total_jobs = PrintJob.query.count()
        
        return jsonify({
            'available': available,
            'online_servers': online_count,
            'total_servers': len(online_servers),
            'pending_jobs': pending_jobs,
            'processing_jobs': processing_jobs,
            'total_jobs': total_jobs,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error checking print service status: {e}")
        return jsonify({
            'available': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@printing_api.route('/queue-job', methods=['POST'])
@login_required  
def queue_print_job():
    """Queue a single print job"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        label_data = data.get('label_data')
        priority = data.get('priority', 'normal')
        
        if not label_data:
            return jsonify({'error': 'label_data is required'}), 400
        
        # Add user information to label data
        label_data['requested_by'] = current_user.username
        label_data['requested_by_id'] = current_user.id
        
        job = printing_service.queue_print_job(label_data, priority)
        
        if job:
            return jsonify({
                'job_id': job.id,
                'status': job.status,
                'message': 'Print job queued successfully'
            }), 201
        else:
            return jsonify({'error': 'Failed to queue print job'}), 500
            
    except Exception as e:
        logger.error(f"Error queuing print job: {e}")
        return jsonify({'error': str(e)}), 500


@printing_api.route('/queue-batch-labels', methods=['POST'])
@login_required
def queue_batch_labels():
    """Queue print jobs for all vials in a batch"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        batch_name = data.get('batch_name')
        batch_id = data.get('batch_id')
        vial_positions = data.get('vial_positions', [])
        
        if not batch_name or not batch_id or not vial_positions:
            return jsonify({'error': 'batch_name, batch_id, and vial_positions are required'}), 400
        
        jobs = printing_service.print_vial_labels(batch_name, batch_id, vial_positions)
        
        # Count successful jobs
        successful_jobs = [job for job in jobs if job is not None]
        failed_count = len(jobs) - len(successful_jobs)
        
        response_data = {
            'total_jobs': len(jobs),
            'successful_jobs': len(successful_jobs),
            'failed_jobs': failed_count,
            'jobs': [job.to_dict() if job else None for job in jobs]
        }
        
        if successful_jobs:
            return jsonify(response_data), 201
        else:
            return jsonify({
                **response_data,
                'error': 'All print jobs failed'
            }), 500
            
    except Exception as e:
        logger.error(f"Error queuing batch labels: {e}")
        return jsonify({'error': str(e)}), 500


@printing_api.route('/job/<int:job_id>/status', methods=['GET'])
@login_required
def get_job_status(job_id):
    """Get the status of a specific print job"""
    try:
        status = printing_service.get_job_status(job_id)
        
        if status:
            return jsonify(status)
        else:
            return jsonify({'error': 'Job not found or service unavailable'}), 404
            
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return jsonify({'error': str(e)}), 500


@printing_api.route('/stats', methods=['GET'])
@login_required
def get_print_stats():
    """Get printing statistics"""
    try:
        from ..cell_storage.models import PrintServer, PrintJob
        
        # Job statistics
        total_jobs = PrintJob.query.count()
        pending_jobs = PrintJob.query.filter_by(status='pending').count()
        processing_jobs = PrintJob.query.filter_by(status='processing').count()
        completed_jobs = PrintJob.query.filter_by(status='completed').count()
        failed_jobs = PrintJob.query.filter_by(status='failed').count()
        
        # Server statistics
        total_servers = PrintServer.query.count()
        online_servers = PrintServer.query.filter_by(status='online').all()
        online_count = len([s for s in online_servers if s.is_online])
        
        return jsonify({
            'jobs': {
                'total': total_jobs,
                'pending': pending_jobs,
                'processing': processing_jobs,
                'completed': completed_jobs,
                'failed': failed_jobs,
                'success_rate': round((completed_jobs / total_jobs * 100), 2) if total_jobs > 0 else 0
            },
            'servers': {
                'total': total_servers,
                'online': online_count,
                'offline': total_servers - online_count
            }
        })
            
    except Exception as e:
        logger.error(f"Error getting print stats: {e}")
        return jsonify({'error': str(e)}), 500


# Print server endpoints (for print servers to communicate with backend)
@printing_api.route('/fetch-pending-job', methods=['GET'])
@require_api_token
def fetch_pending_job():
    """Fetch next pending print job for print server"""
    try:
        from ..cell_storage.models import PrintJob
        
        server_id = request.args.get('server_id')
        if not server_id:
            return jsonify({'error': 'server_id required'}), 400
        
        # Get next pending job (FIFO with priority)
        job = PrintJob.query.filter_by(status='pending').order_by(
            PrintJob.priority.desc(),  # Higher priority first
            PrintJob.created_at.asc()  # Then FIFO
        ).first()
        
        if job:
            return jsonify({'job': job.to_dict()})
        else:
            return jsonify({'job': None})
            
    except Exception as e:
        logger.error(f"Error fetching pending job: {e}")
        return jsonify({'error': str(e)}), 500


@printing_api.route('/update-job-status/<int:job_id>', methods=['POST'])
@require_api_token
def update_job_status(job_id):
    """Update job status from print server, now including batch information."""
    try:
        from ..cell_storage.models import PrintJob, PrintServer, Batch
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        server_id = data.get('server_id')
        status = data.get('status')
        error_message = data.get('error_message')
        batch_id = data.get('batch_id')
        batch_name = data.get('batch_name')

        if not server_id or not status:
            return jsonify({'error': 'server_id and status are required'}), 400

        if not batch_id or not batch_name:
            return jsonify({'error': 'batch_id and batch_name are required'}), 400

        job = PrintJob.query.get_or_404(job_id)
        
        # Link to the batch if not already linked
        if not job.batch_id:
            batch = Batch.query.get(batch_id)
            if batch:
                job.batch_id = batch.id
            else:
                # Optional: handle case where batch_id is invalid
                logger.warning(f"Batch with ID {batch_id} not found for job {job_id}")

        # Update job status
        job.status = status
        job.print_server_id = server_id
        
        if status == 'processing':
            job.started_at = datetime.now()
        elif status in ['completed', 'failed']:
            job.completed_at = datetime.now()
            if error_message:
                job.error_message = error_message
        
        # Update server statistics
        server = PrintServer.query.filter_by(server_id=server_id).first()
        if server:
            if status == 'completed':
                server.successful_jobs += 1
            elif status == 'failed':
                server.failed_jobs += 1
            
            if status in ['completed', 'failed']:
                server.total_jobs_processed += 1
        
        db.session.commit()
        
        return jsonify({'message': 'Job status updated successfully', 'job': job.to_dict()})
        
    except Exception as e:
        logger.error(f"Error updating job status for job {job_id}: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': 'An internal error occurred', 'details': str(e)}), 500


@printing_api.route('/heartbeat', methods=['POST'])
@require_api_token
def print_server_heartbeat():
    """Receive heartbeat from print server"""
    try:
        from ..cell_storage.models import PrintServer
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        server_id = data.get('server_id')
        if not server_id:
            return jsonify({'error': 'server_id required'}), 400
        
        # Find or create server record
        server = PrintServer.query.filter_by(server_id=server_id).first()
        if not server:
            server = PrintServer(
                server_id=server_id,
                name=data.get('server_name', server_id),
                location=data.get('location', ''),
                status='online'
            )
            db.session.add(server)
        else:
            server.status = 'online'
            server.name = data.get('server_name', server.name)
            server.location = data.get('location', server.location)
        
        server.last_heartbeat = datetime.now()
        db.session.commit()
        
        return jsonify({'message': 'Heartbeat received'})
        
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@printing_api.route('/register-server', methods=['POST'])
@require_api_token
def register_print_server():
    """Register a new print server"""
    try:
        from ..cell_storage.models import PrintServer
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        server_id = data.get('server_id')
        if not server_id:
            return jsonify({'error': 'server_id required'}), 400
        
        # Check if server already exists
        existing_server = PrintServer.query.filter_by(server_id=server_id).first()
        if existing_server:
            # Update existing server
            existing_server.name = data.get('name', existing_server.name)
            existing_server.location = data.get('location', existing_server.location)
            existing_server.status = 'online'
            existing_server.last_heartbeat = datetime.now()
            capabilities = data.get('capabilities', {})
            if capabilities:
                existing_server.printer_types = json.dumps(capabilities.get('printer_types', []))
                existing_server.max_concurrent_jobs = capabilities.get('max_concurrent_jobs', 1)
            server = existing_server
        else:
            # Create new server
            capabilities = data.get('capabilities', {})
            server = PrintServer(
                server_id=server_id,
                name=data.get('name', server_id),
                location=data.get('location', ''),
                status='online',
                last_heartbeat=datetime.now(),
                printer_types=json.dumps(capabilities.get('printer_types', [])),
                max_concurrent_jobs=capabilities.get('max_concurrent_jobs', 1)
            )
            db.session.add(server)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Server registered successfully',
            'server': server.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error registering server: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Error handlers - removed 400 handler to allow specific error messages
@printing_api.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Authentication required'}), 401


@printing_api.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Access forbidden'}), 403


@printing_api.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404


@printing_api.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
