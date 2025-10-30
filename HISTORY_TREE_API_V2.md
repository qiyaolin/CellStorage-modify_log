# History Tree API v2 Documentation

## Phase 1 Enhancement - Optimized Lineage API

This document describes the new v2 API endpoints added for optimized History Tree functionality. **All existing v1 endpoints remain unchanged and fully functional.**

### Design Principles

- **Zero Breaking Changes**: All existing endpoints continue to work exactly as before
- **App Engine Optimized**: Compatible with Google App Engine deployment constraints
- **Performance First**: Caching, lazy loading, and optimized data structures
- **Gradual Enhancement**: New endpoints can be adopted progressively

---

## New API Endpoints

### 1. Optimized Lineage Data

**Endpoint**: `GET /api/v2/batch/<batch_id>/lineage/optimized`

**Purpose**: Get frontend-optimized lineage data with lazy loading support

**Parameters**:
- `viewport_depth` (int, default: 3): Maximum depth to load initially
- `include_details` (bool, default: true): Include detailed node information
- `use_cache` (bool, default: true): Use caching for performance

**Response**:
```json
{
  "success": true,
  "lineage": {
    "current": {
      "id": 123,
      "name": "Batch_001",
      "type": "current",
      "depth": 0,
      "hasChildren": true,
      "hasParents": false,
      "cell_line": "HEK293",
      "passage_number": 15,
      "date_frozen": "2024-01-15T10:30:00",
      "vial_count": 10
    },
    "ancestors": [...],
    "descendants": [...],
    "metadata": {
      "viewport_depth": 3,
      "has_more_ancestors": false,
      "has_more_descendants": true,
      "optimized_for_frontend": true
    }
  },
  "cached": true,
  "api_version": "v2"
}
```

**Benefits**:
- Reduced data transfer (only loads visible viewport)
- Frontend-friendly data structure
- Lazy loading metadata for progressive enhancement
- Caching for repeated requests

---

### 2. Summary Statistics

**Endpoint**: `GET /api/v2/batch/<batch_id>/lineage/summary`

**Purpose**: Get lightweight summary statistics for quick loading

**Parameters**:
- `use_cache` (bool, default: true): Use caching for performance

**Response**:
```json
{
  "success": true,
  "summary": {
    "batch_id": 123,
    "batch_name": "Batch_001",
    "has_lineage": true,
    "direct_parents": 2,
    "direct_children": 5,
    "estimated_ancestors": 4,
    "estimated_descendants": 12,
    "estimated_total_related": 16,
    "last_updated": "2024-01-15T14:30:00",
    "is_summary": true
  },
  "cached": true,
  "api_version": "v2"
}
```

**Benefits**:
- Ultra-fast loading for dashboard widgets
- Estimated counts (no deep traversal required)
- Perfect for quick overview displays

---

### 3. Depth-Based Node Loading

**Endpoint**: `GET /api/v2/batch/<batch_id>/lineage/depth/<depth_level>`

**Purpose**: Get nodes at specific depth for lazy loading large trees

**Parameters**:
- `type` (string): "ancestors" or "descendants"
- `limit` (int, default: 50): Maximum nodes to return
- `offset` (int, default: 0): Pagination offset
- `use_cache` (bool, default: true): Use caching

**Response**:
```json
{
  "success": true,
  "data": {
    "nodes": [
      {
        "id": 456,
        "name": "Batch_002",
        "depth": 2,
        "has_children": true,
        "has_parents": true,
        "cell_line": "HEK293T",
        "passage_number": 20
      }
    ],
    "pagination": {
      "depth_level": 2,
      "limit": 50,
      "offset": 0,
      "total_count": 8,
      "has_more": false,
      "next_offset": null
    },
    "metadata": {
      "node_type": "descendants",
      "root_batch_id": 123
    }
  },
  "cached": true,
  "api_version": "v2"
}
```

**Benefits**:
- Supports very large lineage trees
- Pagination prevents memory issues
- Progressive loading for better UX

---

### 4. Cache Management Endpoints

#### Cache Statistics
**Endpoint**: `GET /api/v2/lineage/cache/stats` (Admin only)

**Response**:
```json
{
  "success": true,
  "cache_stats": {
    "total_entries": 45,
    "valid_entries": 42,
    "expired_entries": 3,
    "max_cache_size": 100,
    "cache_usage_percent": 45.0,
    "default_ttl": 300,
    "last_cleanup": "2024-01-15T14:30:00"
  },
  "api_version": "v2"
}
```

#### Warm Cache
**Endpoint**: `POST /api/v2/lineage/cache/warm/<batch_id>`

Pre-loads cache with common data for a batch.

#### Invalidate Cache
**Endpoint**: `POST /api/v2/lineage/cache/invalidate/<batch_id>`

Clears all cached data for a specific batch.

---

## Caching Strategy

### App Engine Compatible Caching

The caching system is designed specifically for Google App Engine:

- **In-Memory Caching**: Uses instance-level memory (no external dependencies)
- **Automatic Cleanup**: Manages memory usage within F1 instance limits
- **TTL Management**: 5-minute default TTL, 10 minutes for statistics
- **Size Limits**: Maximum 100 cache entries to prevent memory issues

### Cache Keys

Cache keys are structured for easy invalidation:
- `lineage_optimized:{batch_id}:depth:{depth}:details:{true/false}`
- `lineage_summary:{batch_id}`
- `lineage_depth:{batch_id}:depth:{level}:type:{type}:offset:{offset}:limit:{limit}`

### Cache Invalidation

Cache is automatically invalidated when:
- Data is modified (manual invalidation required)
- TTL expires
- Memory pressure (LRU eviction)

---

## Migration Strategy

### Phase 1: Coexistence (Current)
- New v2 endpoints available alongside existing v1 endpoints
- Frontend can gradually adopt new endpoints
- Zero risk to existing functionality

### Phase 2: Frontend Enhancement (Next)
- Update frontend to use optimized endpoints
- Implement progressive loading
- Add enhanced visualizations

### Phase 3: Performance Optimization (Future)
- Monitor usage patterns
- Fine-tune caching parameters
- Optimize based on real-world data

---

## Error Handling

All v2 endpoints follow consistent error patterns:

```json
{
  "success": false,
  "message": "Descriptive error message",
  "api_version": "v2"
}
```

Common HTTP status codes:
- `400`: Bad Request (invalid parameters)
- `403`: Forbidden (admin-only endpoints)
- `404`: Not Found (batch doesn't exist)
- `500`: Internal Server Error

---

## Performance Expectations

### Optimized Lineage Endpoint
- **Cached Response**: < 50ms
- **Uncached Response**: < 500ms (for trees up to depth 3)
- **Memory Usage**: ~1KB per cached batch

### Summary Statistics
- **Cached Response**: < 20ms
- **Uncached Response**: < 200ms
- **Memory Usage**: ~200 bytes per cached batch

### Depth Loading
- **Cached Response**: < 30ms
- **Uncached Response**: < 300ms (for 50 nodes)
- **Memory Usage**: ~2KB per cached page

---

## Usage Examples

### Basic Frontend Integration

```javascript
// Load optimized lineage data
async function loadOptimizedLineage(batchId) {
    const response = await fetch(`/api/v2/batch/${batchId}/lineage/optimized?viewport_depth=3`);
    const data = await response.json();
    
    if (data.success) {
        renderLineageTree(data.lineage);
        updateLoadingStatus(data.cached ? 'cached' : 'fresh');
    }
}

// Load summary for dashboard
async function loadSummaryStats(batchId) {
    const response = await fetch(`/api/v2/batch/${batchId}/lineage/summary`);
    const data = await response.json();
    
    if (data.success) {
        updateDashboardStats(data.summary);
    }
}

// Progressive loading for large trees
async function loadMoreDescendants(batchId, depth) {
    const response = await fetch(`/api/v2/batch/${batchId}/lineage/depth/${depth}?type=descendants`);
    const data = await response.json();
    
    if (data.success) {
        appendNodesToTree(data.data.nodes);
        updatePaginationControls(data.data.pagination);
    }
}
```

### Cache Warming for Popular Batches

```javascript
// Pre-warm cache for frequently accessed batches
async function warmPopularBatches(batchIds) {
    for (const batchId of batchIds) {
        await fetch(`/api/v2/lineage/cache/warm/${batchId}`, { method: 'POST' });
    }
}
```

---

## Monitoring and Debugging

### Cache Performance Monitoring

```javascript
// Check cache statistics (admin only)
async function checkCacheHealth() {
    const response = await fetch('/api/v2/lineage/cache/stats');
    const data = await response.json();
    
    if (data.success && data.cache_stats.cache_usage_percent > 90) {
        console.warn('Cache usage high:', data.cache_stats);
    }
}
```

### Performance Logging

All v2 endpoints include performance metadata:
- Cache hit/miss status
- Response generation time
- Data freshness indicators

---

## Security Considerations

- All endpoints require authentication (`@login_required`)
- Cache management endpoints require admin privileges
- No sensitive data is cached (only public batch information)
- Cache keys don't expose sensitive information

---

## Deployment Notes

### App Engine Compatibility
- No external dependencies (Redis, Memcached, etc.)
- Memory usage stays within F1 instance limits
- Compatible with auto-scaling and cold starts
- No special configuration required

### Rollback Plan
If issues arise, simply remove the new routes - existing functionality remains 100% intact.

---

## Next Steps

1. **Frontend Integration**: Begin using v2 endpoints in History Tree frontend
2. **Performance Monitoring**: Track API response times and cache hit rates
3. **User Testing**: Gather feedback on improved loading performance
4. **Optimization**: Fine-tune cache parameters based on usage patterns

---

**Note**: This is Phase 1 of the History Tree redesign. All changes are additive and non-breaking. The existing History Tree functionality continues to work exactly as before.