# app/shared/storage_sync.py

"""
Storage Synchronization Service
Synchronizes vial counts from cell_storage system to inventory locations
"""

from .. import db
from ..cell_storage.models import Tower, Drawer, Box, CryoVial
from ..inventory.models import Location, InventoryItem
from sqlalchemy import or_


class StorageSyncService:
    """Service to synchronize storage data between cell_storage and inventory systems."""
    
    @staticmethod
    def sync_all_locations():
        """Sync all storage locations from cell_storage to inventory system."""
        try:
            synced_count = 0
            
            # Sync towers
            towers = Tower.query.all()
            for tower in towers:
                location = StorageSyncService._sync_tower(tower)
                if location:
                    synced_count += 1
                    
                    # Sync drawers for this tower
                    for drawer in tower.drawers:
                        drawer_location = StorageSyncService._sync_drawer(drawer, location.id)
                        if drawer_location:
                            synced_count += 1
                            
                            # Sync boxes for this drawer
                            for box in drawer.boxes:
                                box_location = StorageSyncService._sync_box(box, drawer_location.id)
                                if box_location:
                                    synced_count += 1
            
            db.session.commit()
            return synced_count
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def _sync_tower(tower):
        """Sync a single tower to inventory locations."""
        # Find or create corresponding location
        location = Location.query.filter_by(
            name=tower.name,
            location_type='tower',
            parent_id=None
        ).first()
        
        if not location:
            location = Location(
                name=tower.name,
                location_type='tower',
                description=f'Freezer tower - {tower.description or ""}',
                temperature=tower.temperature,
                max_capacity=None,  # Towers don't have direct capacity limits
                current_usage=0
            )
            db.session.add(location)
            db.session.flush()  # Get ID
        
        # Update location properties
        location.temperature = tower.temperature
        location.description = f'Freezer tower - {tower.description or ""}'
        
        # Update usage count (sum of all vials in this tower)
        vial_count = CryoVial.query.join(Box).join(Drawer).filter(
            Drawer.tower_id == tower.id,
            CryoVial.status == 'Available'
        ).count()
        location.current_usage = vial_count
        
        return location
    
    @staticmethod
    def _sync_drawer(drawer, parent_location_id):
        """Sync a single drawer to inventory locations."""
        location = Location.query.filter_by(
            name=drawer.name,
            location_type='drawer',
            parent_id=parent_location_id
        ).first()
        
        if not location:
            location = Location(
                name=drawer.name,
                location_type='drawer', 
                parent_id=parent_location_id,
                description=f'Freezer drawer in {drawer.tower_info.name}',
                temperature=drawer.tower_info.temperature,
                max_capacity=None,  # Drawers don't have direct capacity limits
                current_usage=0
            )
            db.session.add(location)
            db.session.flush()
        
        # Update usage count (sum of all vials in this drawer)
        vial_count = CryoVial.query.join(Box).filter(
            Box.drawer_id == drawer.id,
            CryoVial.status == 'Available'
        ).count()
        location.current_usage = vial_count
        
        return location
    
    @staticmethod
    def _sync_box(box, parent_location_id):
        """Sync a single box to inventory locations."""
        location = Location.query.filter_by(
            name=box.name,
            location_type='box',
            parent_id=parent_location_id
        ).first()
        
        if not location:
            location = Location(
                name=box.name,
                location_type='box',
                parent_id=parent_location_id,
                description=f'Storage box ({box.rows}x{box.columns}) in {box.drawer_info.tower_info.name}/{box.drawer_info.name}',
                temperature=box.drawer_info.tower_info.temperature,
                max_capacity=box.rows * box.columns,
                capacity_unit='vials',
                current_usage=0
            )
            db.session.add(location)
            db.session.flush()
        
        # Update capacity and usage
        location.max_capacity = box.rows * box.columns
        location.capacity_unit = 'vials'
        
        # Count available vials in this box
        vial_count = CryoVial.query.filter_by(
            box_id=box.id,
            status='Available'
        ).count()
        location.current_usage = vial_count
        
        return location
    
    @staticmethod
    def update_box_usage(box_id):
        """Update usage count for a specific box after vial status changes."""
        box = Box.query.get(box_id)
        if not box:
            return False
            
        # Find corresponding inventory location
        location = Location.query.filter_by(
            name=box.name,
            location_type='box',
        ).join(Location, Location.id == Location.parent_id).filter(
            Location.name == box.drawer_info.name,
            Location.location_type == 'drawer'
        ).join(Location, Location.id == Location.parent_id).filter(
            Location.name == box.drawer_info.tower_info.name,
            Location.location_type == 'tower'
        ).first()
        
        if not location:
            # Location doesn't exist, create it through full sync
            StorageSyncService._sync_box(box, box.drawer_info.id)
            return True
        
        # Update current usage count
        vial_count = CryoVial.query.filter_by(
            box_id=box_id,
            status='Available'
        ).count()
        
        location.current_usage = vial_count
        
        # Also update parent drawer and tower counts
        StorageSyncService._update_parent_usage(location)
        
        try:
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    @staticmethod
    def _update_parent_usage(location):
        """Update usage counts for parent locations."""
        if location.parent:
            parent = location.parent
            
            # Sum up current usage from all children
            total_usage = sum(child.current_usage or 0 for child in parent.children)
            parent.current_usage = total_usage
            
            # Recursively update grandparents
            StorageSyncService._update_parent_usage(parent)
    
    @staticmethod
    def sync_after_vial_pickup(vial_ids):
        """Sync location usage after vials are picked up."""
        if not vial_ids:
            return
            
        # Get all affected boxes
        affected_boxes = db.session.query(Box.id).join(CryoVial).filter(
            CryoVial.id.in_(vial_ids)
        ).distinct().all()
        
        # Update usage for each affected box
        for (box_id,) in affected_boxes:
            StorageSyncService.update_box_usage(box_id)
    
    @staticmethod
    def get_sync_status():
        """Get synchronization status between the two systems."""
        cell_storage_stats = {
            'towers': Tower.query.count(),
            'drawers': Drawer.query.count(), 
            'boxes': Box.query.count(),
            'total_vials': CryoVial.query.count(),
            'available_vials': CryoVial.query.filter_by(status='Available').count()
        }
        
        inventory_stats = {
            'tower_locations': Location.query.filter_by(location_type='tower').count(),
            'drawer_locations': Location.query.filter_by(location_type='drawer').count(),
            'box_locations': Location.query.filter_by(location_type='box').count(),
            'total_usage': db.session.query(db.func.sum(Location.current_usage)).scalar() or 0
        }
        
        return {
            'cell_storage': cell_storage_stats,
            'inventory': inventory_stats,
            'synced': (
                cell_storage_stats['towers'] == inventory_stats['tower_locations'] and
                cell_storage_stats['drawers'] == inventory_stats['drawer_locations'] and  
                cell_storage_stats['boxes'] == inventory_stats['box_locations']
            )
        }