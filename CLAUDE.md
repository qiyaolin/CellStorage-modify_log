# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Cell Storage Management System** - a dual-module Flask application that combines:
1. **Cell Storage System**: Laboratory cryovial management with batch tracking and location management
2. **Inventory Management System**: Lab supply inventory, ordering, and supplier management

The application features both desktop and mobile interfaces, centralized label printing, and comprehensive role-based permissions.

## Architecture

### Application Structure
```
app/
├── __init__.py                 # Flask app factory with blueprint registration
├── main_routes.py             # Main dashboard routing
├── mobile_routes.py           # Mobile-optimized routes and API endpoints
├── cell_storage/              # Cryovial storage module
├── inventory/                 # Lab inventory module  
├── shared/                    # Common utilities and permissions
├── api/                       # REST API endpoints
├── services/                  # Business logic services
├── templates/                 # Jinja2 templates (desktop + mobile)
└── static/                    # CSS, JS, images
```

### Database Architecture
- **PostgreSQL** in production (Google Cloud SQL), **SQLite** for local development
- **Cell Storage Models**: User, CellLine, Tower/Drawer/Box hierarchy, VialBatch, CryoVial
- **Inventory Models**: InventoryType, InventoryItem, Location, Supplier, Order, OrderItem
- **Printing System**: PrintJob, PrintServer, PrintJobHistory
- **Permission System**: UserPermission with fine-grained access control

### Key Design Patterns
- **Blueprint-based modular architecture** with separate cell_storage and inventory modules
- **Mobile-first responsive design** with dedicated mobile routes (/mobile/*)
- **Centralized printing service** with external print server communication
- **Role-based permissions** with granular resource-level access control
- **Audit logging** for all critical operations

## Development Commands

### Environment Setup
```bash
# Activate virtual environment (Windows)
activate_env.bat

# Install dependencies
pip install -r requirements.txt

# Set environment variables
set FLASK_APP=run.py
set FLASK_ENV=development
```

### Running the Application
```bash
# Development server
python run.py

# Production server (Gunicorn)
gunicorn -b :5000 'app:create_app()'

# With specific config
python run.py --config config.py
```

### Database Operations
```bash
# Database initialization (auto-creates tables)
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# Create admin user
python create_admin.py

# Database migrations
python migrate_database.py

# Fix batch migrations
python fix_batch_migration.py
```

### Testing and Validation
```bash
# Check website functionality
python check_website.py

# Validate CSV import functionality
python csv_import_validator.py

# Debug CSV import issues
python debug_csv_import.py

# Test browser functionality
python real_browser_test.py
```

## Mobile System

### Mobile Architecture
- **Dedicated mobile blueprint** (`/mobile/*`) with touch-optimized UI
- **Automatic mobile detection** via user agent and viewport detection
- **Mobile middleware** for device-specific handling
- **Responsive templates** in `templates/mobile/`
- **CSRF exemptions** for mobile API endpoints

### Mobile Features
- Mobile dashboard with quick actions
- Touch-friendly vial search and inventory management
- Auto-positioned vial creation with grid visualization
- Mobile-optimized printing interface
- Pickup list management with visual confirmation

### Mobile API Endpoints
- `GET /mobile/api/box/<int:box_id>/details` - Load box vial grid on demand
- `POST /mobile/api/vial/<int:vial_id>/status` - Update vial status
- `POST /mobile/api/clear-pickup-list` - Clear pickup selection

## Printing System

### Centralized Printing Architecture
The system uses a **queue-based printing architecture** with external print servers:

1. **Backend Queue**: Flask app queues print jobs in PostgreSQL
2. **Print Servers**: External Python agents monitor queue and handle actual printing
3. **DYMO Integration**: Print servers communicate with DYMO printers via DYMO Connect framework

### Print Server Setup
```bash
# Navigate to print server directory
cd dymo-print-server-nodejs/src

# Start print agent
python production_print_agent.py

# Windows batch script
start_print_agent.bat
```

### Printing API Endpoints
- `GET /api/print/status` - Check print service status
- `POST /api/print/queue-job` - Queue single print job
- `POST /api/print/queue-batch-labels` - Queue batch vial labels
- `POST /api/print/heartbeat` - Print server heartbeat
- `GET /api/print/fetch-pending-job` - Print server fetches next job

### Configuration
```python
# Environment variables
CENTRALIZED_PRINTING_ENABLED=true
PRINT_SERVER_URL=http://localhost:5001
PRINT_API_TOKEN=your-secure-token
```

## Key Models and Relationships

### Cell Storage Hierarchy
```
Tower (freezer unit)
├── Drawer (shelf level)
    ├── Box (storage container with grid)
        ├── CryoVial (individual vial at row/col position)
            └── VialBatch (groups related vials)
                └── CellLine (cell line information)
```

### Inventory Structure
```
Location (hierarchical storage)
├── InventoryItem (tracked supplies)
    ├── InventoryType (categories: chemicals, antibodies, etc.)
    ├── Supplier (vendor information)
    └── Order/OrderItem (purchasing workflow)
```

### Permission System
```python
# Permission format: 'module.action'
permissions = [
    'inventory.view', 'inventory.create', 'inventory.edit',
    'location.manage', 'supplier.edit', 'order.approve',
    'admin.user_management', 'admin.system_config'
]

# Usage in templates
{% if has_permission('inventory.edit') %}
    <button>Edit Item</button>
{% endif %}

# Usage in routes
@require_permission('inventory.create')
def create_item():
    pass
```

## Security Implementation

### Authentication
- **Flask-Login** for session management
- **CSRF protection** via Flask-WTF (with mobile exemptions)
- **Role-based access** (admin, user roles)
- **Fine-grained permissions** via UserPermission model

### Data Protection
- **Password hashing** with Werkzeug
- **SQL injection protection** via SQLAlchemy ORM
- **API token authentication** for print server communication
- **Audit logging** for all critical operations

## Configuration

### Environment-Specific Settings
```python
# config.py handles multiple environments
if os.environ.get("INSTANCE_CONNECTION_NAME"):
    # Google Cloud SQL (production)
    SQLALCHEMY_DATABASE_URI = "postgresql+pg8000://"
    SQLALCHEMY_ENGINE_OPTIONS = {"creator": getconn}
else:
    # SQLite (local development)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
```

### Google App Engine Deployment
```yaml
# app.yaml
runtime: python313
instance_class: F1
entrypoint: gunicorn -b :$PORT 'app:create_app()'

env_variables:
  INSTANCE_CONNECTION_NAME: "project:region:instance"
  DB_USER: "postgres"
  DB_PASS: "password"
  SECRET_KEY: "secure-key"
  CENTRALIZED_PRINTING_ENABLED: "true"
```

## Common Operations

### Create New Vial Batch
```python
# Backend: Find available positions
positions = find_available_positions_mobile(quantity)

# Create batch and vials
batch = VialBatch(name=batch_name, created_by_user_id=user_id)
for position in positions:
    vial = CryoVial(
        batch_id=batch.id,
        box_id=position['box_id'],
        row_in_box=position['row'],
        col_in_box=position['col']
    )
```

### Mobile vs Desktop Routing
```python
# Mobile detection in middleware
if is_mobile_device(request.user_agent.string):
    g.view_mode = 'mobile'

# Template selection
template = 'mobile/inventory.html' if g.view_mode == 'mobile' else 'inventory.html'
```

### Queue Print Jobs
```python
# Queue single vial label
label_data = {
    'item_name': batch_name,
    'barcode': f"B{batch_id}",
    'location': f"{tower}/{drawer}/{box}",
    'position': f"R{row}C{col}"
}
job = printing_service.queue_print_job(label_data)
```

## Important Notes

- **Database migrations** are handled through direct SQL in `app/__init__.py`
- **Batch IDs** are auto-generated and managed through `AppConfig` table
- **Mobile CSRF exemptions** are configured for specific API endpoints only
- **Print server communication** requires API token authentication
- **Location hierarchy** supports unlimited nesting for flexible lab organization
- **Audit logging** captures user actions for compliance and debugging