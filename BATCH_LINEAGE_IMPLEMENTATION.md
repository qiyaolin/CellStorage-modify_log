# Batch Lineage Implementation Guide

## Overview

This document describes the complete implementation of the Batch History Tree feature with proper database relationships, replacing the previous unreliable string-based matching system.

## Problem Statement

### Previous Implementation Issues

❌ **No Proper Database Relationships**: VialBatch model had no foreign key for parent-child relationships
❌ **String-Based Matching**: Relied on matching `parental_cell_line` text field against batch names
❌ **Data Integrity Issues**: No referential integrity, duplicate matches possible
❌ **Performance Problems**: N+1 query issues, recursive string matching
❌ **No Management UI**: Users couldn't manually create or edit relationships

### Root Cause

The `get_parent_batches()` and `get_child_batches()` methods used fragile string matching:

```python
# OLD - Unreliable string matching
def get_parent_batches(self):
    parent_batches = VialBatch.query.filter_by(name=self.parental_cell_line).all()
    # Multiple queries, no referential integrity, unreliable
```

## New Solution

### Database Schema

**New Table: `batch_lineage`**

```sql
CREATE TABLE batch_lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_batch_id INTEGER NOT NULL,
    child_batch_id INTEGER NOT NULL,
    relationship_type VARCHAR(50) NOT NULL DEFAULT 'passage',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER,
    FOREIGN KEY (parent_batch_id) REFERENCES vial_batches(id) ON DELETE CASCADE,
    FOREIGN KEY (child_batch_id) REFERENCES vial_batches(id) ON DELETE CASCADE,
    CHECK (parent_batch_id != child_batch_id),
    UNIQUE (parent_batch_id, child_batch_id)
);
```

**Features:**
- ✅ Proper foreign key constraints
- ✅ Prevents self-references (CHECK constraint)
- ✅ Prevents duplicate relationships (UNIQUE constraint)
- ✅ Cascade deletion when batches are deleted
- ✅ Tracks relationship type (passage, split, fusion, derived)
- ✅ Audit trail (created_at, created_by_user_id)

### Model Changes

**New Model: `BatchLineage`**

```python
class BatchLineage(db.Model):
    __tablename__ = 'batch_lineage'
    id = db.Column(db.Integer, primary_key=True)
    parent_batch_id = db.Column(db.Integer, db.ForeignKey('vial_batches.id', ondelete='CASCADE'))
    child_batch_id = db.Column(db.Integer, db.ForeignKey('vial_batches.id', ondelete='CASCADE'))
    relationship_type = db.Column(db.String(50), default='passage')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
```

**Updated VialBatch Model:**

```python
class VialBatch(db.Model):
    # ... existing fields ...

    # New lineage relationships
    parent_lineages = db.relationship('BatchLineage',
        foreign_keys='BatchLineage.child_batch_id',
        backref='child_batch', lazy='dynamic')

    child_lineages = db.relationship('BatchLineage',
        foreign_keys='BatchLineage.parent_batch_id',
        backref='parent_batch', lazy='dynamic')

    def get_parent_batches(self):
        """Returns list of parent VialBatch objects"""
        return [lineage.parent_batch for lineage in self.parent_lineages.all()]

    def get_child_batches(self):
        """Returns list of child VialBatch objects"""
        return [lineage.child_batch for lineage in self.child_lineages.all()]

    def add_parent(self, parent_batch, relationship_type='passage', notes=None):
        """Create parent relationship with validation"""
        # ... implementation ...

    def add_child(self, child_batch, relationship_type='passage', notes=None):
        """Create child relationship with validation"""
        # ... implementation ...
```

## Migration Process

This system uses a **dual-track migration approach** following existing patterns:

### Local Development (SQLite)

```bash
# Activate virtual environment
activate_env.bat

# Run migration script (follows migrate_database.py pattern)
python migrate_batch_lineage.py

# Rollback if needed
python migrate_batch_lineage.py --rollback
```

### Production Environment (PostgreSQL/Google Cloud)

Migration runs **automatically on application startup** (integrated in `app/__init__.py`):

```bash
# Simply deploy - migration runs automatically
gcloud app deploy

# Or run locally (if using PostgreSQL)
python run.py
```

**Key Points**:
- PostgreSQL migration uses `CREATE TABLE IF NOT EXISTS` - safe and idempotent
- Migrations don't block application startup (error handling in place)
- Follows existing system patterns (see `app/__init__.py` lines 62-91)

### Migration Steps

1. **Create Table**: Creates `batch_lineage` table with proper schema
2. **Create Indexes**: Adds indexes on `parent_batch_id` and `child_batch_id` for performance
3. **Migrate Data**: Best-effort migration of existing string-based relationships
4. **Verify**: Checks table structure and samples relationships

### Expected Output

```
================================================================================
Batch Lineage Table Migration
================================================================================
Creating batch_lineage table...
✅ batch_lineage table created successfully
Creating indexes...
✅ Indexes created successfully

Migrating existing string-based relationships...
This may take a while for large datasets...
Processing 150 batches...
  Progress: 100/150
  Progress: 150/150

✅ Migration complete:
   - Migrated: 45 relationships
   - Skipped: 95 (no parent or already exists)
   - Failed: 0

Verifying migration...
✅ Found 45 batch lineage relationships
✅ No circular references found

Sample relationships:
  Batch_001 (1) -> Batch_002 (2) [passage]
  Batch_002 (2) -> Batch_003 (3) [passage]
  ...

================================================================================
✅ Migration completed successfully!
================================================================================
```

## API Endpoints

### Get Batch Relationships

```http
GET /cell-storage/api/batch/<batch_id>/lineage/relationships
```

**Response:**
```json
{
  "success": true,
  "batch_id": 123,
  "batch_name": "Batch_001",
  "parents": [
    {
      "id": 1,
      "parent_batch_id": 100,
      "parent_batch_name": "Batch_000",
      "relationship_type": "passage",
      "notes": "P15 passage",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "children": [
    {
      "id": 2,
      "child_batch_id": 150,
      "child_batch_name": "Batch_002",
      "relationship_type": "split",
      "notes": "Split for experiment",
      "created_at": "2024-01-20T14:00:00"
    }
  ]
}
```

### Add Parent Relationship

```http
POST /cell-storage/api/batch/<batch_id>/lineage/add-parent
Content-Type: application/json

{
  "parent_batch_id": 100,
  "relationship_type": "passage",  // optional, default: "passage"
  "notes": "P15 passage"  // optional
}
```

### Add Child Relationship

```http
POST /cell-storage/api/batch/<batch_id>/lineage/add-child
Content-Type: application/json

{
  "child_batch_id": 150,
  "relationship_type": "split",
  "notes": "Split for experiment"
}
```

### Delete Relationship

```http
DELETE /cell-storage/api/batch/lineage/<relationship_id>
```

### Update Relationship

```http
PATCH /cell-storage/api/batch/lineage/<relationship_id>
Content-Type: application/json

{
  "relationship_type": "fusion",
  "notes": "Updated notes"
}
```

### Search Batches for Lineage

```http
GET /cell-storage/api/batch/search-for-lineage?q=Batch_&exclude_batch_id=123&limit=20
```

## Relationship Types

| Type | Description | Use Case |
|------|-------------|----------|
| **passage** | Sequential cell passage | Normal cell line maintenance |
| **split** | Splitting cells into multiple batches | Expanding culture for experiments |
| **fusion** | Cell fusion from multiple parents | Creating hybrid cell lines |
| **derived** | Derived cell line (e.g., clonal selection) | Selecting specific clones |

## User Interface

### Batch Management Page

**Location**: `/cell-storage/admin/manage_batch/<batch_id>`

**Features:**
- View current parent/child relationships
- Add new parent/child relationships with search autocomplete
- Edit relationship type and notes
- Delete relationships
- Visual indication of relationship types

### History Tree Visualization

**Location**: `/cell-storage/history-tree`

**Improvements:**
- Now displays actual database relationships
- Shows relationship types on connections
- Proper ancestor/descendant trees
- No more "phantom" relationships from string matching

## Testing Procedures

### 1. Test Migration

```bash
# Backup database first
cp instance/app.db instance/app.db.backup

# Run migration
python migrations/add_batch_lineage_table.py

# Verify in database
sqlite3 instance/app.db
> SELECT COUNT(*) FROM batch_lineage;
> SELECT * FROM batch_lineage LIMIT 5;
```

### 2. Test API Endpoints

```bash
# Get relationships for batch 1
curl -X GET http://localhost:5000/cell-storage/api/batch/1/lineage/relationships \
  -H "Cookie: session=..."

# Add parent relationship
curl -X POST http://localhost:5000/cell-storage/api/batch/2/lineage/add-parent \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"parent_batch_id": 1, "relationship_type": "passage"}'
```

### 3. Test History Tree Page

1. Navigate to `/cell-storage/history-tree`
2. Search for a batch with relationships
3. Verify tree visualization displays correctly
4. Switch between Full/Ancestors/Descendants views
5. Click nodes to navigate between batches

## Troubleshooting

### Migration Issues

**Problem**: Migration fails with "table already exists"
```bash
# Solution: Drop table and retry
python migrations/add_batch_lineage_table.py --rollback
python migrations/add_batch_lineage_table.py
```

**Problem**: Few relationships migrated
- **Cause**: Old data used inconsistent naming
- **Solution**: Manually add relationships through UI or API

### API Issues

**Problem**: "404 Not Found" on lineage endpoints
```python
# Solution: Verify lineage_routes.py is imported
# Check app/cell_storage/main/__init__.py:
from . import lineage_routes
```

**Problem**: "500 Internal Server Error"
- Check logs for specific error
- Verify database migration completed
- Ensure BatchLineage model is imported

### UI Issues

**Problem**: History Tree shows empty
- Verify batch has relationships in database
- Check browser console for JavaScript errors
- Verify D3.js loaded correctly

## Performance Considerations

### Query Optimization

**Before (String Matching):**
```python
# Multiple queries, joins, string comparisons
parent_batches = VialBatch.query.filter_by(name=self.parental_cell_line).all()
cell_line_matches = VialBatch.query.join(CryoVial).join(CellLine).filter(...)
# O(n²) for deep trees
```

**After (Foreign Keys):**
```python
# Single query with indexes
parent_lineages = self.parent_lineages.all()  # Indexed FK lookup
parents = [lineage.parent_batch for lineage in parent_lineages]
# O(n) with constant factor improvement
```

### Caching

The existing v2 lineage API endpoints (`/api/v2/batch/<id>/lineage/optimized`) automatically benefit from proper relationships:
- Faster queries mean faster cache fills
- No more incorrect relationships in cache
- Cache invalidation on relationship changes

## Future Enhancements

### Phase 2 - UI Improvements
- [ ] Drag-and-drop relationship creation in tree view
- [ ] Batch relationship suggestions based on cell line and timing
- [ ] Relationship validation warnings (e.g., circular dependencies)
- [ ] Bulk import relationships from CSV

### Phase 3 - Advanced Features
- [ ] Relationship strength/confidence scoring
- [ ] Auto-detect relationships from experimental logs
- [ ] Export lineage tree as PDF/PNG
- [ ] Lineage-based batch search and filtering

## Support and Maintenance

### Database Schema Updates

If schema changes are needed:
1. Create new migration script in `migrations/`
2. Test on development database
3. Backup production database
4. Run migration on production
5. Verify data integrity

### Monitoring

Key metrics to monitor:
- Relationship count over time
- Orphaned batches (no parents or children)
- Circular dependency detection
- Query performance on lineage endpoints

## Conclusion

The new BatchLineage implementation provides:

✅ **Data Integrity**: Proper foreign key relationships
✅ **Performance**: Indexed queries, no string matching
✅ **Flexibility**: Multiple relationship types, audit trail
✅ **User Control**: Full CRUD API and management UI
✅ **Reliability**: Database constraints prevent invalid states

The History Tree visualization now displays accurate, database-backed relationships with proper performance and user management capabilities.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-25
**Status**: Implementation Complete, Testing Required
