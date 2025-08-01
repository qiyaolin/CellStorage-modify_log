"""
Centralized Label Printing Service
Backend service for managing print job queue that print servers monitor.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import current_app
from .. import db

logger = logging.getLogger(__name__)


class PrintJob:
    """Represents a single print job in the database"""
    
    def __init__(self, label_data: Dict[str, Any], priority: str = 'normal', job_id: Optional[int] = None):
        self.job_id = job_id
        self.label_data = label_data
        self.priority = priority
        self.status = 'pending'
        self.created_at = datetime.now()
        self.error_message = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.job_id,
            'label_data': self.label_data,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'error_message': self.error_message
        }


class PrintingService:
    """Backend printing service - manages job queue for print servers"""
    
    def __init__(self):
        self._enabled = None
    
    @property
    def enabled(self) -> bool:
        """Lazily load the enabled configuration from Flask app config"""
        if self._enabled is None:
            try:
                self._enabled = current_app.config.get('CENTRALIZED_PRINTING_ENABLED', False)
            except RuntimeError:
                # No application context available, default to False
                self._enabled = False
        return self._enabled
    
    def is_available(self) -> bool:
        """Check if centralized printing is enabled and database is accessible"""
        if not self.enabled:
            return False
            
        try:
            # Simple database check
            from ..cell_storage.models import User
            User.query.first()
            return True
        except Exception as e:
            logger.warning(f"Print service database check failed: {e}")
            return False
    
    def queue_print_job(self, label_data: Dict[str, Any], priority: str = 'normal', user_id: int = None) -> Optional['PrintJob']:
        """Queue a new print job in database"""
        if not self.is_available():
            logger.warning("Print service not available")
            return None
        
        try:
            from ..cell_storage.models import PrintJob as PrintJobModel
            from flask_login import current_user
            
            if user_id is None and current_user and current_user.is_authenticated:
                user_id = current_user.id
            elif user_id is None:
                logger.error("No user ID provided for print job")
                return None
            
            # Create new print job in database
            job = PrintJobModel(
                label_data=json.dumps(label_data),
                priority=priority,
                requested_by=user_id,
                status='pending'
            )
            
            db.session.add(job)
            db.session.commit()
            
            logger.info(f"Print job queued successfully: {job.id}")
            return job
                
        except Exception as e:
            logger.error(f"Error queuing print job: {e}")
            db.session.rollback()
            return None
    
    def print_vial_labels(self, batch_name: str, batch_id: int, vial_positions: List[Dict[str, Any]]) -> List[Optional[PrintJob]]:
        """
        Print labels for multiple vials in a batch.
        Each vial gets its own print job.
        
        Args:
            batch_name: Name of the batch
            batch_id: ID of the batch
            vial_positions: List of vial position info with keys: row, col, box_name, tower_name, drawer_name
        
        Returns:
            List of PrintJob objects (or None for failed jobs)
        """
        jobs = []
        
        for i, position in enumerate(vial_positions, 1):
            label_data = {
                'batch_name': batch_name,
                'batch_id': f"B{batch_id}",
                'vial_number': i,
                'location': f"{position.get('tower_name', '')}/{position.get('drawer_name', '')}/{position.get('box_name', '')}",
                'position': f"R{position.get('row', '')}C{position.get('col', '')}",
                'date_created': datetime.now().strftime('%Y-%m-%d'),
                'label_type': 'vial'
            }
            
            job = self.queue_print_job(label_data, priority='normal')
            jobs.append(job)
            
            if job:
                logger.info(f"Queued print job for vial {i}: Job ID {job.job_id}")
            else:
                logger.error(f"Failed to queue print job for vial {i}")
        
        return jobs
    
    def get_job_status(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get the status of a specific print job"""
        if not self.is_available():
            return None
            
        try:
            response = requests.get(
                f"{self.print_server_url}/api/jobs/{job_id}",
                headers={'Authorization': f'Bearer {self.api_token}'},
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get job status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return None
    
    def get_print_stats(self) -> Optional[Dict[str, int]]:
        """Get printing statistics"""
        if not self.is_available():
            return None
            
        try:
            response = requests.get(
                f"{self.print_server_url}/api/stats",
                headers={'Authorization': f'Bearer {self.api_token}'},
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting print stats: {e}")
            return None


# Global instance
printing_service = PrintingService()