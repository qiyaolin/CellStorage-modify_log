from datetime import datetime, timedelta
import json
from sqlalchemy import text
from .. import db
from ..cell_storage.models import AuditLog, AppConfig, VialBatch, CryoVial

def log_audit(user_id, action, target_type=None, target_id=None, details=None, **extra):
    """Create an ``AuditLog`` entry.

    ``details`` may be a string or dictionary. Any additional keyword
    arguments are captured into the details payload for convenience so
    callers won't accidentally pass unexpected parameters.
    """

    if extra:
        if isinstance(details, dict):
            extra.update(details)
        elif details is not None:
            extra["details"] = details
        details = json.dumps(extra)
    elif isinstance(details, dict):
        details = json.dumps(details)

    log = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.session.add(log)
    db.session.commit()


def clear_database_except_admin():
    """Delete all records except ALL user accounts using robust transaction management.

    Uses raw SQL with proper foreign key handling and individual transactions
    to avoid PostgreSQL transaction abort issues.
    
    Clears ALL business data but preserves ALL user accounts including:
    - Cell Storage: CryoVials, Batches, Cell Lines, Storage Locations
    - Inventory: Items, Orders, Usage Logs, Alerts
    - Configuration: Themes, App Settings, Alerts
    - All audit logs and notifications
    
    PRESERVES: All user accounts (admin and regular users)
    """
    from sqlalchemy import text
    
    # Define deletion order - most dependent tables first
    # Each group will be processed in a separate transaction for reliability
    deletion_groups = [
        {
            'name': 'Usage and Transaction Records',
            'tables': [
                'usage_logs',
                'order_items', 
                'item_price_history',
                'supplier_ratings',
                'audit_logs'
            ]
        },
        {
            'name': 'Orders and Requests',
            'tables': [
                'orders',
                'purchase_requests',
                'shopping_cart'
            ]
        },
        {
            'name': 'Cell Storage Data',
            'tables': [
                'cryovials',
                'alerts'
            ]
        },
        {
            'name': 'Batch and Items Data',
            'tables': [
                'vial_batches',
                'inventory_items',
                'stock_alerts',
                'notifications'
            ]
        },
        {
            'name': 'Location Hierarchy', 
            'tables': [
                'boxes',
                'drawers',
                'towers',
                'locations'  # inventory locations
            ]
        },
        {
            'name': 'Base Reference Data',
            'tables': [
                'cell_lines',
                'supplier_contacts',
                'suppliers',
                'inventory_types'
            ]
        },
        {
            'name': 'Configuration Data',
            'tables': [
                'user_permissions',
                'theme_config', 
                'alert_configs',
                'app_config'
            ]
        }
    ]
    
    success_count = 0
    total_deleted = 0
    errors = []
    
    # Process each group in a separate transaction
    for group in deletion_groups:
        group_name = group['name']
        tables = group['tables']
        group_deleted = 0
        
        try:
            print(f"🔄 Processing {group_name}...")
            
            for table in tables:
                try:
                    # Check if table exists before trying to delete
                    result = db.session.execute(text(
                        f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
                    ))
                    table_exists = result.fetchone()[0]
                    
                    if table_exists:
                        # Delete all records from table
                        result = db.session.execute(text(f"DELETE FROM {table}"))
                        deleted = result.rowcount
                        group_deleted += deleted
                        print(f"  ✅ Cleared {deleted} records from {table}")
                    else:
                        print(f"  ⏭️  Table {table} does not exist, skipping")
                        
                except Exception as e:
                    print(f"  ❌ Error clearing {table}: {e}")
                    errors.append(f"{table}: {str(e)}")
                    # Continue with next table in group
            
            # Commit this group's changes
            db.session.commit()
            total_deleted += group_deleted
            success_count += 1
            print(f"✅ {group_name} completed - {group_deleted} total records deleted")
            
        except Exception as e:
            # Rollback this group's transaction and clean up session
            try:
                db.session.rollback()
            except Exception:
                # If rollback fails, remove the session entirely
                db.session.remove()
            print(f"❌ {group_name} failed: {e}")
            errors.append(f"{group_name}: {str(e)}")
            
    # PRESERVE ALL USERS - Do not delete any user accounts
    print("✅ All user accounts preserved (no users deleted)")
    
    # Verify key tables are actually empty
    key_tables_to_verify = ['cryovials', 'vial_batches', 'cell_lines', 'inventory_items']
    verification_results = {}
    
    for table in key_tables_to_verify:
        try:
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            db.session.commit()  # Ensure clean transaction state
            verification_results[table] = count
        except Exception as e:
            verification_results[table] = f"Error: {e}"
            try:
                db.session.rollback()
            except Exception:
                pass
    
    # Final summary
    if success_count == len(deletion_groups):
        print(f"✅ Database cleared successfully!")
        print(f"   📊 {success_count}/{len(deletion_groups)} groups processed")
        print(f"   📊 {total_deleted} total records deleted")
        print(f"   🛡️  All user accounts preserved")
    else:
        print(f"⚠️  Database clearing completed with some errors:")
        print(f"   📊 {success_count}/{len(deletion_groups)} groups successful")
        print(f"   📊 {total_deleted} total records deleted")
        print(f"   🛡️  All user accounts preserved")
        if errors:
            print("   ❌ Errors encountered:")
            for error in errors:
                print(f"      - {error}")
    
    # Print verification results
    print(f"\n🔍 Table verification (record counts):")
    for table, count in verification_results.items():
        if isinstance(count, int):
            status = "✅ Empty" if count == 0 else f"⚠️  {count} records remaining"
            print(f"   {table}: {status}")
        else:
            print(f"   {table}: {count}")
    
    # Reset sequences for key tables to start from 1
    sequences_to_reset = [
        ('cryovials', 'cryovials_id_seq'),
        ('vial_batches', 'vial_batches_id_seq'), 
        ('cell_lines', 'cell_lines_id_seq'),
        ('inventory_items', 'inventory_items_id_seq'),
        ('boxes', 'boxes_id_seq'),
        ('drawers', 'drawers_id_seq'),
        ('towers', 'towers_id_seq')
    ]
    
    print(f"\n🔄 Resetting ID sequences...")
    reset_count = 0
    for table, sequence in sequences_to_reset:
        try:
            # Check if table exists first
            result = db.session.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
            ))
            if result.fetchone()[0]:
                db.session.execute(text(f"ALTER SEQUENCE {sequence} RESTART WITH 1"))
                db.session.commit()  # Commit each sequence reset individually
                print(f"   ✅ Reset {sequence} to start from 1")
                reset_count += 1
            else:
                print(f"   ⏭️  Table {table} does not exist, skipping sequence reset")
        except Exception as e:
            print(f"   ⚠️  Could not reset {sequence}: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass
    
    if reset_count > 0:
        print(f"✅ {reset_count} sequences reset successfully")
    else:
        print("ℹ️  No sequences to reset")
    
    # CRITICAL: Clean up the session completely to avoid transaction state issues
    # This ensures subsequent operations (like user authentication) start fresh
    try:
        db.session.remove()
        print("🧹 Database session cleaned up successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not clean up database session: {e}")
    
    return success_count == len(deletion_groups)


def get_vial_counter():
    """Return current vial counter as int, ensuring sync with PostgreSQL sequence."""
    try:
        # 获取 PostgreSQL 序列的当前值
        result = db.session.execute(text("SELECT last_value FROM cryovials_id_seq")).fetchone()
        sequence_value = result[0] if result else 0
        
        # 获取 AppConfig 中的值
        setting = AppConfig.query.filter_by(key='vial_counter').first()
        
        if not setting:
            # 初始化：基于当前最大 ID 或序列值
            max_id = db.session.query(db.func.max(CryoVial.id)).scalar() or 0
            next_value = max(max_id + 1, sequence_value + 1)
            setting = AppConfig(key='vial_counter', value=str(next_value))
            db.session.add(setting)
            # 同步序列值
            db.session.execute(text(f"ALTER SEQUENCE cryovials_id_seq RESTART WITH {next_value}"))
            db.session.commit()
            return next_value
        
        # 检查 AppConfig 和序列是否同步
        config_value = int(setting.value)
        if abs(config_value - sequence_value) > 1:  # 允许1的差异（序列可能已经被使用）
            # 不同步时，以序列值为准，更新 AppConfig
            next_value = sequence_value + 1
            setting.value = str(next_value)
            db.session.commit()
            return next_value
        
        return config_value
        
    except (ValueError, TypeError):
        return 1
    except Exception as e:
        # 发生错误时，回退到基于最大 ID 的方式
        max_id = db.session.query(db.func.max(CryoVial.id)).scalar() or 0
        return max_id + 1


def set_vial_counter(value):
    """Set vial counter and update PostgreSQL sequence to match"""
    try:
        new_value = int(value)
        if new_value < 1:
            raise ValueError("Vial counter must be a positive integer")
        
        # 更新 AppConfig 中的计数器值
        setting = AppConfig.query.filter_by(key='vial_counter').first()
        if not setting:
            setting = AppConfig(key='vial_counter')
            db.session.add(setting)
        setting.value = str(new_value)
        
        # 同时更新 PostgreSQL 序列，让下一个 ID 从指定值开始
        db.session.execute(text(f"ALTER SEQUENCE cryovials_id_seq RESTART WITH {new_value}"))
        db.session.commit()
        
    except (ValueError, TypeError) as e:
        db.session.rollback()
        raise ValueError(f"Invalid vial counter value: {e}")
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Failed to update vial counter: {e}")


def get_next_vial_id(auto_commit=True):
    """
    这个函数已经不再需要，因为 CryoVial 的 id 现在由 PostgreSQL 序列自动管理。
    保留此函数是为了向后兼容，但实际上 vial 的 ID 将由数据库自动分配。
    """
    # 获取当前的 vial_counter 值（这只是为了显示目的）
    return get_vial_counter()


def get_batch_counter():
    """Return current batch counter as int, initializing if missing."""
    setting = AppConfig.query.filter_by(key='batch_counter').first()
    if not setting:
        # initialize based on current max batch id
        max_id = db.session.query(db.func.max(VialBatch.id)).scalar() or 0
        setting = AppConfig(key='batch_counter', value=str(max_id + 1))
        db.session.add(setting)
        db.session.commit()
    try:
        return int(setting.value)
    except (ValueError, TypeError):
        return 1


def set_batch_counter(value):
    setting = AppConfig.query.filter_by(key='batch_counter').first()
    if not setting:
        setting = AppConfig(key='batch_counter')
        db.session.add(setting)
    setting.value = str(int(value))
    db.session.commit()


def get_next_batch_id(auto_commit=True):
    """Retrieve and increment the batch counter atomically using database-level operations."""
    try:
        # Use PostgreSQL's built-in atomic operations for ID generation
        # This prevents race conditions by using database-level locking
        
        # Try to get existing counter setting with row-level lock
        setting = AppConfig.query.filter_by(key='batch_counter').with_for_update().first()
        
        if not setting:
            # Initialize counter based on current max ID
            max_id = db.session.query(db.func.max(VialBatch.id)).scalar() or 0
            setting = AppConfig(key='batch_counter', value=str(max_id + 1))
            db.session.add(setting)
            # Commit immediately to avoid transaction conflicts
            db.session.commit()
            return max_id + 1
        
        # Get current value and increment atomically
        current = int(setting.value)
        setting.value = str(current + 1)
        
        if auto_commit:
            db.session.commit()
        else:
            # For non-auto-commit, we still need to commit the counter update
            # to avoid conflicts, then start a new transaction for the batch creation
            db.session.commit()
            
        return current
        
    except Exception as e:
        # Fallback: generate ID based on current max + timestamp to ensure uniqueness
        import time
        max_id = db.session.query(db.func.max(VialBatch.id)).scalar() or 0
        timestamp_suffix = int(time.time() * 1000) % 10000  # Last 4 digits of timestamp
        fallback_id = max_id + 1 + timestamp_suffix
        
        # Update counter to this value to maintain sequence
        try:
            setting = AppConfig.query.filter_by(key='batch_counter').first()
            if setting:
                setting.value = str(fallback_id + 1)
                if auto_commit:
                    db.session.commit()
        except:
            pass  # Counter update failed, but we have a valid ID
            
        return fallback_id


# =============================================================================
# Alert system related functions
# =============================================================================

def get_default_alert_configs():
    """Get default alert configurations"""
    return {
        'low_stock': {
            'threshold_value': 5,  # Alert when less than 5 available samples
            'is_enabled': True
        },
        'box_capacity': {
            'threshold_value': 80,  # Alert when box usage exceeds 80%
            'is_enabled': True
        },
        'old_samples': {
            'threshold_days': 365,  # Alert when samples exceed 1 year
            'is_enabled': True
        }
    }


def get_alert_config(alert_type, cell_line_id=None):
    """Get alert configuration for specified type"""
    from app.cell_storage.models import AlertConfig
    
    # Priority search for specific cell line configuration
    if cell_line_id:
        config = AlertConfig.query.filter_by(
            alert_type=alert_type, 
            cell_line_id=cell_line_id
        ).first()
        if config:
            return config
    
    # Search for global configuration
    config = AlertConfig.query.filter_by(
        alert_type=alert_type, 
        cell_line_id=None
    ).first()
    
    if not config:
        # Create default configuration
        defaults = get_default_alert_configs()
        if alert_type in defaults:
            config = AlertConfig(
                alert_type=alert_type,
                **defaults[alert_type]
            )
            db.session.add(config)
            db.session.commit()
    
    return config


def check_low_stock_alerts():
    """Check low stock alerts"""
    from app.cell_storage.models import CellLine, CryoVial, Alert
    
    config = get_alert_config('low_stock')
    if not config or not config.is_enabled:
        return []
    
    alerts = []
    threshold = config.threshold_value or 5
    
    # Count available samples by cell line
    cell_lines_stock = db.session.query(
        CellLine.id,
        CellLine.name,
        db.func.count(CryoVial.id).label('available_count')
    ).select_from(CellLine)\
     .outerjoin(CryoVial, (CryoVial.cell_line_id == CellLine.id) & (CryoVial.status == 'Available'))\
     .group_by(CellLine.id, CellLine.name).all()
    
    for cell_line_id, cell_line_name, available_count in cell_lines_stock:
        if available_count < threshold:
            # Check if unresolved alert already exists
            existing_alert = Alert.query.filter_by(
                alert_type='low_stock',
                cell_line_id=cell_line_id,
                is_resolved=False,
                is_dismissed=False
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    alert_type='low_stock',
                    severity='high' if available_count == 0 else 'medium',
                    title=f'Low Stock: {cell_line_name}',
                    message=f'Cell line {cell_line_name} has only {available_count} available samples (threshold: {threshold})',
                    cell_line_id=cell_line_id,
                    extra_data=json.dumps({
                        'current_count': available_count,
                        'threshold': threshold,
                        'cell_line_name': cell_line_name
                    })
                )
                alerts.append(alert)
    
    return alerts


def check_box_capacity_alerts():
    """Check box capacity alerts"""
    from app.cell_storage.models import Box, CryoVial, Alert
    
    config = get_alert_config('box_capacity')
    if not config or not config.is_enabled:
        return []
    
    alerts = []
    threshold_percent = config.threshold_value or 80
    
    # Query usage status of all boxes
    boxes_usage = db.session.query(
        Box.id,
        Box.name,
        Box.rows,
        Box.columns,
        db.func.count(CryoVial.id).label('used_positions')
    ).outerjoin(CryoVial, CryoVial.box_id == Box.id).group_by(Box.id, Box.name, Box.rows, Box.columns).all()
    
    for box_id, box_name, rows, columns, used_positions in boxes_usage:
        total_positions = rows * columns
        usage_percent = (used_positions / total_positions) * 100 if total_positions > 0 else 0
        
        if usage_percent >= threshold_percent:
            # Check if unresolved alert already exists
            existing_alert = Alert.query.filter_by(
                alert_type='box_capacity',
                box_id=box_id,
                is_resolved=False,
                is_dismissed=False
            ).first()
            
            if not existing_alert:
                severity = 'critical' if usage_percent >= 95 else 'high' if usage_percent >= 90 else 'medium'
                alert = Alert(
                    alert_type='box_capacity',
                    severity=severity,
                    title=f'Box Nearly Full: {box_name}',
                    message=f'Box {box_name} is {usage_percent:.1f}% full ({used_positions}/{total_positions} positions)',
                    box_id=box_id,
                    extra_data=json.dumps({
                        'usage_percent': round(usage_percent, 1),
                        'used_positions': used_positions,
                        'total_positions': total_positions,
                        'threshold_percent': threshold_percent,
                        'box_name': box_name
                    })
                )
                alerts.append(alert)
    
    return alerts


def check_old_samples_alerts():
    """Check old sample alerts"""
    from app.cell_storage.models import CryoVial, Alert, CellLine, VialBatch
    
    config = get_alert_config('old_samples')
    if not config or not config.is_enabled:
        return []
    
    alerts = []
    threshold_days = config.threshold_days or 365
    cutoff_date = datetime.utcnow().date() - timedelta(days=threshold_days)
    
    # Query samples exceeding threshold days
    old_vials = db.session.query(
        VialBatch.id,
        VialBatch.name,
        CellLine.name.label('cell_line_name'),
        db.func.min(CryoVial.date_frozen).label('oldest_date'),
        db.func.count(CryoVial.id).label('vial_count')
    ).join(CryoVial, CryoVial.batch_id == VialBatch.id).join(CellLine, CellLine.id == CryoVial.cell_line_id)\
     .filter(CryoVial.date_frozen <= cutoff_date)\
     .filter(CryoVial.status == 'Available')\
     .group_by(VialBatch.id, VialBatch.name, CellLine.name).all()
    
    for batch_id, batch_name, cell_line_name, oldest_date, vial_count in old_vials:
        days_old = (datetime.utcnow().date() - oldest_date).days
        
        # 检查是否已存在未解决的预警
        existing_alert = Alert.query.filter_by(
            alert_type='old_samples',
            batch_id=batch_id,
            is_resolved=False,
            is_dismissed=False
        ).first()
        
        if not existing_alert:
            severity = 'high' if days_old > threshold_days * 1.5 else 'medium'
            alert = Alert(
                alert_type='old_samples',
                severity=severity,
                title=f'Old Samples: {batch_name}',
                message=f'Batch {batch_name} ({cell_line_name}) contains {vial_count} samples that are {days_old} days old',
                batch_id=batch_id,
                extra_data=json.dumps({
                    'days_old': days_old,
                    'threshold_days': threshold_days,
                    'vial_count': vial_count,
                    'batch_name': batch_name,
                    'cell_line_name': cell_line_name
                })
            )
            alerts.append(alert)
    
    return alerts


def generate_all_alerts():
    """Generate all types of alerts"""
    alerts = []
    
    # Import timedelta
    from datetime import timedelta
    
    # Check various types of alerts
    alerts.extend(check_low_stock_alerts())
    alerts.extend(check_box_capacity_alerts())
    alerts.extend(check_old_samples_alerts())
    
    # Batch save new alerts
    if alerts:
        for alert in alerts:
            db.session.add(alert)
        db.session.commit()
    
    return len(alerts)


def get_active_alerts(limit=None):
    """Get active alerts"""
    from app.cell_storage.models import Alert
    
    query = Alert.query.filter_by(is_resolved=False, is_dismissed=False)\
                      .order_by(Alert.created_at.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def resolve_alert(alert_id, user_id, commit=True):
    """Resolve alert"""
    from app.cell_storage.models import Alert
    
    alert = Alert.query.get(alert_id)
    if alert and not alert.is_resolved:
        alert.is_resolved = True
        alert.resolved_by_user_id = user_id
        alert.resolved_at = datetime.utcnow()
        
        if commit:
            db.session.commit()
        
        # Record audit log
        log_audit(
            user_id=user_id,
            action='RESOLVE_ALERT',
            target_type='Alert',
            target_id=alert_id,
            details={'alert_type': alert.alert_type, 'title': alert.title}
        )
    
    return alert


def dismiss_alert(alert_id, user_id, commit=True):
    """Dismiss alert"""
    from app.cell_storage.models import Alert
    
    alert = Alert.query.get(alert_id)
    if alert and not alert.is_dismissed:
        alert.is_dismissed = True
        alert.dismissed_at = datetime.utcnow()
        
        if commit:
            db.session.commit()
        
        # Record audit log
        log_audit(
            user_id=user_id,
            action='DISMISS_ALERT',
            target_type='Alert',
            target_id=alert_id,
            details={'alert_type': alert.alert_type, 'title': alert.title}
        )
    
    return alert

# === Theme management utility functions ===

def get_available_themes():
    """Get all available theme configurations"""
    return {
        'professional_blue': {
            'name': 'Professional Blue',
            'description': 'Modern corporate blue theme with excellent contrast and readability',
            'primary_color': '#1976D2',
            'secondary_color': '#1565C0',
            'accent_color': '#42A5F5',
            'background_color': '#FAFAFA',
            'text_color': '#212121',
            'navbar_style': 'light'
        },
        'laboratory_green': {
            'name': 'Laboratory Green',
            'description': 'Fresh scientific green theme promoting focus and clarity',
            'primary_color': '#388E3C',
            'secondary_color': '#2E7D32',
            'accent_color': '#66BB6A',
            'background_color': '#F1F8E9',
            'text_color': '#1B5E20',
            'navbar_style': 'light'
        },
        'research_purple': {
            'name': 'Research Purple',
            'description': 'Sophisticated purple theme for innovative research environments',
            'primary_color': '#7B1FA2',
            'secondary_color': '#6A1B9A',
            'accent_color': '#BA68C8',
            'background_color': '#F3E5F5',
            'text_color': '#4A148C',
            'navbar_style': 'light'
        },
        'medical_teal': {
            'name': 'Medical Teal',
            'description': 'Clean medical teal theme ensuring clinical precision and trust',
            'primary_color': '#00796B',
            'secondary_color': '#00695C',
            'accent_color': '#4DB6AC',
            'background_color': '#E0F2F1',
            'text_color': '#004D40',
            'navbar_style': 'light'
        },
        'elegant_navy': {
            'name': 'Elegant Navy',
            'description': 'Professional navy theme conveying authority and trustworthiness',
            'primary_color': '#283593',
            'secondary_color': '#1A237E',
            'accent_color': '#5C6BC0',
            'background_color': '#F5F5F5',
            'text_color': '#1A237E',
            'navbar_style': 'light'
        },
        'warm_orange': {
            'name': 'Warm Orange',
            'description': 'Energizing orange theme that promotes creativity and enthusiasm',
            'primary_color': '#F57C00',
            'secondary_color': '#E65100',
            'accent_color': '#FFB74D',
            'background_color': '#FFF8E1',
            'text_color': '#BF360C',
            'navbar_style': 'light'
        },
        'dark_professional': {
            'name': 'Dark Professional',
            'description': 'Modern dark theme reducing eye strain for extended work sessions',
            'primary_color': '#3F51B5',
            'secondary_color': '#303F9F',
            'accent_color': '#7986CB',
            'background_color': '#121212',
            'text_color': '#E0E0E0',
            'navbar_style': 'dark'
        },
        'high_contrast': {
            'name': 'High Contrast',
            'description': 'Maximum contrast for accessibility compliance',
            'primary_color': '#000000',
            'secondary_color': '#424242',
            'accent_color': '#757575',
            'background_color': '#FFFFFF',
            'text_color': '#000000',
            'navbar_style': 'light'
        },
        'warm_amber': {
            'name': 'Warm Amber',
            'description': 'Comfortable amber theme designed for extended use sessions',
            'primary_color': '#F57C00',
            'secondary_color': '#E65100',
            'accent_color': '#FFB74D',
            'background_color': '#FFF8E1',
            'text_color': '#BF360C',
            'navbar_style': 'light'
        },
        'cool_slate': {
            'name': 'Cool Slate',
            'description': 'Professional slate theme with modern aesthetics',
            'primary_color': '#455A64',
            'secondary_color': '#263238',
            'accent_color': '#78909C',
            'background_color': '#ECEFF1',
            'text_color': '#263238',
            'navbar_style': 'light'
        }
    }

def get_user_theme(user_id):
    """Get user's current theme configuration"""
    from app.cell_storage.models import ThemeConfig
    
    theme_config = ThemeConfig.query.filter_by(user_id=user_id).first()
    if not theme_config:
        # Create default theme configuration
        default_theme = get_available_themes()['professional_blue']
        theme_config = ThemeConfig(
            user_id=user_id,
            theme_name='professional_blue',
            primary_color=default_theme['primary_color'],
            secondary_color=default_theme['secondary_color'],
            accent_color=default_theme['accent_color'],
            background_color=default_theme['background_color'],
            text_color=default_theme['text_color'],
            navbar_style=default_theme['navbar_style']
        )
        db.session.add(theme_config)
        db.session.commit()
    
    return theme_config.to_dict()

def update_user_theme(user_id, theme_name):
    """Update user's theme configuration"""
    from app.cell_storage.models import ThemeConfig
    
    themes = get_available_themes()
    if theme_name not in themes:
        return False, "Theme does not exist"
    
    theme_data = themes[theme_name]
    
    try:
        theme_config = ThemeConfig.query.filter_by(user_id=user_id).first()
        
        if not theme_config:
            theme_config = ThemeConfig(user_id=user_id)
            db.session.add(theme_config)
        
        theme_config.theme_name = theme_name
        theme_config.primary_color = theme_data['primary_color']
        theme_config.secondary_color = theme_data['secondary_color']
        theme_config.accent_color = theme_data['accent_color']
        theme_config.background_color = theme_data['background_color']
        theme_config.text_color = theme_data['text_color']
        theme_config.navbar_style = theme_data['navbar_style']
        
        db.session.commit()
        return True, "Theme updated successfully"
    except Exception as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}"

def get_theme_css_variables(theme_config):
    """Generate CSS variables based on theme configuration"""
    return f"""
    :root {{
        --primary-color: {theme_config['primary_color']};
        --secondary-color: {theme_config['secondary_color']};
        --accent-color: {theme_config['accent_color']};
        --background-color: {theme_config['background_color']};
        --text-color: {theme_config['text_color']};
        --navbar-style: {theme_config['navbar_style']};
    }}
    """
